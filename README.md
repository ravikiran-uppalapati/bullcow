# Bulls and Cows LangGraph Agent

This Streamlit demo shows a one-person Bulls and Cows game with a LangGraph agent.
The main demo mode lets the agent guess a 3-digit number while LangSmith traces
each turn: feedback intake, candidate filtering, next guess selection, and the
reasoning summary.

## Run

```powershell
pip install -r requirements.txt
$env:LANGSMITH_TRACING="true"
$env:LANGSMITH_API_KEY="<your-key>"
$env:LANGSMITH_PROJECT="bulls-and-cows-agent"
streamlit run main.py
```

`OPENAI_API_KEY` is listed in the presentation plan for future LLM-backed
explanations, but this first version is deterministic and does not require an
LLM call.

## Demo Script

1. Choose **Agent guesses**.
2. Think of a valid number such as `427`.
3. Enter bulls/cows feedback for each agent guess.
4. Open LangSmith and show the node-by-node trace for the run.

Rules: digits are unique, the first digit cannot be `0`, a bull is a correct
digit in the correct position, and a cow is a correct digit in the wrong
position.
