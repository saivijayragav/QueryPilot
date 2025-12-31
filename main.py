from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import SystemMessage, HumanMessage
import sqlite3
import mysql.connector

load_dotenv()
import os

def sayhello(name: str) -> str:
    """Say hello to user when they ask you to"""
    return "Hello, "+name



def executequery(query: str) -> str:
    """Execute queries or Perfrom operations in the database and return the results"""
    conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "appuser"),
            password=os.getenv("DB_PASSWORD", "StrongPass123!"),
            database=os.getenv("DB_NAME", "testdb")
    )
    cursor = conn.cursor()
    result = ""
    try:
        cursor.execute(query)
        if query.strip().lower().startswith("select"):
            result = cursor.fetchall()
        else:
            conn.commit()
            result = f"{cursor.rowcount} row(s) affected."
    except Exception as e:
        result = "Exception occured " + str(e)
        conn.rollback()
    finally:    
        cursor.close()
        conn.close()
    return result


def getdbstructure() -> str:
    """Fetches the complete schema of the 'testdb' database, including table names, column names, data types, and relationships.
    Call this tool proactively before writing any query if you are unsure about the database structure.
    """
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "appuser"),
            password=os.getenv("DB_PASSWORD", "StrongPass123!"),
            database=os.getenv("DB_NAME", "testdb")
        )
        cursor = conn.cursor()
        cursor.execute("""
        SELECT
            c.table_name,
            c.column_name,
            c.column_type,
            c.is_nullable,
            c.column_default,
            tc.constraint_type,
            k.referenced_table_name,
            k.referenced_column_name
        FROM information_schema.columns c
        LEFT JOIN information_schema.key_column_usage k
            ON c.table_name = k.table_name
           AND c.column_name = k.column_name
           AND c.table_schema = k.table_schema
        LEFT JOIN information_schema.table_constraints tc
            ON tc.constraint_name = k.constraint_name
           AND tc.table_schema = c.table_schema
        WHERE c.table_schema = 'testdb'
        ORDER BY c.table_name, c.ordinal_position;
        """)
        result = cursor.fetchall()
        cursor.close()
        conn.close()

        return "\n".join(str(row) for row in result)

    except Exception as e:
        return f"Error fetching structure: {e}"


tools = [sayhello, getdbstructure, executequery]


llm = init_chat_model("google_genai:gemini-2.0-flash")

llm_with_tools = llm.bind_tools(tools)

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

def chatbot(state: State):
    response = llm_with_tools.invoke(state["messages"]) 
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
            "Your primary rule is to always use the `getdbstructure` tool to understand the database schema "
            "before attempting to write or execute any SQL query. This gives you the necessary context. "
            "After understanding the structure, you must create and execute queries based on the user's request. "
            "**You are permitted to execute both DML (INSERT, UPDATE, DELETE) and DDL (ALTER, DROP, CREATE) queries "
            "to modify data and the database schema directly and automatically, without asking for confirmation.** "
            "Prefer concise explanations, but include query outputs when relevant."
       )
   ),
   HumanMessage(content="Start Session") 
]
graph.invoke({"messages": initial_messages}, config=config)

while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        if not user_input.strip():
            continue
        result = graph.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
        print("AI: ", result["messages"][-1].content)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        print("AI: ", "Something went wrong!") 
        break

