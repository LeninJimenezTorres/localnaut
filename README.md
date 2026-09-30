# LocalNaut ⛵

**LocalNaut** is an autonomous, privacy-first AI agent orchestrator designed to run 100% locally on macOS[cite: 11]. It combines local Large Language Models via **Ollama** with a self-hosted **SearXNG** web search engine running on Docker, enabling real-time web access and multi-step reasoning without sending any data to cloud providers[cite: 11].

---

## 🌟 Key Features

- **100% Local & Private:** Zero cloud dependencies for inference or web searching[cite: 11].
- **Self-Healing Infrastructure Management:** Automatically detects, configures, and silently launches Ollama (via CLI or macOS app), Docker Desktop, and SearXNG in the background without manual intervention[cite: 10, 11].
- **Tool-Augmented Reasoning:** Uses local function calling (`qwen2.5-coder:14b`) to autonomously decide when web searches are required[cite: 11].
- **Interactive CLI (REPL):** Features a rich terminal interface with built-in commands (`/help`, `/clear`, `/reset`, `/history`, `/exit`), history retention, and seamless conversational memory[cite: 10].

---

## 🏗️ Architecture & Interaction Flow

The interaction lifecycle follows a 4-stage pipeline orchestrated over persistent user sessions[cite: 10, 11]:

```text
[User Query]
     │
     ▼
┌────────────────────────────────────────────────────────┐
│ 1. System Pipeline Manager (SystemPipelineManager)     │
│    • Silently verifies and starts the Ollama service   │
│    • Ensures the Docker daemon is running              │
│    • Deploys SearXNG with JSON API support             │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 2. Intent Analysis (Orchestrator & TaskSession)        │
│    • Ingests input into the session history            │
│    • Evaluates intent using qwen2.5-coder:14b          │
│    • Determines if search_internet(query="..") is need │
└───────────────────────────┬────────────────────────────┘
                            │
               ┌────────────┴────────────┐
               │                         │
     [Requires Web Search]        [Direct Response]
               │                         │
               ▼                         ▼
┌──────────────────────────────┐  ┌──────────────────────┐
│ 3. Tool Execution            │  │ Outputs text         │
│    • Queries local SearXNG   │  │ directly in          │
│      at http://localhost:8080│  │ Markdown format      │
│    • Extracts top results    │  └──────────────────────┘
└──────────────┬───────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────┐
│ 4. Synthesis & Response Generation                     │
│    • Injects web findings back into session memory     │
│    • qwen2.5-coder synthesizes final formatted data    │
└────────────────────────────────────────────────────────┘
```

### Detailed Flow Explanation

1. **Infrastructure Self-Check (`core/pipeline.py`):**
    - Verifies if Ollama is running (`localhost:11434`)[cite: 10]. It attempts to start it silently via CLI (`ollama serve`) or by opening the native macOS app if no response is detected[cite: 10].
    - Checks Docker availability and starts Docker Desktop if necessary[cite: 10].
    - Deploys the `searxng` Docker container, mounting `searxng/settings.yml` to enable JSON and HTML format support[cite: 10].

2. **Intent & Function Calling (`agents/orchestrator_agent.py`):**
    - Stores the user message in `TaskSession` and sends it through the `LocalLLMGateway`[cite: 10].
    - If the LLM requires up-to-date information, it emits a tool call detected via regular expressions[cite: 10].

3. **Local Search Execution (`tools/search_tool.py`):**
    - Extracts the `query` parameter and queries the local SearXNG API[cite: 10].
    - Formats the top 5 retrieved results, unifying the title, URL, and descriptive snippet[cite: 10].

4. **Final Synthesis:**
    - Logs the web results as a temporary user role prompt, instructing the LLM to answer the initial query based on the newly retrieved information[cite: 10].

---

## 📋 Prerequisites

- **OS:** macOS 12+ (Apple Silicon recommended)[cite: 11]
- **Python:** `python3.9` or higher[cite: 11]
- **Storage:** ~12 GB free space (for Docker + Qwen 2.5 Coder 14B model)[cite: 11]

---

## 🚀 Getting Started

### 1. Clone & Set Up Environment

```bash
git clone [https://github.com/your-repo/localnaut.git](https://github.com/your-repo/localnaut.git)
cd localnaut

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt rich markdown-it-py pygments
```

### 2. Running LocalNaut

LocalNaut supports two main modes of operation configured in `main.py`[cite: 10]:

#### A. Interactive CLI with Memory (REPL)
Launch a continuous and persistent conversational environment by running the main file without arguments[cite: 10]:

```bash
python main.py
```

*The console provides real-time commands to manage your session:*[cite: 10]
- `/help`     - Shows the help menu[cite: 10].
- `/clear`    - Clears the terminal screen[cite: 10].
- `/reset`    - Resets and clears the conversational memory of the active session[cite: 10].
- `/history`  - Displays the current number of messages kept in context[cite: 10].
- `/exit`     - Closes the LocalNaut environment[cite: 10].

#### B. Single Shot Command Mode
Pass your query directly as an argument for the orchestrator to resolve, print the response, and exit the program immediately[cite: 10]:

```bash
python main.py "Find recent news about quantum computing and summarize the key points"
```

---

## 📁 Project Structure

```text
localnaut/
├── main.py                   # Entry point and interactive REPL loop management[cite: 10]
├── requirements.txt          # Base package dependencies (openai, httpx, requests, pydantic)[cite: 10]
├── core/
│   ├── pipeline.py           # Auto-start manager for Ollama, Docker, and SearXNG[cite: 10]
│   ├── llm_gateway.py        # OpenAI-compatible gateway for the local qwen2.5-coder model[cite: 10]
│   └── session.py            # `TaskSession` state controller, system rules, and memory[cite: 10]
├── agents/
│   └── orchestrator_agent.py # Two-pass analytical engine for data parsing and injection[cite: 10]
├── tools/
│   ├── search_tool.py        # HTTP client to format SearXNG responses[cite: 10]
│   ├── firecrawl_tool.py     # Optional web scraping client for full URL extraction[cite: 10]
│   └── searxng_tool.py       # JSON Schema definition and local search engine parameters[cite: 10]
└── searxng/
    └── settings.yml          # Environment variables and configuration for SearXNG[cite: 10]
```