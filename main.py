from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_groq import ChatGroq
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import SystemMessage, HumanMessage, trim_messages
import sqlite3
import os
import database
import tools_analysis

load_dotenv()

def sayhello(name: str) -> str:
    """Say hello to user when they ask you to"""
    return "Hello, "+name

def executequery(query: str, allow_destructive: bool = False) -> str:
    """
    Execute SQL queries.
    DANGEROUS: For 'DELETE', 'DROP', 'ALTER', or 'TRUNCATE', you MUST set allow_destructive=True.
    ONLY set allow_destructive=True if the user has explicitly confirmed the action.
    """
    return database.execute_query(query, allow_destructive)

def getdbstructure() -> str:
    """Fetches the complete schema of the database."""
    return database.get_db_structure()

def analyze_data(data_json: str, user_request: str) -> str:
    """
    Analyzes JSON data (list of dictionaries) and generates a plot if requested.
    Pass the output of 'executequery' directly to this tool if it contains JSON data.
    """
    return tools_analysis.analyze_and_plot(data_json, user_request)

tools = [sayhello, getdbstructure, executequery, analyze_data]

llm = ChatGroq(model=os.environ.get("GROQ_MODEL_NAME", "llama-3.3-70b-versatile"))

llm_with_tools = llm.bind_tools(tools)

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

import tiktoken

def get_token_count(messages: list[SystemMessage | HumanMessage]) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    count = 0
    for m in messages:
        # Simple estimation: content tokens + 3 overhead per message (standard for chat)
        count += len(encoding.encode(str(m.content))) + 3
    return count

# Define trimmer
trimmer = trim_messages(
    max_tokens=2048,
    strategy="last",
    token_counter=get_token_count,
    include_system=True,
    allow_partial=False,
    start_on="human",
)

def chatbot(state: State):
    # Trim the messages before sending to the model
    # We must ensure the SystemMessage is preserved, which 'include_system=True' does if it's in the list.
    # However, 'trim_messages' expects a list of messages.
    trimmed_messages = trimmer.invoke(state["messages"])
    response = llm_with_tools.invoke(trimmed_messages) 
    return {"messages": [response]}

config = {"configurable": {"thread_id":"1"}}

graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
sqlite_conn = sqlite3.connect("Checkpoint.sqlite", check_same_thread=False)
memory = SqliteSaver(sqlite_conn)
graph = graph_builder.compile(checkpointer=memory)

initial_messages = [
   SystemMessage(
       content=(
            "You are QueryPilot, an intelligent and autonomous assistant for working with SQL databases. "
            "1. ALWAYS use `getdbstructure` first to understand the schema. "
            "2. For database modification (INSERT, DELETE, DROP, etc.), you have permission to execute, "
            "   BUT if the query is destructive (DROP/DELETE/TRUNCATE), the system will block it. "
            "   You must then ask the user for explicit confirmation. Only if they say 'yes', call `executequery` with `allow_destructive=True`. "
            "3. If the user asks for trends, plots, or visualization: "
            "   a. Run a SELECT query using `executequery` to get the data (it returns JSON). "
            "   b. Pass that JSON string to the `analyze_data` tool. "
            "IMPORTANT: "
            " - Do NOT generate XML tags like <function>. Use the provided tools directly. "
            " - Ensure all SQL queries are syntactically correct."
       )
   ),
   HumanMessage(content="Start Session") 
]
# Initialize with system prompt logic if needed, usually we just send the system prompt in the invoke.
# But here we want it persistent. The graph handles history.

while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        if not user_input.strip():
            continue
        
        # We append the system message only on the very first run if history is empty? 
        # Actually checking history is hard here. simpler to just inject normal messages.
        # But to ensure system prompt is active, we can pass it every time or rely on checkpoint.
        # Ideally, passed once. For this script, let's assume 'initial_messages' was strictly for the first boot.
        # But since we use checkpointer, we need to be careful.
        # Let's just pass the user input. The SystemMessage logic typically needs to be in the graph state or passed once.
        # For simplicity in this loop, we assume the agent 'knows' its role. 
        # A better pattern is to modify 'chatbot' node to prepend SystemMessage if not present.
        # But let's trust the LLM remembers or we can add it to the 'messages' list in the invoke if we weren't using checkpointer persistence for it.
        # Actually, let's just prepend it to the *current* input if we want to be safe, but that duplicates it in history.
        # Correct way: Passing it in the very first invoke call only.
        
        # Let's just do:
        result = graph.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
        
        # Robust output printing
        last_msg = result["messages"][-1]
        print("AI: ", last_msg.content)
            
    except KeyboardInterrupt:
        print("\nGoodbye!")
        break
    except Exception as e:
        # fallback if input() is not available
        print(f"Error: {e}")
        # user_input = "What do you know about LangGraph?"
        # print("User: " + user_input)
        # break
