import os
import mysql.connector
from mysql.connector import pooling
from functools import lru_cache

# Initialize connection pool
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "appuser"),
    password=os.getenv("DB_PASSWORD", "StrongPass123!"),
    database=os.getenv("DB_NAME", "testdb")
)

def get_connection():
    return db_pool.get_connection()

@lru_cache(maxsize=1)
def get_db_structure() -> str:
    """Same logic as before, but cached to avoid repeated heavy queries"""
    try:
        conn = get_connection()
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
        WHERE c.table_schema = DATABASE()
        ORDER BY c.table_name, c.ordinal_position;
        """)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return "\n".join(str(row) for row in result)
    except Exception as e:
        return f"Error fetching structure: {e}"

def execute_query(query: str, allow_destructive: bool = False) -> str:
    """
    Executes query. 
    If the query is destructive (DELETE, DROP, ALTER, TRUNCATE) and allow_destructive is False,
    it returns a safety warning instead of executing.
    """
    normalized_query = query.strip().upper()
    is_destructive = any(normalized_query.startswith(cmd) for cmd in ["DROP", "DELETE", "ALTER", "TRUNCATE"])
    
    if is_destructive and not allow_destructive:
        return (
            f"[SAFETY BLOCK] The query '{query}' is destructive. "
            "To execute this, you must explicitly set allow_destructive=True. "
            "Please ask the user for confirmation before proceeding."
        )

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        
        result = ""
        if normalized_query.startswith("SELECT"):
            # Fetch column headers
            columns = [i[0] for i in cursor.description]
            rows = cursor.fetchall()
            
            # Convert to list of dicts for JSON serialization
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            import json
            # handle date/decimal serialization if needed, simplistic for now:
            result = json.dumps(results, default=str)
        else:
            conn.commit()
            result = f"Query executed successfully. {cursor.rowcount} row(s) affected."
            
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        return f"Error executing query: {e}"
