# Bulls and Cows LangGraph Agent

This Streamlit demo shows an Agent vs Human Bulls and Cows game. The opponent
agent uses LangGraph to guess the human's secret number, while a Coach Agent
keeps notes for the human player. A hosted LLM can power both the opponent's
playful game talk and the coach's reasoning note using the full per-session
game memory: agent guesses, human guesses, feedback, candidate counts, and the
merged turn timeline. Local Ollama is preferred when `OLLAMA_MODEL` is
configured; Nebius and Gemini are available as hosted fallbacks for deployed
apps.

The UI also includes an **Agent Toolbelt** panel showing the tools and skills
available to the agents, such as candidate generation, bulls/cows scoring,
candidate filtering, next-guess selection, coach memory, LLM chat, LLM
reasoning, and LangSmith tracing.

For a presentation-friendly architecture diagram, see
[`documents/architecture.md`](documents/architecture.md).

For the project submission document, see
[`documents/project_submission.pdf`](documents/project_submission.pdf). A Markdown source version is available at
[`documents/project_submission.md`](documents/project_submission.md).

## Local Setup With Ollama

Use this path when you want the LLM Coach and Opponent messages to run from
your own laptop without using Gemini, Nebius, or any hosted LLM quota.

### 1. Install Python dependencies

From the project folder:

```powershell
pip install -r requirements.txt
```

### 2. Install and start Ollama

Install Ollama from [https://ollama.com](https://ollama.com), then pull a local
chat model:

```powershell
ollama pull llama3.1
```

You can also use another local model, for example:

```powershell
ollama pull gemma3:4b
```

Keep Ollama running in the background. By default, the app expects Ollama at:

```text
http://localhost:11434
```

### 3. Configure local Streamlit secrets

Create a file called `.streamlit/secrets.toml` in the project folder. This file
is intentionally ignored by git so your API keys stay local.

```toml
OLLAMA_MODEL = "llama3.1"
OLLAMA_BASE_URL = "http://localhost:11434"

LANGSMITH_TRACING = "true"
LANGSMITH_API_KEY = "your-langsmith-key"
LANGSMITH_PROJECT = "bulls-and-cows-agent"
LANGSMITH_ENDPOINT = "https://eu.api.smith.langchain.com"
```

If your LangSmith account is not in the EU region, use the default US endpoint:

```toml
LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
```

### 4. Run the game

```powershell
streamlit run main.py
```

Open the local preview:

```text
http://127.0.0.1:8501/
```

### 5. What Ollama does in this project

Ollama is used as the local LLM behind the game personalities:

- **Opponent Agent voice**: reacts playfully to the game history and the
  current turn.
- **Coach Agent voice**: explains likely next guesses, remembers previous
  attempts, and gives reasoning using the full session history.

The actual bulls/cows scoring and candidate filtering are still deterministic
tools. This keeps the game correct while allowing the LLM to make the
experience conversational and engaging.

### 6. Streamlit Cloud note

A deployed Streamlit app cannot directly call `localhost` on your laptop. That
means local Ollama works for local demos, but not for the public Streamlit Cloud
link. For a public deployment, configure a hosted LLM provider such as Nebius or
Gemini in Streamlit secrets.

Example Streamlit Cloud secrets:

```toml
LANGSMITH_TRACING = "true"
LANGSMITH_API_KEY = "your-langsmith-key"
LANGSMITH_PROJECT = "bulls-and-cows-agent"
LANGSMITH_ENDPOINT = "https://eu.api.smith.langchain.com"

NEBIUS_API_KEY = "your-nebius-token"
NEBIUS_MODEL = "meta-llama/Meta-Llama-3.1-70B-Instruct"
```

## Quick Run With Environment Variables

```powershell
pip install -r requirements.txt
$env:LANGSMITH_TRACING="true"
$env:LANGSMITH_API_KEY="<your-key>"
$env:LANGSMITH_PROJECT="bulls-and-cows-agent"
$env:LANGSMITH_ENDPOINT="https://eu.api.smith.langchain.com"
$env:OLLAMA_MODEL="llama3.1"
streamlit run main.py
```

Alternative local Ollama environment variable setup:

```powershell
ollama pull llama3.1
$env:OLLAMA_MODEL="llama3.1"
$env:OLLAMA_BASE_URL="http://localhost:11434"
streamlit run main.py
```

For Streamlit Cloud, use a hosted provider because the cloud app cannot reach
your laptop's `localhost`. `NEBIUS_API_KEY` enables the live LLM Opponent and
Coach agents in the deployed app. You can also use `GOOGLE_API_KEY` or
`GEMINI_API_KEY` for Gemini. If no LLM is configured, deterministic fallback
messages and Coach Agent notes still work.

For Streamlit Community Cloud, add these values in the app's secrets/settings
instead of typing them into the app:

```toml
LANGSMITH_TRACING = "true"
LANGSMITH_API_KEY = "your-langsmith-key"
LANGSMITH_PROJECT = "bulls-and-cows-agent"
LANGSMITH_ENDPOINT = "https://eu.api.smith.langchain.com"
NEBIUS_API_KEY = "your-nebius-token"
NEBIUS_MODEL = "meta-llama/Meta-Llama-3.1-70B-Instruct"
```

Optional Gemini fallback:

```powershell
$env:GOOGLE_API_KEY="<your-gemini-key>"
$env:GEMINI_MODEL="gemini-2.0-flash"
```

## Demo Script

1. Click **Start game**.
2. Think of a valid number such as `427`.
3. Give bulls/cows feedback for the opponent agent's guess.
4. Make your own guess against the opponent's secret number.
5. Use **Coach Agent Notes** and **Coach notebook** to track clues.
6. With `OLLAMA_MODEL`, `NEBIUS_API_KEY`, `GOOGLE_API_KEY`, or `GEMINI_API_KEY`
   set, show the live Opponent and Coach Agent messages reacting to the full
   game history.
7. Open LangSmith and show `agent_feedback_turn`, LangGraph nodes,
   `human_guess_turn`, and `llm_agent_message` traces.

Rules: digits are unique, the first digit cannot be `0`, a bull is a correct
digit in the correct position, and a cow is a correct digit in the wrong
position.
