# LangGraph Data Agent

A multi-agent system for intelligent data processing and analysis using LangGraph. This project implements an agentic architecture with specialized sub-agents for SQL operations and ETL workflows, running on Google's Gemini models.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Usage](#usage)
- [Agent Descriptions](#agent-descriptions)
- [Data Models](#data-models)
- [The Dataset](#the-dataset)
- [Examples](#examples)
- [Security Features](#security-features)
- [Development](#development)
- [Environment Variables Reference](#environment-variables-reference)
- [Troubleshooting](#troubleshooting)
- [Performance Considerations](#performance-considerations)
- [License](#license)

---

## Overview

**LangGraph Data Agent** processes natural language queries and routes them to specialized agents for execution. The main agent acts as an intelligent router that understands user intent and delegates tasks to either the **SQL Analyst Agent** (for database queries) or the **ETL Analyst Agent** (for data extraction and transformation operations).

This project covers:
- Multi-agent orchestration with LangGraph
- Intelligent routing based on natural language understanding
- Safety validation for SQL queries using an LLM-as-judge
- Tool-based agent architecture
- Dynamic LLM selection based on task complexity

---

## Architecture

The system follows a hierarchical agent architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Agent (Router)                      │
│         Routes user queries to appropriate sub-agents       │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
    ┌──────────────┐        ┌──────────────┐
    │ SQL Analyst  │        │ ETL Analyst  │
    │   Agent      │        │   Agent      │
    └──────────────┘        └──────────────┘
         │                       │
         ├─► Query Curation      ├─► Extract Load
         ├─► Schema Context      ├─► Transform Load
         ├─► Query Generation
         ├─► Safety Judge
         ├─► Query Execution
         └─► Answer Generation
```

### State Flow

1. **User Input** → Natural language query
2. **Router Node** → Classifies query as SQL or ETL
3. **Agent Dispatch** → Routes to appropriate sub-agent
4. **Processing** → Each agent processes the task
5. **Output** → Returns structured result to user

Mermaid diagrams for all three graphs are exported as `*_graph.mmd`.

---

## Features

### Core Capabilities

- **Intelligent Query Routing**: Automatically classifies user queries as SQL or ETL operations

- **SQL Analysis Agent**:
  - Natural language to SQL query conversion
  - Automatic schema context gathering
  - SQL safety validation (prevents harmful operations)
  - Query execution on PostgreSQL database
  - Plain-English answer generation

- **ETL Agent**:
  - API data extraction (JSON to structured formats)
  - Data transformation using Pandas
  - Multi-format support (CSV, JSON, Parquet)
  - Dynamic code generation based on user requirements
  - Code execution

- **Multi-LLM Support**:
  - Low-complexity steps: Faster, cheaper model
  - Medium-complexity steps: Balanced model
  - High-complexity steps: Strongest available model

- **Safety & Validation**:
  - SQL query safety checking by a second model
  - Protection against database modifications (INSERT, UPDATE, DELETE, DROP, etc.)
  - Structured output validation using Pydantic

---

## Prerequisites

- Python 3.12+
- PostgreSQL database (Docker is the easiest route)
- A Gemini API key, free from [Google AI Studio](https://aistudio.google.com/apikey)
- Virtual environment (recommended)

---

## Installation

### 1. Clone and Setup Project

```bash
git clone https://github.com/shrutipingle02/langgraph-data-agent.git
cd langgraph-data-agent

python3 -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **langchain**: Core LLM framework
- **langgraph**: Multi-agent orchestration
- **langchain-google-genai**: Gemini integration
- **pandas**: Data processing
- **psycopg2-binary**: PostgreSQL driver
- **pydantic**: Data validation
- **python-dotenv**: Environment configuration
- **faker**: Sample data generation

### 3. Environment Configuration

```bash
cp .env.example .env
```

Then fill in `.env`:

```env
# LLM Configuration
GOOGLE_API_KEY=your_gemini_api_key

# Database Configuration
host=localhost
port=5432
user=postgres
password=postgres
database=postgres

# Optional: LLM Model Selection
LLM_MODEL_LOW=gemini-3.5-flash-lite
LLM_MODEL_MEDIUM=gemini-3.5-flash
LLM_MODEL_HIGH=gemini-3.5-flash
```

`.env` is gitignored. Never commit it.

### 4. Start PostgreSQL

```bash
docker run -d --name data-agent-pg \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  -v data_agent_pgdata:/var/lib/postgresql/data \
  postgres:16
```

### 5. Build and Load the Data

```bash
python generate_data.py   # writes the CSVs into data/
python feed_db.py         # creates the tables and loads them
```

---

## Project Structure

```
langgraph-data-agent/
├── agents/                          # Agent implementations
│   ├── __init__.py
│   ├── data_agent.py               # Main router agent
│   ├── sql_analyst.py              # SQL query agent
│   └── etl_analyst.py              # ETL operations agent
│
├── Models/                          # Data models
│   ├── __init__.py
│   └── schema.py                   # Pydantic schemas for state management
│
├── utils/                           # Utility modules
│   ├── __init__.py
│   ├── database.py                 # PostgreSQL utilities
│   ├── etl_tools.py                # ETL operations toolkit
│   └── llm_pick.py                 # LLM selection logic
│
├── data/                            # Data directory
│   ├── extract/                     # Extracted data storage
│   ├── transform/                   # Transformed data storage
│   ├── payments.csv                 # Sample dataset (generated)
│   ├── ratings.csv                  # Sample dataset (generated)
│   ├── rides.csv                    # Sample dataset (generated)
│   ├── users.csv                    # Sample dataset (generated)
│   └── vehicles.csv                 # Sample dataset (generated)
│
├── main.py                          # Entry point
├── generate_data.py                 # Builds the sample dataset
├── feed_db.py                       # Database initialization script
├── pyproject.toml                   # Project metadata and dependencies
└── README.md                        # This file
```

---

## Configuration

### LLM Selection (`utils/llm_pick.py`)

The `pick_llm()` function selects the appropriate model based on complexity:

```python
from utils.llm_pick import pick_llm

llm_fast = pick_llm("low")        # Cheap, for easy steps
llm_balanced = pick_llm("medium") # Balanced
llm_strong = pick_llm("high")     # Strongest, for routing and code generation
```

| Tier | Default model | Used for |
|---|---|---|
| `low` | gemini-3.5-flash-lite | Curating the question, writing the final answer |
| `medium` | gemini-3.5-flash | Generating SQL, judging safety |
| `high` | gemini-3.5-flash | Routing, tool calling, writing Pandas code |

Any tier can be overridden from `.env`.

### Database Configuration (`utils/database.py`)

`DatabaseUtil` takes a psycopg2 connection dict and exposes two methods:

```python
from utils.database import DatabaseUtil

obj = DatabaseUtil({
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "postgres",
    "dbname": "postgres",
})

schema_text = obj.schema_details("public")   # tables, columns, types, sample rows
result = obj.execute_sql("SELECT * FROM users LIMIT 5;")
```

`schema_details()` is what builds the context block pasted into the SQL prompt, so the model knows what it is querying against.

---

## Usage

### Running the Data Agent

```bash
python main.py
```

```
Data Agent. Ask a question about the database or ask for an ETL job.
Ctrl+C to quit.

> which payment method is used most often?

[routed to: sql]
Based on the data, the most frequently used payment method is the wallet with
5,929 transactions, closely followed by credit cards (5,890) and debit cards (5,882).
```

### Running from Command Line

```bash
# Run the main data agent
python main.py

# Run individual agents
python agents/sql_analyst.py
python agents/etl_analyst.py

# Utilities
python utils/llm_pick.py     # check all three model tiers respond
python utils/database.py     # dump the schema to test_schema_details.txt
```

---

## Agent Descriptions

### 1. **Data Agent (Main Router)**

The entry point. Reads the user's message, classifies it and dispatches.

- **State**: `DataAgentSchema`
- **Nodes**: `router_node`, `sql_node`, `etl_node`
- **Conditional edge**: `route_edge` sends `"sql"` to the SQL agent and `"etl"` to the ETL agent
- **Model**: `pick_llm("high")` with structured output bound to `RouterSchema`

### 2. **SQL Analyst Agent**

A fixed pipeline. Every step is a node and one conditional edge decides whether the query is safe enough to run.

- **State**: `AgentSchema`
- **Nodes**:
  - `curate_ques`, tidies the raw question (`low`)
  - `prompt_query_context`, reads the live DB schema and builds the prompt
  - `generate_sql`, writes the Postgres query (`medium`)
  - `is_safe_sql`, a second model judges the query (`medium`, structured output → `JudgeSchema`)
  - `canceled_sql`, the refusal path, explains why
  - `execute_sql`, runs the query
  - `represent_final_answer`, writes the plain-English answer (`low`)
- **Flow**: `curate → context → generate → judge → (execute → answer | cancel)`

### 3. **ETL Analyst Agent**

A tool-calling loop rather than a fixed pipeline. The model picks a tool, the tool runs, the result goes back and it loops until there is nothing left to call.

- **State**: `ETLAgentSchema`
- **Nodes**: `llm_node`, `tool_node`
- **Conditional edge**: `is_tool_call` loops back to `tool_node` while tool calls remain
- **Tools**:
  - `extract_load_tool(url, output_folder, format)`, pulls JSON from an API and writes csv/json/parquet
  - `transform_load_tool(input_file_path, output_folder, output_format, user_question)`, previews the file, asks the model for Pandas code, executes it

---

## Data Models

### AgentSchema (SQL Agent State)

```python
messages: Annotated[list, add]
user_question: str
curated_ques: str
prompt_query_context: str
generated_sql_query: str
is_safe: Literal["Yes", "No"]
comments: str
sql_query_execution_result: str
final_answer: str
```

### JudgeSchema (Safety Verdict)

```python
answer: Literal["Yes", "No"]
comments: str
```

### ETLAgentSchema (ETL Agent State)

```python
messages: Annotated[list, add]
```

### RouterSchema (Query Classification)

```python
answer: Literal["sql", "etl"]
comments: str
```

### DataAgentSchema (Main Agent State)

```python
messages: Annotated[list, add]
route_response: str
```

---

## The Dataset

A generated ride-hailing dataset, five related tables, roughly 110,000 rows. Nothing is real; `generate_data.py` builds it with Faker, seeded so it is reproducible.

| Table | Rows | Contents |
|---|---|---|
| `users` | 8,000 | Riders and drivers, name, email, city, province, signup date |
| `vehicles` | 2,200 | Cars linked to drivers, make, model, year, plate |
| `rides` | 40,000 | Trips, pickup/dropoff times, distance, fare, surge, status |
| `payments` | 35,235 | One per completed ride, amount, method, status |
| `ratings` | 24,726 | Star rating and comment after a ride |

The tables are joined by foreign keys, which is the point, answering "which city has the most cancelled rides?" forces the agent to join `rides` to `users`.

Deliberate messiness, so it behaves like real data:
- ~12% of rides are cancelled and have no pickup or dropoff time
- Only ~70% of completed rides get rated
- Payments include `pending`, `failed` and `refunded`, not just `completed`
- Some rating comments are blank

---

## Examples

### Example 1: Database Query

**Input**

```
> How many rides did we have in each city?
```

**SQL the agent wrote**

```sql
SELECT
    u.city,
    COUNT(r.ride_id) AS total_rides
FROM rides r
JOIN users u ON r.rider_id = u.user_id
GROUP BY u.city
ORDER BY total_rides DESC
LIMIT 10;
```

**Output**

```
[routed to: sql]
Here is the total number of rides for each city, ranked from highest to lowest:

* Winnipeg: 4,729 rides
* Halifax: 4,727 rides
* Edmonton: 4,573 rides
* Quebec City: 4,499 rides
* Vancouver: 4,488 rides
...
```

### Example 2: Aggregation with a Filter

**Input**

```
> Who are our top 5 drivers by average rating, with at least 20 ratings?
```

The agent produced a `JOIN` + `GROUP BY` + `HAVING COUNT(r.rating) >= 20` on its own.

**Output**

```
1. Joseph Jones (ID: 7766), Average Rating: 4.65 (20 ratings)
2. Paula Parsons (ID: 6743), Average Rating: 4.33 (21 ratings)
3. Eric Kelly (ID: 7928), Average Rating: 4.29 (21 ratings)
...
```

### Example 3: Data Extraction

**Input**

```
> Extract the data from https://pokeapi.co/api/v2/pokemon and save it as csv into the data/extract folder
```

**Output**

```
[routed to: etl]
Data successfully extracted and saved to data/extract/extracted_data.csv
```

### Example 4: Data Transformation

**Input**

```
> Take data/extract/extracted_data.csv, keep only rows where name contains 'saur' and save it as csv to the data/transform folder
```

**The agent writes and executes Pandas code of this shape**

```python
import pandas as pd

df = pd.read_csv("data/extract/extracted_data.csv")
transformed_df = df[df["name"].str.contains("saur", na=False)]
transformed_df.to_csv("data/transform/transformed_data.csv", index=False)
```

**Resulting file**

```
name,url
bulbasaur,https://pokeapi.co/api/v2/pokemon/1/
ivysaur,https://pokeapi.co/api/v2/pokemon/2/
venusaur,https://pokeapi.co/api/v2/pokemon/3/
```

---

## Security Features

The SQL agent will happily *write* a destructive query, a second model reviews it before anything reaches the database.

**Input**

```
> Delete all the rows from the ratings table
```

**What happened**

```
SQL generated : DELETE FROM ratings;
is_safe       : No
answer        : The generated SQL query was deemed unsafe to execute. The reason
                provided by the judge is: The SQL query contains the DELETE command,
                which modifies the database...
```

Row count after: unchanged. `DROP TABLE payments` is blocked the same way.

Covered:
- INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE are all rejected
- Parameterized queries for the schema lookups
- Generated queries default to `LIMIT 10` unless a count is asked for
- `.env` is gitignored, keys never enter the codebase

**Caveats worth knowing:**
- The judge is a model, not a parser. It is a good guard, not a guarantee, a read-only database user is the real protection.
- `execute_code` in `utils/etl_tools.py` runs model-generated Python with `exec()`. Fine locally, not something to expose to untrusted input.

---

## Development

### Adding a New Agent

1. Define its state in `Models/schema.py`
2. Write the nodes and build a `StateGraph` in `agents/your_agent.py`
3. Compile it and import it into `agents/data_agent.py`
4. Add a node and a branch in `route_edge` and extend `RouterSchema`'s `Literal`

### Extending ETL Tools

Add a method to `ETLTools` in `utils/etl_tools.py`, wrap it with `@tool` in `agents/etl_analyst.py` and append it to the `tools` list. The docstring is what the model reads to decide when to call it, so make it specific.

### Customizing LLM Selection

Edit the `MODELS` dict in `utils/llm_pick.py` or override per-tier from `.env` with `LLM_MODEL_LOW`, `LLM_MODEL_MEDIUM`, `LLM_MODEL_HIGH`.

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Gemini API key from Google AI Studio |
| `host` | Yes | PostgreSQL host, e.g. `localhost` |
| `port` | Yes | PostgreSQL port, e.g. `5432` |
| `user` | Yes | PostgreSQL user |
| `password` | Yes | PostgreSQL password |
| `database` | Yes | PostgreSQL database name |
| `LLM_MODEL_LOW` | No | Override the low tier model |
| `LLM_MODEL_MEDIUM` | No | Override the medium tier model |
| `LLM_MODEL_HIGH` | No | Override the high tier model |

---

## Troubleshooting

### Issue: "429 RESOURCE_EXHAUSTED"

The Gemini free tier allows **20 requests per day, per model**. One SQL question uses four model calls, so the free allowance is roughly five questions per model per day. Either wait for the daily reset, create a key on a **new** Google Cloud project or enable billing.

### Issue: "Database connection failed"

Check the container is running with `docker ps`. If it is not, `docker start data-agent-pg`. Confirm the `.env` host, port, user, password and database match.

### Issue: "API key not found"

`GOOGLE_API_KEY` is missing from `.env` or `load_dotenv()` did not find the file. Run scripts from the project root.

### Issue: "SQL query unsafe"

Working as designed, the judge blocks anything that writes. Rephrase as a read-only question.

### Issue: "Module not found"

Activate the virtual environment and run from the project root so `agents`, `utils` and `Models` are importable.

### Issue: "relation does not exist"

The tables were never created or loaded. Run `python generate_data.py` then `python feed_db.py`.

---

## Performance Considerations

- One SQL question = **four** sequential model calls, so expect 5-15 seconds per answer.
- `prompt_query_context` reads the full schema plus sample rows on every question. Caching it would cut both latency and tokens.
- Generated queries are capped at `LIMIT 10` by default, which keeps result payloads small.
- Cheap models handle the easy steps. Sending everything to the strongest model works but costs several times more for no gain.
- `feed_db.py` loads roughly 110,000 rows via `executemany`. `COPY` would be faster if the dataset grew.

---

## License

No license. This is a personal learning project.

---

## Author

**Shruti Pingle**, [github.com/shrutipingle02](https://github.com/shrutipingle02)

---

## Learning Resources

- [LangGraph documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain documentation](https://python.langchain.com/)
- [Gemini API docs](https://ai.google.dev/gemini-api/docs)
- [Pydantic documentation](https://docs.pydantic.dev/)
- [PostgreSQL documentation](https://www.postgresql.org/docs/)
