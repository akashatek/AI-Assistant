import requests
from typing import TypedDict, Annotated, List, Optional
import operator
from pydantic import BaseModel, Field
from langchain_core.tools import tool
# CHANGE 1: Import SystemMessage
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
# from langgraph.prebuilt.tool_executor import ToolExecutor 
from langgraph.prebuilt import ToolNode


# --- Configuration ---
# NOTE: Replace with your actual PostgREST base URL
POSTGREST_BASE_URL = "http://localhost:3000" 
LLM_MODEL = "llama3.2:1b" # A good, cost-effective model for tool-calling

# --- 1. Pydantic Schemas for Tool Arguments ---

class TodoID(BaseModel):
    """Schema for functions that require a todo item's ID."""
    todo_id: int = Field(..., description="The unique integer ID of the todo item.")

class TodoSearch(BaseModel):
    """Schema for searching todos by task title."""
    query: str = Field(..., description="The text to search for in the todo task description.")

class TodoUpdate(BaseModel):
    """Schema for updating a todo item."""
    todo_id: int = Field(..., description="The unique integer ID of the todo item.")
    task: Optional[str] = Field(None, description="The new task description (optional).")
    done: Optional[bool] = Field(None, description="The new completion status (true/false) (optional).")
    due: Optional[str] = Field(None, description="The new due date (e.g., '2025-10-01T10:00:00Z') (optional).")

class TodoFilter(BaseModel):
    """Schema for filtering todos by due date."""
    due_date: str = Field(..., description="The due date string to filter against (e.g., '2025-10-01').")
    operator: str = Field('eq', description="The comparison operator for the due date ('eq', 'gt', 'lt', 'gte', 'lte'). Defaults to 'eq'.")

# --- 2. Tool Implementations (Functions) ---

@tool
def list_all_todos() -> str:
    """Retrieves a list of all tasks from the todo list."""
    try:
        response = requests.get(f"{POSTGREST_BASE_URL}/todos")
        response.raise_for_status()
        return f"Successfully retrieved all todos:\n{response.json()}"
    except requests.exceptions.RequestException as e:
        return f"ERROR: Could not connect to PostgREST API: {e}"

@tool
def search_todo_by_title(query: str) -> str:
    """Finds tasks containing the given text in their title."""
    try:
        # PostgREST uses 'ilike' for case-insensitive partial search
        url = f"{POSTGREST_BASE_URL}/todos?task=ilike.*{query}*"
        response = requests.get(url)
        response.raise_for_status()
        return f"Search results for '{query}':\n{response.json()}"
    except requests.exceptions.RequestException as e:
        return f"ERROR: PostgREST API request failed: {e}"

@tool
def read_todo_by_id(todo_id: int) -> str:
    """Fetches a single todo task by its unique ID."""
    try:
        url = f"{POSTGREST_BASE_URL}/todos?id=eq.{todo_id}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not data:
            return f"Error: Todo with ID {todo_id} not found."
        return f"Todo {todo_id} details:\n{data[0]}"
    except requests.exceptions.RequestException as e:
        return f"ERROR: PostgREST API request failed: {e}"

@tool
def update_todo_by_id(todo_id: int, task: str = None, done: bool = None, due: str = None) -> str:
    """Modifies the task, status, or due date of a specific todo item."""
    update_data = {}
    if task is not None:
        update_data['task'] = task
    if done is not None:
        update_data['done'] = done
    if due is not None:
        update_data['due'] = due

    if not update_data:
        return "Error: No update fields (task, done, due) were provided."

    try:
        url = f"{POSTGREST_BASE_URL}/todos?id=eq.{todo_id}"
        headers = {'Content-Type': 'application/json', 'Prefer': 'return=representation'}
        response = requests.patch(url, json=update_data, headers=headers)
        response.raise_for_status()
        
        updated_todo = response.json()
        if not updated_todo:
             return f"Error: Todo with ID {todo_id} not found or no change was made."
        return f"Successfully updated Todo {todo_id}:\n{updated_todo[0]}"
        
    except requests.exceptions.RequestException as e:
        return f"ERROR: PostgREST API request failed: {e}"

