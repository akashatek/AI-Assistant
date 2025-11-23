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

# --- UPDATED IMPORTS ---
from task_tools import (
    task_create_wrapper, task_update_wrapper, task_delete_wrapper, 
    task_list_wrapper, task_search_wrapper, task_read_wrapper, 
    parse_date_wrapper,
    CreateTaskInput, UpdateTaskInput, DeleteTaskInput, 
    ListTasksInput, SearchTasksInput, ReadTaskInput, ParseDateInput
)

# 1. Define LLM, Tools, and Agent outside the graph nodes
# os.environ["OLLAMA_BASE_URL"] = "http://batman.local:11434" # Assuming this is set externally or via env var
llm = OllamaLLM(model="llama3.2:1b", temperature=0.0) # Ensure your LLM model is correct

# 2. Define Tools using the wrapper functions
tools = [
    StructuredTool.from_function(
        func=task_create_wrapper, # FIX: Use the wrapper function
        name="create_task",
        description="Creates a new Google Task with a title, notes, and an optional due date in YYYY-MM-DD format. The LLM must first call the parse_date tool to get the correct format if the user provides a natural language date.",
        args_schema=CreateTaskInput
    ),
    StructuredTool.from_function(
        func=task_update_wrapper, # FIX: Use the wrapper function
        name="update_task",
        description="Updates a Google Task. Requires the task_id. Can update the title, notes, status ('completed' or 'needsAction'), or due date.",
        args_schema=UpdateTaskInput
    ),
    StructuredTool.from_function(
        func=task_delete_wrapper, # FIX: Use the wrapper function
        name="delete_task",
        description="Deletes a Google Task. Requires the task_id.",
        args_schema=DeleteTaskInput
    ),
    StructuredTool.from_function(
        func=task_list_wrapper, # FIX: Use the wrapper function
        name="list_tasks",
        description="Lists all Google Tasks, optionally filtered by due date (YYYY-MM-DD).",
        args_schema=ListTasksInput
    ),
    StructuredTool.from_function(
        func=task_search_wrapper, # FIX: Use the wrapper function
        name="search_tasks",
        description="Searches for a specific task by a keyword in its title. Can be filtered by an optional due date (YYYY-MM-DD).",
        args_schema=SearchTasksInput
    ),
    StructuredTool.from_function(
        func=task_read_wrapper, # FIX: Use the wrapper function
        name="read_task",
        description="Reads a single Google Task by its ID. Requires the task_id.",
        args_schema=ReadTaskInput
    ),
    StructuredTool.from_function(
        func=parse_date_wrapper, # FIX: Use the wrapper function
        name="parse_date",
        description="Converts a natural language date (e.g., 'today', 'tomorrow', 'next week') into a YYYY-MM-DD string. Always use this tool before calling `create_task` or `update_task` if the user provides a natural language date.",
        args_schema=ParseDateInput
    )
]
tool_names = [t.name for t in tools]

# 3. Define the Agent State
class AgentState(TypedDict):
    input: str
    chat_history: List[BaseMessage]
    agent_outcome: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[List[tuple[AgentAction, str]], operator.add]

# 4. Define the Agent's Nodes and Edges
def run_agent(state: AgentState):
    """A node that runs the agent and returns an AgentAction or AgentFinish."""
    inputs = state["input"]
    intermediate_steps = state.get("intermediate_steps", [])
    
    # --- PROMPT INSTRUCTIONS enforcing rules ---
    tool_list_text = "\n".join([f"- {t.name}: {t.description}" for t in tools])
    
    prompt_parts = [
        f"""You are a helpful assistant that can interact with my Google Tasks.
You have access to the following Google Task management tools.

# Tool Usage and Rules:
1. **Date Formatting:** Always use the **`parse_date`** tool first if the user provides a natural language date (e.g., 'tomorrow', 'next week') to convert it to **YYYY-MM-DD** format before using `create_task` or `update_task`.
2. **Task Status Mapping:** When updating a task's status, map natural language status to the following official values for the `status` argument in `update_task`:
    * 'not started' or 'on going' should map to: **'needsAction'**
    * 'completed' should map to: **'completed'**
3. **Tool Fallback:** If you cannot find a suitable tool for the request (e.g., asking for a joke), or the request is ambiguous, you **must** list the available tools and a brief description of what they do in your final answer.

The available tools are:
{tool_list_text}

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
        # Format the thought/observation history
        formatted_steps = []
        for action, observation in intermediate_steps:
            thought = action.log.split("Action:")[0].strip()
            formatted_steps.append(f"{thought}\nObservation: {observation}")
        
        prompt_parts.append("\n".join(formatted_steps))
    
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
                raise ValueError("Could not find required 'Final Answer:' or 'Action:/Action Input:' structure in LLM output.")
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
                # This correctly unpacks the dict into keyword arguments (e.g., title=...)
                result = tool.run(**tool_input)
            else:
                # This handles single string inputs (like the date_string in parse_date)
                result = tool.run(tool_input)
            return {"intermediate_steps": [(action, str(result))]}
    
    raise ValueError(f"Tool {tool_name} not found.")

def should_continue(state: AgentState):
    """Conditional edge to decide whether to continue or end the conversation."""
    if isinstance(state["agent_outcome"], AgentFinish):
        return "end"
    else:
        return "continue"

# 5. Build the Langgraph
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

# 6. Run the Agent
if __name__ == "__main__":
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            for s in app.stream({"input": user_input, "intermediate_steps": []}):
                if "__end__" in s:
                    print("\nAssistant:", s["__end__"]["agent_outcome"]["output"])
        except Exception as e:
            print(f"An error occurred: {e}")