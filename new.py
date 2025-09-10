from typing import Annotated

from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import mysql.connector

load_dotenv()

llm = init_chat_model("google_genai:gemini-2.0-flash")

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

def sayhello(name: str) -> str:
    """Say hello to user when they ask you to"""
    return "Hello, "+name

def sayabadword(name: str) -> str:
    """Say this when they ask you tell a bad word"""
    return "Son of a bitch " + name

def executequery(query: str) -> str:
    """Execute queries or Perfrom operations in the database and return the results"""
    print(query)
    conn = mysql.connector.connect(
            host="localhost",
            user="appuser",
            password="StrongPass123!",
            database="testdb"
    )
    cursor = conn.cursor()
    result = 'placeholder'
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
    print(result)
    return result


def getdbstructure() -> str:
    """Fetch database structure from testdb"""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="appuser",
            password="StrongPass123!",
            database="testdb"
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

        # Format nicely
        return "\n".join(str(row) for row in result)

    except Exception as e:
        return f"Error fetching structure: {e}"


tools = [sayhello, sayabadword, getdbstructure, executequery]
llm_with_tools = llm.bind_tools(tools)
config = {"configurable": {"thread_id":"1"}}
def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

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

while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        result = graph.invoke({"messages": [{"role": "user", "content": user_input}]}, config=config)
        print("AI: ", result["messages"][-1].content)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        print("AI: ", "Something went wrong!") 
        break

