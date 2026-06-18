# Bulls and Cows LangGraph Agent

This Streamlit demo shows an Agent vs Human Bulls and Cows game. The opponent
agent uses LangGraph to guess the human's secret number, while a Coach Agent
keeps notes for the human player. A hosted LLM can power both the opponent's
playful game talk and the coach's reasoning note using the full per-session
game memory: agent guesses, human guesses, feedback, candidate counts, and the
merged turn timeline. Nebius is preferred when `NEBIUS_API_KEY` is configured;
Gemini is used as a fallback provider when a Gemini key is configured instead.

The UI also includes an **Agent Toolbelt** panel showing the tools and skills
available to the agents, such as candidate generation, bulls/cows scoring,
candidate filtering, next-guess selection, coach memory, LLM chat, LLM
reasoning, and LangSmith tracing.

## Run

```powershell
pip install -r requirements.txt
$env:LANGSMITH_TRACING="true"
$env:LANGSMITH_API_KEY="<your-key>"
$env:LANGSMITH_PROJECT="bulls-and-cows-agent"
$env:LANGSMITH_ENDPOINT="https://eu.api.smith.langchain.com"
$env:NEBIUS_API_KEY="<your-nebius-token>"
$env:NEBIUS_MODEL="meta-llama/Meta-Llama-3.1-70B-Instruct"
streamlit run main.py
```

`NEBIUS_API_KEY` enables the live LLM Opponent and Coach agents on Streamlit
Cloud. You can also use `GOOGLE_API_KEY` or `GEMINI_API_KEY` for Gemini. If no
LLM key is set, deterministic fallback messages and Coach Agent notes still
work.

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
6. With `NEBIUS_API_KEY`, `GOOGLE_API_KEY`, or `GEMINI_API_KEY` set, show the
   live Opponent and Coach Agent messages reacting to the full game history.
7. Open LangSmith and show `agent_feedback_turn`, LangGraph nodes,
   `human_guess_turn`, and `llm_agent_message` traces.

Rules: digits are unique, the first digit cannot be `0`, a bull is a correct
digit in the correct position, and a cow is a correct digit in the wrong
position.
