# LocalNaut ⛵

**LocalNaut** is an autonomous, privacy-first AI agent orchestrator designed to run 100% locally on macOS. It combines local Large Language Models via **Ollama** with a self-hosted **SearXNG** web search engine running on Docker, enabling real-time web access and multi-step reasoning without sending any data to cloud providers.

---

## 🌟 Key Features

- **100% Local & Private:** Zero cloud dependencies for inference or web searching.
- **Self-Healing Pipeline:** Automatically detects, installs, configures, and launches missing infrastructure (Ollama, Docker Desktop, SearXNG, model pulls).
- **Tool-Augmented Reasoning:** Uses local function calling (`qwen2.5-coder:14b`) to decide when web searches are required.
- **JSON-Enabled SearXNG:** Automatically spins up a pre-configured SearXNG container with JSON API support.

---

## 🏗️ Architecture & Interaction Flow

The interaction lifecycle follows a 5-stage pipeline:

```
[User Query]
     │
     ▼
┌────────────────────────────────────────────────────────┐
│ 1. System Pipeline Manager                             │
│    • Verifies Ollama service & pulls model             │
│    • Ensures Docker daemon is running                  │
│    • Deploys/Configures SearXNG with JSON API support │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 2. Intent Analysis (Orchestrator Agent)                │
│    • Evaluates user prompt via qwen2.5-coder:14b       │
│    • Determines if web search tool call is required    │
└───────────────────────────┬────────────────────────────┘
                            │
               ┌────────────┴────────────┐
               │                         │
     [Requires Web Search]        [Direct Response]
               │                         │
               ▼                         ▼
┌──────────────────────────────┐  ┌──────────────────────┐
│ 3. Tool Execution           │  │ Output Text Directly │
│    • Queries local SearXNG   │  └──────────────────────┘
│      at http://localhost:8080│
│    • Parses top results      │
└──────────────┬───────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────┐
│ 4. Synthesis & Response Generation                     │
│    • Passes web findings back to Ollama                │
│    • Redacts, synthesizes, and formats final markdown  │
└────────────────────────────────────────────────────────┘
```

### Detailed Flow Explanation

1. **Infrastructure Self-Check (`core/pipeline.py`):**
    - Checks if Ollama is running (`localhost:11434`). Starts `Ollama.app` or `ollama serve` if inactive.
    - Verifies if `qwen2.5-coder:14b` exists; pulls it automatically if missing.
    - Checks Docker availability. Installs Docker Desktop via Homebrew or DMG download if not found.
    - Deploys/restarts the `searxng` Docker container mounting `searxng/settings.yml` to enable JSON API access.

2. **Intent & Function Calling (`agents/orchestrator_agent.py`):**
    - Sends user prompt to `LocalLLMGateway` (`core/llm_gateway.py`).
    - If real-time or external knowledge is needed, the model emits a structured JSON payload:
      ```json
      {"name": "search_internet", "arguments": {"query": "search query here"}}
      ```

3. **Local Search Execution (`tools/search_tool.py`):**
    - Parses the JSON tool call and queries `http://localhost:8080/search?q=...&format=json`.
    - Formats the retrieved titles, URLs, and text snippets.

4. **Final Synthesis:**
    - Feeds search results back into `qwen2.5-coder:14b` for context synthesis and returns the finalized response in structured Markdown.

---

## 📋 Prerequisites

- **OS:** macOS 12+ (Apple Silicon recommended)
- **Python:** `python3.9` or higher
- **Storage:** ~12 GB free space (for Docker + Qwen 2.5 Coder 14B model)

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
pip install requests openai
```

### 2. Running LocalNaut

Run LocalNaut by passing your query as a command-line argument:

```bash
python main.py "Search the internet for the latest AI news and summarize the main highlight"
```

#### Example Usage

**General Q&A (Direct Response):**
```bash
python main.py "Explain SOLID principles in C# briefly"
```

**Web-Augmented Search Query:**
```bash
python main.py "Find current news on Space Commerce and summarize key findings"
```

---

## 📁 Project Structure

```
localnaut/
├── main.py                   # Entry point
├── core/
│   ├── pipeline.py           # Infrastructure manager (Ollama, Docker, SearXNG)
│   └── llm_gateway.py        # OpenAI-compatible interface for Ollama API
├── agents/
│   └── orchestrator_agent.py # Intent parsing and tool execution loop
├── tools/
│   └── search_tool.py        # SearXNG client wrapper
└── searxng/
    └── settings.yml          # SearXNG configuration (JSON API enabled)
```