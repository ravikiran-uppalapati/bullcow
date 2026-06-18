# Bulls and Cows Agent Architecture

This diagram explains how the project works for a presentation or project submission. The core idea is that the game is not a one-shot answer. It is an agent loop: guess, observe feedback, remember history, reduce candidates, choose the next move, and explain what happened.

## Component Architecture

```mermaid
flowchart TB
    User["Human Player"]
    UI["Streamlit Game UI<br/>main.py"]

    subgraph Game["Game Experience"]
        Intro["Intro / Start Game"]
        AgentTurn["Opponent Agent Turn"]
        HumanTurn["Human Turn"]
        CoachPanel["Coach Agent Notes"]
        Winner["Winner Congratulations Dialog"]
    end

    subgraph Rules["Bulls and Cows Rules Engine"]
        Candidates["Candidate Generator<br/>all valid 3-digit numbers"]
        Scorer["Bulls/Cows Scorer<br/>score_guess(secret, guess)"]
        Validator["Input Validator<br/>unique digits, no leading zero"]
    end

    subgraph LangGraph["LangGraph Opponent Workflow"]
        Init["initialize_game"]
        Generate["generate_guess"]
        Feedback["receive_feedback"]
        Filter["filter_candidates"]
        Choose["choose_next_guess"]
        Detect["detect_win_or_conflict"]
        Explain["explain_reasoning"]
    end

    subgraph Coach["Coach Agent"]
        Notes["Build Coach Notes"]
        History["Previous Human Guesses<br/>with bulls/cows"]
        Possibles["Remaining Possible Secrets"]
        Suggest["Suggested Next Guess"]
        Reason["Reasoning Summary"]
    end

    subgraph Memory["Session Memory"]
        AgentMemory["Opponent Guess History"]
        HumanMemory["Human Guess History"]
        CoachChat["Previous Coach Chat"]
        Timeline["Merged Turn Timeline"]
    end

    subgraph LLM["LLM Providers"]
        Ollama["Local Ollama<br/>preferred for laptop demo"]
        Nebius["Nebius Hosted LLM<br/>preferred for Streamlit Cloud"]
        Gemini["Gemini Fallback"]
        Deterministic["Deterministic Fallback<br/>when no LLM is configured"]
    end

    subgraph Observability["LangSmith Observability"]
        TraceGraph["LangGraph Node Traces"]
        TraceTurns["Human and Agent Turn Traces"]
        TraceLLM["LLM Message Traces"]
        Debug["Debug State and Reasoning"]
    end

    User --> UI
    UI --> Intro
    UI --> AgentTurn
    UI --> HumanTurn
    UI --> CoachPanel
    UI --> Winner

    AgentTurn --> LangGraph
    HumanTurn --> Scorer
    HumanTurn --> Validator
    LangGraph --> Candidates
    LangGraph --> Scorer

    Init --> Generate --> Feedback --> Filter --> Choose --> Detect --> Explain

    CoachPanel --> Coach
    Notes --> History
    Notes --> Possibles
    Notes --> Suggest
    Notes --> Reason

    LangGraph --> AgentMemory
    HumanTurn --> HumanMemory
    CoachPanel --> CoachChat
    AgentMemory --> Timeline
    HumanMemory --> Timeline

    Memory --> LLM
    LLM --> CoachPanel
    LLM --> AgentTurn

    Ollama -->|"local app"| UI
    Nebius -->|"published app"| UI
    Gemini -->|"fallback hosted provider"| UI
    Deterministic --> UI

    LangGraph --> Observability
    HumanTurn --> Observability
    LLM --> Observability
```

## Turn-by-Turn Flow

