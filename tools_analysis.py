import pandas as pd
import matplotlib
matplotlib.use('Agg') # Fix: Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
import json
import os
import time

def analyze_and_plot(data_json: str, user_request: str) -> str:
    """
    Analyzes data (JSON string) and generates a plot if requested.
    Returns a summary or path to the generated plot.
    
    The data_json should be a list of dictionaries (records).
    """
    print("analyze and plot is called")
    try:
        data = json.loads(data_json)
        if not data:
            return "No data provided for analysis."
            
        df = pd.DataFrame(data)
        
        # Attempt to convert object columns to numeric (e.g. "100.50" -> 100.50)
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass # Keep as object if conversion fails
        
        # Simple heuristic analysis based on request
        summary = df.describe().to_string()
        
        # Check if plot is requested
        request_lower = user_request.lower()
        print(df.dtypes)
        print(request_lower)
        if any(w in request_lower for w in ["plot", "chart", "graph", "visualize", "trend"]):
            plt.figure(figsize=(10, 6))
            
            # Simple auto-plot logic
            # Attempt to find numeric columns and a categorical/date column
            numeric_cols = df.select_dtypes(include=['number']).columns
            
            # Generate unique filename
            timestamp = int(time.time())
            chart_filename = f"chart_{timestamp}.png"
            chart_path = os.path.join(os.getcwd(), chart_filename)
            
            if len(numeric_cols) > 0:
                if "date" in df.columns or "time" in df.columns:
                    time_col = "date" if "date" in df.columns else "time"
                    df[time_col] = pd.to_datetime(df[time_col])
                    df.set_index(time_col)[numeric_cols[0]].plot()
                    plt.title(f"{numeric_cols[0]} over Time")
                elif len(df.columns) >= 2:
                    # Bar chart of first generic column vs first numeric
                    cat_col = df.columns[0]
                    if cat_col == numeric_cols[0] and len(df.columns) > 1:
                        cat_col = df.columns[1] # fallback
                    
                    if cat_col != numeric_cols[0]:
                        df.set_index(cat_col)[numeric_cols[0]].plot(kind='bar')
                        plt.title(f"{numeric_cols[0]} by {cat_col}")
                    else:
                         df[numeric_cols[0]].plot(kind='hist')
                         plt.title(f"Distribution of {numeric_cols[0]}")
                else:
                    df[numeric_cols[0]].plot(kind='hist')
                    plt.title(f"Distribution of {numeric_cols[0]}")
                
                plt.tight_layout()
                plt.savefig(chart_path)
                print("Saved to ", chart_path)
                plt.close()
                return f"Data Summary:\n{summary}\n\n[CHART GENERATED] Saved to: {chart_path}"
            else:
                return f"Data Summary:\n{summary}\n\n(No numeric columns found for plotting)"
        return f"Data Summary:\n{summary}"

    except Exception as e:
        print(e)
        return f"Error in analysis: {e}"
