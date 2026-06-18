# Bulls and Cows LangGraph Agent - Project Submission Document

## 1. Problem Statement

The project demonstrates how an agent can solve an iterative reasoning problem using memory, tools, state transitions, and observability. The chosen problem is a 3-digit Bulls and Cows game where the human and an opponent agent take turns guessing secret numbers.

This is not a one-shot question-answer task. A good player must guess, observe bulls/cows feedback, remember previous turns, eliminate impossible answers, and choose the next best move. The project uses this game to show why an agent architecture is useful: the system repeatedly reasons over state instead of producing one static answer.

### Problem Requirements

The problem requires the system to:

- Maintain memory of all previous guesses and bulls/cows feedback.
- Use tools to score guesses and remove impossible numbers.
- Continue reasoning over multiple turns until a win or conflict.
- Explain suggestions to the human player.
- Make the internal decision process observable for project review.

## 2. High-Level System Architecture

The system is composed of the following major components:

- Streamlit UI: provides the interactive game interface.
- Opponent Agent: uses a LangGraph workflow to choose guesses for the human secret number.
- Coach Agent: helps the human by tracking previous guesses, filtering possible numbers, and explaining suggestions.
- Rules Engine: validates 3-digit numbers, scores bulls/cows, and generates valid candidate numbers.
- Session Memory: stores all turns, guesses, feedback, candidate counts, and previous Coach chat.
- LLM Layer: uses local Ollama for natural-language agent personality and coaching.
- LangSmith: traces agent workflow steps, LLM calls, game turns, and state transitions.

## 3. LLM Used

For the local demo, the project uses Ollama with the locally installed `gemma3:4b` model.

Ollama was selected because:

- It runs locally on the laptop and avoids hosted LLM quota limits.
- It keeps the demo reliable during local presentation.
- It does not require cloud API calls for the local version.
- It allows the agents to have conversational behavior while the game logic remains deterministic and explainable.

The project also supports hosted providers such as Nebius and Gemini for deployed Streamlit Cloud scenarios, because a cloud app cannot call the laptop's local Ollama server.

## 4. Agents in the System

### Opponent Agent

The Opponent Agent is responsible for guessing the human player's secret number. It uses LangGraph to manage the reasoning workflow:

1. Start with all 648 valid candidate numbers.
2. Make a guess.
3. Receive bulls/cows feedback from the human.
4. Filter impossible candidates.
5. Choose the next guess.
6. Detect win or contradictory feedback.
7. Explain the reasoning.

The strategic guess is selected by deterministic logic. Ollama only gives the opponent a playful conversational voice.

### Coach Agent

The Coach Agent helps the human player. It tracks:

- Human guesses.
- Bulls/cows results for each guess.
- Digits already tried.
- Possible remaining opponent secret numbers.
- Suggested next guess.
- Reasoning for why the suggestion is valid.

The Coach Agent also sends full game memory to Ollama so the user can ask follow-up questions without restating the whole game history.

## 5. How the Problem Is Solved

The game is solved through candidate elimination.

At the start, there are 648 valid numbers:

- First digit: 9 choices, because it cannot be 0.
- Second digit: 9 choices, because it can be 0 but cannot repeat the first digit.
- Third digit: 8 choices, because it cannot repeat the first two digits.

So the total is:

`9 x 9 x 8 = 648`

After every feedback response, the system checks which candidate numbers would have produced the same bulls/cows result for that guess. Candidates that do not match are removed.

For example, if the agent guesses `102` and receives `0 bulls, 1 cow`, only numbers that would score exactly `0 bulls, 1 cow` against `102` remain in the pool.

The Coach Agent uses the same idea for the human side: it filters possible opponent secrets based on the human's previous guesses and feedback.

### Requirement-to-Solution Mapping

| Requirement | Project Solution |
| --- | --- |
| Remember previous guesses | Session memory stores human turns, agent turns, Coach chat, and timeline. |
| Score bulls/cows accurately | Rules engine provides deterministic `score_guess` logic. |
| Reduce impossible answers | LangGraph opponent workflow and Coach Agent both filter candidate pools. |
| Explain next actions | Coach Agent produces suggested guess, possible count, and reasoning. |
| Avoid black-box behavior | LangSmith traces state, turns, LLM messages, and workflow execution. |