@tool
def delete_todo_by_id(todo_id: int) -> str:
    """Permanently removes a task by its ID."""
    try:
        url = f"{POSTGREST_BASE_URL}/todos?id=eq.{todo_id}"
        response = requests.delete(url)
        # PostgREST returns 204 No Content for a successful DELETE
        if response.status_code == 204:
            return f"Successfully deleted Todo with ID {todo_id}."
        elif response.status_code == 200 and not response.text:
             return f"Successfully deleted Todo with ID {todo_id} (PostgREST returned 200 with no content)."
        elif response.status_code == 404:
            return f"Error: Todo with ID {todo_id} not found."
        else:
             response.raise_for_status()
             return f"Unexpected successful response for DELETE Todo {todo_id}." # Should be rare
             
    except requests.exceptions.RequestException as e:
        return f"ERROR: PostgREST API request failed: {e}"

@tool
def filter_todo_by_due_date(due_date: str, operator: str = 'eq') -> str:
    """Filters tasks based on the due date using comparison operators ('eq', 'gt', 'lt', 'gte', 'lte')."""
    valid_operators = ['eq', 'gt', 'lt', 'gte', 'lte']
    if operator not in valid_operators:
        return f"Error: Invalid operator '{operator}'. Must be one of {valid_operators}."
    
    try:
        # Format the URL query parameter for PostgREST filtering
        url = f"{POSTGREST_BASE_URL}/todos?due={operator}.{due_date}"
        response = requests.get(url)
        response.raise_for_status()
        return f"Filter results (due {operator} {due_date}):\n{response.json()}"
    except requests.exceptions.RequestException as e:
        return f"ERROR: PostgREST API request failed: {e}"

# --- 3. The Core LangGraph Components ---

# List of all tools available to the LLM
tools = [
    list_all_todos,
    search_todo_by_title,
    read_todo_by_id,
    update_todo_by_id,
    delete_todo_by_id,
    filter_todo_by_due_date,
]

# Define the Agent State
class AgentState(TypedDict):
    """The state for the graph. It includes a list of messages."""
    messages: Annotated[List[BaseMessage], operator.add]

# Initialize the LLM and bind the tools
llm = ChatOllama(model=LLM_MODEL, temperature=0)
llm_with_tools = llm.bind_tools(tools)
tool_executor = ToolNode(tools)

# Define the 'Agent' node
def run_agent(state: AgentState):
    """The node that calls the LLM for reasoning and/or tool use."""
    
    # System Prompting for the Assistant's persona and rules
    tool_list_text = (
        "Available Functions:\n"
        "1. list_all_todos()\n"
        "2. search_todo_by_title(query: str)\n"
        "3. read_todo_by_id(todo_id: int)\n"
        "4. update_todo_by_id(todo_id: int, task: str = None, done: bool = None, due: str = None)\n"
        "5. delete_todo_by_id(todo_id: int)\n"
        "6. filter_todo_by_due_date(due_date: str, operator: str = 'eq')"
    )
    
    system_prompt = (
        "You are the TodoAssistant, an expert agent for managing a to-do list via a PostgREST API. "
        "Your responses must be based ONLY on the results of the tool calls you perform. "
        "If a user asks for a task that involves creating a NEW todo item, you MUST inform them that you can only read, search, update, and delete tasks. "
        "NEVER make up a task ID. ALWAYS try to use a function if it matches the request. "
        "If the request is invalid or cannot be executed with the available tools, return the following exact text (and nothing else):\n\n"
        f"{tool_list_text}"
    )
    
    # Prepend the system prompt to the messages
    # CHANGE 2: Use SystemMessage instead of HumanMessage for the system prompt
    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    # Call the LLM
    try:
        response = llm_with_tools.invoke(messages)
    except Exception as e:
        # Handle LLM API errors gracefully
        error_message = f"LLM API Error: Failed to generate response. {e}"
        # If the LLM call fails, we assume it's an 'invalid request'
        return {"messages": [AIMessage(content=tool_list_text)]}

    # Custom check for the "invalid request" rule
    if "return the following exact text" in response.content or response.content == tool_list_text.strip():
        return {"messages": [AIMessage(content=tool_list_text)]}
        
    return {"messages": [response]}

