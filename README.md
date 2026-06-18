# Bulls and Cows LangGraph Agent

This Streamlit demo shows an Agent vs Human Bulls and Cows game. The opponent
agent uses LangGraph to guess the human's secret number, while a Coach Agent
keeps notes for the human player. Gemini can optionally generate a human-like
coach hint from the clue notebook.

## Run

```powershell
pip install -r requirements.txt
$env:LANGSMITH_TRACING="true"
$env:LANGSMITH_API_KEY="<your-key>"
$env:LANGSMITH_PROJECT="bulls-and-cows-agent"
$env:LANGSMITH_ENDPOINT="https://eu.api.smith.langchain.com"
$env:GOOGLE_API_KEY="<your-gemini-key>"
streamlit run main.py
```

`GOOGLE_API_KEY` enables the optional Gemini Coach button. You can also use
`GEMINI_API_KEY`. If no Gemini key is set, the deterministic Coach Agent still
works.

You can also paste Gemini and LangSmith keys directly into the app under
**API setup: Gemini and LangSmith**. Those values are only applied to the local
Streamlit session and are not saved in the repository.

Optional Gemini model override:

```powershell
$env:GEMINI_MODEL="gemini-2.0-flash"
```

## Demo Script

1. Click **Start game**.
2. Think of a valid number such as `427`.
3. Give bulls/cows feedback for the opponent agent's guess.
4. Make your own guess against the opponent's secret number.
5. Use **Coach Agent Notes** and **Coach notebook** to track clues.
6. Click **Ask Gemini Coach** when `GOOGLE_API_KEY` or `GEMINI_API_KEY` is set.
7. Open LangSmith and show the node-by-node trace for LangGraph and Gemini calls.

Rules: digits are unique, the first digit cannot be `0`, a bull is a correct
digit in the correct position, and a cow is a correct digit in the wrong
position.