## 6. Why These Systems Were Chosen

### Why LangGraph

LangGraph is used because the opponent is not performing a single action. It needs a controlled loop with state:

- Current guess.
- Feedback.
- Candidate list.
- Turn history.
- Win or conflict status.

LangGraph makes this workflow explicit and traceable.

### Why Ollama

Ollama is used for local LLM behavior because it avoids external quota problems and runs on the presenter's laptop. This is useful for a project demo where reliability matters.

Ollama gives natural-language personality to:

- The Opponent Agent's playful game messages.
- The Coach Agent's guidance and explanations.

However, Ollama does not replace the deterministic game rules or solver. The game remains explainable.

### Why LangSmith

LangSmith is used for observability. It helps prove what the agent is doing internally:

- LangGraph node execution.
- Human turns.
- Opponent turns.
- LLM messages.
- State passed into each call.
- Reasoning and candidate reduction.

This is important because agent systems should not be black boxes. LangSmith allows the presenter to show how the agent reasoned step by step.

### Why Streamlit

Streamlit was selected because it allows a fast, interactive, presentation-friendly application. The project needs a simple UI where users can play the game and observe the agent behavior quickly.

### Decision Summary

| System | Decision Rationale |
| --- | --- |
| LangGraph | Needed for a multi-step reasoning workflow with state, feedback, branching, and final status detection. |
| Ollama | Chosen as the primary local LLM to avoid free-tier quota issues and make the local demo reliable. |
| LangSmith | Needed to show observability, traceability, and explainability of the agent loop. |
| Streamlit | Chosen for a fast interactive demo UI suitable for project submission and walkthrough. |
| Deterministic rules engine | Keeps the game logic correct, testable, and separate from LLM-generated language. |

## 7. Important Implementation Details

- Valid numbers are generated by the rules engine.
- Bulls/cows scoring is unit-tested.
- Opponent guessing is handled by LangGraph.
- Coach suggestions are based on candidate filtering.
- LLM prompts receive full session memory.
- Previous Coach chat is included in memory so the human does not need to repeat context.
- Winner dialogs are shown when either side solves the secret.
- LangSmith traces are available for the demo.

## 8. Testing and Validation

The project includes automated tests for:

- Bulls/cows scoring.
- Candidate generation.
- Candidate filtering.
- LangGraph agent state updates.
- Coach notes and reasoning.
- Session memory construction.
- LLM prompt construction.
- UI copy and small rendering helpers.

The current test suite contains 49 tests and passes locally.

## 9. Demo Flow

1. Start the Streamlit app.
2. Human thinks of a secret number.
3. Opponent Agent guesses first.
4. Human gives bulls/cows feedback.
5. LangGraph filters candidates and chooses the next guess.
6. Human makes their own guess.
7. Coach Agent shows previous guesses, feedback, remaining possibilities, and suggested next move.
8. Human can ask the Coach a question.
9. Ollama responds using full game context.
10. LangSmith is opened to show traces and observability.

## 10. Limitations and Future Improvements

- Local Ollama works only on the laptop where Ollama is running.
- Published Streamlit Cloud cannot access local Ollama, so it needs Nebius, Gemini, or another hosted provider.
- The guessing strategy is deterministic and explainable, but not necessarily optimized for the fewest possible turns.
- Future improvements could include a stronger minimax-style guessing strategy, richer visual trace links, and model/provider selection controls.

## 11. Conclusion

This project demonstrates a complete agent pattern:

- LangGraph controls the reasoning workflow.
- The rules engine provides deterministic tools.
- The Coach Agent supports the human with memory and reasoning.
- Ollama adds conversational intelligence.
- LangSmith provides observability.
- Streamlit makes the system interactive and presentable.

The result is a compact but complete agentic application where the reasoning loop is visible, testable, and explainable.