# Define the 'Tool' node
def execute_tools(state: AgentState):
    """The node that executes the tool calls requested by the LLM."""
    ai_message = state["messages"][-1]
    
    # Handle the custom 'invalid request' output
    if ai_message.content.strip().startswith("Available Functions:"):
        return state # Skip tool execution if the agent returned the error message

    tool_calls = ai_message.tool_calls
    results = []
    for tool_call in tool_calls:
        # The ToolExecutor handles mapping the function name/args to the actual Python function
        output = tool_executor.invoke(tool_call)
        
        # We append the ToolMessage result back to the state
        results.append(ToolMessage(
            content=output,
            name=tool_call["name"],
            tool_call_id=tool_call["id"],
        ))
    
    return {"messages": results}

# Define the conditional edge (Router)
def should_continue(state: AgentState) -> str:
    """Decide whether to continue or end based on the last message."""
    last_message = state["messages"][-1]
    
    # If the last message is the "Available Functions" text, we terminate.
    if last_message.content.strip().startswith("Available Functions:"):
        return "end"

    # If the LLM requested a tool call, we go to the tool node.
    if last_message.tool_calls:
        return "tools"
    
    # Otherwise, the LLM has formulated a final, natural language answer, so we stop.
    return "end"

# --- 4. Build the LangGraph ---

# 1. Create the graph
workflow = StateGraph(AgentState)

# 2. Add nodes (Agent and Tool Executor)
workflow.add_node("agent", run_agent)
workflow.add_node("tools", execute_tools)

# 3. Set the entry point
workflow.set_entry_point("agent")

# 4. Add the edges
# Conditional edge from agent: If tool calls exist -> go to tools; otherwise -> end
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "end": END},
)

# Direct edge from tools: After tool execution, always go back to the agent for final synthesis
workflow.add_edge("tools", "agent")

# 5. Compile the graph
todo_assistant = workflow.compile()

# --- 5. Helper Function for Interaction ---

def ask_todo_assistant(prompt: str):
    """Invokes the compiled graph and prints the final output."""
    initial_message = HumanMessage(content=prompt)
    
    # Run the graph and stream the steps (optional, but good for debugging)
    final_output = None
    for step in todo_assistant.stream({"messages": [initial_message]}):
        final_output = step
        # Optional: Print the step-by-step trace
        # print(f"Current State: {step}") 
    
    # Extract the final AI message
    if final_output and final_output.get("agent"):
        final_response = final_output["agent"]["messages"][-1].content
    else:
        # This handles the case where the graph terminates on the first step (e.g., direct LLM response)
        final_response = final_output[END]["messages"][-1].content
        
    print(f"\n[TodoAssistant Final Response]\n{final_response}")


# --- 6. Example Usage (Needs a running PostgREST server on localhost:3000) ---

if __name__ == "__main__":
    print(f"--- TodoAssistant Initialized with LLM: {LLM_MODEL} ---")
    print(f"PostgREST Base URL: {POSTGREST_BASE_URL}")
    print("----------------------------------------------------------\n")

    # Example 1: Successful tool use (List all tasks)
    print(">>> Request: 'Show me my entire todo list.'")
    ask_todo_assistant("Show me my entire todo list.")
    
    # Example 2: Successful tool use (Update a task)
    print("\n>>> Request: 'I finished the first tutorial, mark task 1 as done.'")
    # Assuming 'finish tutorial 0' is ID 1
    ask_todo_assistant("I finished the first tutorial, mark task 1 as done.")

    # Example 3: Invalid request / Restricted function (Create)
    print("\n>>> Request: 'Add a new todo item: Learn LangGraph.'")
    ask_todo_assistant("Add a new todo item: Learn LangGraph.")
    
    # Example 4: Search
    print("\n>>> Request: 'Find the task where I need to pat myself on the back.'")
    ask_todo_assistant("Find the task where I need to pat myself on the back.")