```mermaid
sequenceDiagram
    participant Human as Human Player
    participant UI as Streamlit UI
    participant Graph as LangGraph Opponent Agent
    participant Rules as Rules Engine
    participant Coach as Coach Agent
    participant LLM as Ollama / Hosted LLM
    participant Smith as LangSmith

    Human->>UI: Start game
    UI->>Graph: Create initial agent state
    Graph->>Rules: Generate valid candidates
    Graph->>UI: First opponent guess
    UI->>LLM: Ask for opponent personality line with game memory
    LLM-->>UI: Playful opponent message
    UI->>Smith: Trace opponent LLM message

    Human->>UI: Enter bulls/cows feedback for opponent guess
    UI->>Graph: Send feedback
    Graph->>Rules: Score/filter candidates
    Graph->>Graph: Choose next valid guess
    Graph->>Smith: Trace receive, filter, choose, detect nodes

    Human->>UI: Enter human guess
    UI->>Rules: Score human guess against app secret
    UI->>Coach: Update human guess history
    Coach->>Rules: Filter possible secrets from all human clues
    Coach-->>UI: Suggested next guess, possible count, reasoning
    UI->>Smith: Trace human guess turn

    Human->>UI: Ask Coach a question
    UI->>LLM: Send full session memory and previous Coach chat
    LLM-->>UI: Proactive guidance and reasoning
    UI->>Smith: Trace Coach LLM message

    alt Human wins
        UI->>Human: Winner congratulations pop-up
    else Opponent wins
        UI->>Human: Opponent solved number pop-up
    end
```

## What Each Component Does

| Component | Responsibility | Why it matters |
| --- | --- | --- |
| Streamlit UI | Runs the game screen, inputs, dialogs, Coach panel, and notebook | Makes the agent demo interactive and easy to present |
| Rules Engine | Validates numbers, generates candidates, scores bulls/cows | Keeps game behavior deterministic and testable |
| LangGraph Opponent Agent | Manages the opponent reasoning loop and state transitions | Shows a real agent workflow rather than a single chatbot response |
| Coach Agent | Tracks human guesses, filters possible opponent secrets, suggests next guess, explains why | Helps the human play better using memory and reasoning |
| Session Memory | Stores agent turns, human turns, Coach chat, and a merged timeline | Gives LLM calls the full context without the user repeating history |
| Ollama / Nebius / Gemini | Adds conversational personality and natural-language coaching | Makes the agents feel human while strategy remains explainable |
| LangSmith | Traces LangGraph steps, human turns, and LLM messages | Proves what the agent knew, what it did, and why |

## Five-Minute Presentation Script

1. **Problem**: Bulls and Cows is not a one-answer task. It needs repeated reasoning: guess, feedback, memory, elimination, and next move.
2. **UI**: Streamlit gives the game surface where the human plays against the agent.
3. **LangGraph**: The opponent agent is controlled by a LangGraph workflow. It keeps candidate state, receives feedback, filters impossible numbers, and chooses the next guess.
4. **Coach Agent**: The Coach helps the human by tracking previous guesses, bulls/cows responses, possible remaining secrets, and the suggested next move.
5. **LLM Layer**: Ollama runs locally for the demo. Nebius or Gemini can be used for hosted deployment. The LLM gives the opponent and coach natural language, but it does not replace the deterministic game logic.
6. **Memory**: Every LLM call gets full game context: previous guesses, responses, current phase, candidate count, reasoning, and previous Coach chat.
7. **LangSmith**: LangSmith makes the hidden reasoning visible. It traces the LangGraph nodes, human turns, LLM calls, and state changes.
8. **Closing**: This project demonstrates the full agent pattern: LangGraph for workflow, deterministic tools for logic, LLM for conversation, Streamlit for interaction, and LangSmith for observability.

## Deployment Notes

- Local demo: use `OLLAMA_MODEL` and `OLLAMA_BASE_URL`.
- Published Streamlit app: use `NEBIUS_API_KEY` or Gemini keys because Streamlit Cloud cannot reach your laptop's local Ollama server.
- LangSmith EU endpoint: `https://eu.api.smith.langchain.com`.
