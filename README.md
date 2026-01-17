# QueryPilot

An intelligent, AI-powered SQL database assistant that enables natural language interaction with databases. QueryPilot bridges the gap between users and complex SQL queries by leveraging advanced language models to understand natural language requests and execute them safely against your databases.

**Status**: ⚠️ Work in Progress - Actively under development

## Overview

QueryPilot is designed to become an industry-ready agent for seamless database interaction. It uses cutting-edge AI to:
- Convert natural language queries into SQL
- Execute queries safely with built-in safeguards
- Analyze data and generate visualizations
- Maintain conversation context across sessions
- Provide schema understanding and database exploration

## Features

✅ **Current Features:**
- Natural language to SQL conversion using Groq LLM (llama-3.3-70b)
- Agentic workflow with LangGraph for intelligent decision-making
- Safe query execution with destructive operation safeguards
- Database schema introspection and caching
- JSON-based data analysis and visualization
- Persistent conversation history with SQLite checkpointing
- Connection pooling for efficient database access
- Token management and message trimming for context optimization

🚧 **In Development:**
- Multi-database support (MySQL, PostgreSQL, SQLite, etc.)
- Advanced AI features (query optimization, cost estimation, anomaly detection)
- Web interface and REST API
- Query result caching and optimization
- Performance monitoring and analytics

## Tech Stack

- **LLM Integration**: [Groq](https://groq.com/) - High-performance inference
- **Agent Framework**: [LangGraph](https://langchain-ai.github.io/langgraph/) - Graph-based agent orchestration
- **LLM Library**: [LangChain](https://langchain.com/) - LLM abstractions and tools
- **Database**: MySQL with connection pooling
- **Data Analysis**: Pandas for data manipulation
- **Visualization**: Matplotlib for chart generation
- **Persistence**: SQLite for conversation checkpointing
- **Language**: Python 3.x

## Project Structure

```
Querypilot/
├── main.py              # Main agent logic and LangGraph orchestration
├── database.py          # Database connection and query execution
├── tools_analysis.py    # Data analysis and visualization tools
├── test_api.py          # API and integration tests
├── .env                 # Environment configuration (not in repo)
└── Checkpoint.sqlite    # Conversation history storage
```

## Getting Started

### Prerequisites
- Python 3.8+
- MySQL database
- Groq API key
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/saivijayragav/Querypilot.git
   cd Querypilot
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   GROQ_MODEL_NAME=llama-3.3-70b-versatile
   GROQ_API_KEY=your_groq_api_key_here
   
   DB_HOST=localhost
   DB_USER=appuser
   DB_PASSWORD=your_password
   DB_NAME=testdb
   ```

5. **Run the agent**
   ```bash
   python main.py
   ```

## Usage

### Basic Example

```python
from main import graph

# Start a conversation with QueryPilot
config = {"configurable": {"thread_id": "1"}}
initial_input = {"messages": [HumanMessage(content="Show me all tables in the database")]}

response = graph.invoke(initial_input, config)
```

### Supported Operations

- **Explore Database**: "What tables do we have?" → Returns schema
- **Query Data**: "Get all users from the users table" → Executes SELECT
- **Analyze Data**: "Plot the sales trend over time" → Generates visualization
- **Safe Modifications**: "Delete inactive users" → Prompts for explicit confirmation

## Safety Features

QueryPilot includes multiple safeguards:
- ⛔ Blocks destructive operations (DELETE, DROP, ALTER, TRUNCATE) by default
- 🔐 Requires explicit user confirmation for sensitive operations
- 💾 Maintains query history for auditing
- ⏱️ Token management to prevent context overflow
- 🔄 Connection pooling to prevent resource exhaustion

## Future Roadmap

### Near-term (v0.2-0.3)
- [ ] Web UI with chat interface
- [ ] REST API endpoints
- [ ] Support for PostgreSQL and SQLite
- [ ] Query optimization suggestions
- [ ] Advanced data visualization options

### Medium-term (v0.4-0.5)
- [ ] Multi-database management (switch between databases seamlessly)
- [ ] Query performance analysis and optimization
- [ ] Cost estimation for large queries
- [ ] Data anomaly detection
- [ ] Custom function/stored procedure support
- [ ] Export results in multiple formats (CSV, Excel, Parquet)

### Long-term (v1.0+)
- [ ] Enterprise-grade security and audit logging
- [ ] Role-based access control (RBAC)
- [ ] Data lineage and impact analysis
- [ ] Advanced AI features (intelligent caching, predictive query generation)
- [ ] Multi-language support
- [ ] Kubernetes-ready deployment

## Contributing

Contributions are welcome! This project is in active development and we're looking for:
- Feature implementations
- Bug fixes
- Documentation improvements
- Test coverage
- Performance optimizations

Please feel free to open issues and pull requests.

## Architecture Highlights

### Agent Workflow
```
User Input → Chatbot Node → Tool Invocation → Execution → Response
     ↑                                                        ↓
     └────────────────── Feedback Loop ──────────────────────┘
```

The LangGraph workflow enables:
- Intelligent tool selection based on context
- Multi-step reasoning for complex queries
- State persistence across interactions
- Graceful fallback and error handling

### Database Safety
All queries go through a safety filter:
1. Parse and normalize query
2. Check for destructive operations
3. Block or prompt for confirmation
4. Execute safely within a transaction
5. Return results or error messages

## Known Limitations (Current Phase)

- MySQL support only (expanding soon)
- Limited advanced AI features
- No web UI yet
- No production-grade security features
- Single-threaded operation

## License

MIT License - feel free to use this project as you wish!

## Author

**Sai Vijay Ragav**
- GitHub: [@saivijayragav](https://github.com/saivijayragav)
- Email: (add your contact info)

## Acknowledgments

- [LangChain](https://langchain.com/) for the amazing LLM toolkit
- [LangGraph](https://langchain-ai.github.io/langgraph/) for agent orchestration
- [Groq](https://groq.com/) for fast and efficient inference
- Open-source community for amazing libraries like Pandas and Matplotlib

---

**Made with ❤️ to make databases more accessible**

*Last Updated: January 2026*
