# agent.py
import os
import operator
import json
import re
from typing import TypedDict, Annotated, List, Union
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage
from langchain_ollama import OllamaLLM
from langchain_core.tools import StructuredTool
from langgraph.graph import StateGraph, END
from tools import create_task, update_task, delete_task, list_tasks, search_tasks, read_task, parse_date, CreateTaskInput, UpdateTaskInput, DeleteTaskInput, ListTasksInput, SearchTasksInput, ReadTaskInput, ParseDateInput

# 1. Define LLM, Tools, and Agent outside the graph nodes
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
llm = OllamaLLM(model="llama3.2:1b", temperature=0.0)

tools = [
    StructuredTool.from_function(
        func=create_task,
        name="create_task",
        description="Creates a new Google Task with a title, notes, and an optional due date in YYYY-MM-DD format. The LLM must first call the parse_date tool to get the correct format if the user provides a natural language date.",
        args_schema=CreateTaskInput
    ),
    StructuredTool.from_function(
        func=update_task,
        name="update_task",
        description="Updates a Google Task. Requires the task_id. Can update the title, notes, status ('completed' or 'needsAction'), or due date.",
        args_schema=UpdateTaskInput
    ),
    StructuredTool.from_function(
        func=delete_task,
        name="delete_task",
        description="Deletes a Google Task. Requires the task_id.",
        args_schema=DeleteTaskInput
    ),
    StructuredTool.from_function(
        func=list_tasks,
        name="list_tasks",
        description="Lists all Google Tasks, optionally filtered by due date.",
        args_schema=ListTasksInput
    ),
    StructuredTool.from_function(
        func=search_tasks,
        name="search_tasks",
        description="Searches for a specific task by a keyword in its title. Can be filtered by an optional due date.",
        args_schema=SearchTasksInput
    ),
    StructuredTool.from_function(
        func=read_task,
        name="read_task",
        description="Reads a single Google Task by its ID. Requires the task_id.",
        args_schema=ReadTaskInput
    ),
    StructuredTool.from_function(
        func=parse_date,
        name="parse_date",
        description="Converts a natural language date (e.g., 'today', 'tomorrow', 'next week', 'in 2 weeks') into a YYYY-MM-DD string. Always use this tool before calling `create_task` or `update_task` if the user provides a natural language date.",
        args_schema=ParseDateInput
    )
]
# A list of all valid tool names
tool_names = [t.name for t in tools]

# 2. Define the Agent State
class AgentState(TypedDict):
    input: str
    chat_history: List[BaseMessage]
    agent_outcome: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[List[tuple[AgentAction, str]], operator.add]

# 3. Define the Agent's Nodes and Edges
def run_agent(state: AgentState):
    """A node that runs the agent and returns an AgentAction or AgentFinish."""
    inputs = state["input"]
    intermediate_steps = state.get("intermediate_steps", [])
    
    prompt_parts = [
        f"""You are a helpful assistant that can interact with my Google Tasks.
You can use the following tools to manage my tasks.

{tools}

To use a tool, you **must** follow this **exact** format:
Thought: I need to use a tool to respond to the request.
Action: [the tool name from the list provided]
Action Input: [the input to the action in JSON format]

When you have the final answer, use this **exact** format:
Thought: I have the final answer.
Final Answer: [the final answer to the original input question]

Begin!

Question: {inputs}
"""
    ]
    
    if intermediate_steps:
        prompt_parts.append("\n".join([f"Thought: {step[0].log}\nObservation: {step[1]}" for step in intermediate_steps]))
    
    prompt = "\n".join(prompt_parts)
    response_text = llm.invoke(prompt)

    if "Final Answer:" in response_text:
        return {"agent_outcome": AgentFinish(
            return_values={"output": response_text.split("Final Answer:")[-1].strip()},
            log=response_text
        )}
    else:
        try:
            action_match = re.search(r"Action:(.*?)\nAction Input:(.*)", response_text, re.DOTALL)
            
            if action_match:
                action_content = action_match.group(1).strip()
                action_input_str = action_match.group(2).strip()

                # Find the first valid tool name in the action content
                action_name = next((name for name in tool_names if name in action_content), None)

                if action_name is None:
                    raise ValueError(f"Could not find a valid tool name in the LLM output. Found: {action_content}")

                try:
                    action_input = json.loads(action_input_str.replace("'", "\""))
                except json.JSONDecodeError:
                    action_input = action_input_str

                return {"agent_outcome": AgentAction(
                    tool=action_name,
                    tool_input=action_input,
                    log=response_text
                )}
            else:
                raise ValueError("Could not find both 'Action:' and 'Action Input:' in LLM output.")
        except Exception as e:
            raise ValueError(f"Failed to parse LLM output: {e}\nOutput: {response_text}")

def execute_tools(state: AgentState):
    """A node that executes the tool specified by the agent."""
    action = state["agent_outcome"]
    tool_name = action.tool
    tool_input = action.tool_input
    
    for tool in tools:
        if tool.name == tool_name:
            if isinstance(tool_input, dict):
                result = tool.run(**tool_input)
            else:
                result = tool.run(tool_input)
            return {"intermediate_steps": [(action, str(result))]}
    
    raise ValueError(f"Tool {tool_name} not found.")

def should_continue(state: AgentState):
    """Conditional edge to decide whether to continue or end the conversation."""
    if isinstance(state["agent_outcome"], AgentFinish):
        return "end"
    else:
        return "continue"

# 4. Build the Langgraph
graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", run_agent)
graph_builder.add_node("tools", execute_tools)

graph_builder.set_entry_point("agent")

graph_builder.add_conditional_edges("agent", should_continue, {
    "continue": "tools",
    "end": END
})
graph_builder.add_edge("tools", "agent")

app = graph_builder.compile()

# 5. Run the Agent
if __name__ == "__main__":
    while True:
        user_input = input("User: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        
        for s in app.stream({"input": user_input, "intermediate_steps": []}):
            print(s)