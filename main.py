import os
import random
from html import escape

import streamlit as st

from bulls_cows.agent_graph import create_initial_agent_state
from bulls_cows.coach import build_coach_notes
from bulls_cows.game import (
    CandidateFeedback,
    generate_candidates,
    is_valid_feedback,
    is_valid_secret,
    score_guess,
)
from bulls_cows.llm_coach import (
    DEFAULT_GEMINI_MODEL,
    generate_gemini_agent_message,
    generate_gemini_coach_tip,
    generate_gemini_referee_help,
)
from bulls_cows.memory import build_game_memory
from bulls_cows.session_flow import (
    next_phase_after_agent_feedback,
    next_phase_after_human_guess,
    start_game_phase,
)
from bulls_cows.telemetry import (
    record_human_guess_turn,
    record_llm_agent_message,
    run_traced_agent_feedback_turn,
)


def reset_game() -> None:
    st.session_state.agent_state = create_initial_agent_state()
    st.session_state.secret = random.choice(generate_candidates())
    st.session_state.player_history = []
    st.session_state.game_phase = "intro"
    st.session_state.human_feedback = None
    st.session_state.gemini_coach_tip = None
    st.session_state.llm_opponent_message = None
    st.session_state.llm_opponent_key = None
    st.session_state.llm_coach_reasoning = None
    st.session_state.llm_coach_key = None
    st.session_state.referee_help = None


def ensure_session() -> None:
    if "agent_state" not in st.session_state:
        reset_game()
    if "gemini_coach_tip" not in st.session_state:
        st.session_state.gemini_coach_tip = None
    if "llm_opponent_message" not in st.session_state:
        st.session_state.llm_opponent_message = None
    if "llm_opponent_key" not in st.session_state:
        st.session_state.llm_opponent_key = None
    if "llm_coach_reasoning" not in st.session_state:
        st.session_state.llm_coach_reasoning = None
    if "llm_coach_key" not in st.session_state:
        st.session_state.llm_coach_key = None
    if "referee_help" not in st.session_state:
        st.session_state.referee_help = None


def get_setting(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        secret_value = st.secrets.get(name, default)
    except Exception:
        secret_value = default
    return str(secret_value) if secret_value is not None else default


def get_streamlit_secrets() -> dict:
    try:
        return dict(st.secrets)
    except Exception:
        return {}


def apply_settings_to_environment(settings: dict | None = None) -> None:
    secret_values = settings if settings is not None else get_streamlit_secrets()
    for name in [
        "LANGSMITH_TRACING",
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
        "LANGSMITH_ENDPOINT",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
    ]:
        value = secret_values.get(name)
        if value and not os.getenv(name):
            os.environ[name] = str(value)


def render_game_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 12% 10%, rgba(250, 204, 21, .28), transparent 26%),
                radial-gradient(circle at 88% 16%, rgba(56, 189, 248, .28), transparent 28%),
                linear-gradient(135deg, #6d28d9 0%, #be185d 46%, #f97316 100%);
        }
        section.main > div {
            max-width: 900px;
        }
        div[data-testid="stHeader"] {
            background: transparent;
        }
        div[data-testid="stToolbar"] {
            display: none;
        }
        .block-container {
            padding-top: 1.4rem;
        }
        .game-shell {
            border: 3px solid rgba(255, 255, 255, .72);
            border-radius: 8px;
            background: linear-gradient(180deg, #fff7ed 0%, #fffbeb 100%);
            color: #3b0764;
            padding: 1rem;
            box-shadow: 0 22px 55px rgba(76, 29, 149, .36);
        }
        .game-shell h1, .game-shell h2, .game-shell h3, .game-shell p, .game-shell strong {
            color: #3b0764;
        }
        .top-hud {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: .55rem;
            margin-bottom: .85rem;
        }
        .hud-tile {
            border: 2px solid rgba(124, 58, 237, .22);
            border-radius: 8px;
            padding: .65rem .55rem;
            text-align: center;
            background: linear-gradient(180deg, #ffffff 0%, #fef3c7 100%);
            box-shadow: inset 0 -3px 0 rgba(180, 83, 9, .18);
        }
        .hud-label {
            color: #7c2d12;
            font-size: .72rem;
            font-weight: 900;
            text-transform: uppercase;
        }
        .hud-value {
            color: #4c1d95;
            font-weight: 950;
            font-size: 1.15rem;
        }
        .game-logo {
            border-radius: 8px;
            padding: .7rem;
            margin-bottom: .65rem;
            text-align: center;
            color: white;
            background: linear-gradient(135deg, #7c3aed 0%, #db2777 55%, #f59e0b 100%);
            box-shadow: inset 0 -4px 0 rgba(0, 0, 0, .18);
        }
        .game-logo-title {
            color: white;
            font-size: 1.8rem;
            font-weight: 950;
            line-height: 1.05;
            margin: 0;
        }
        .game-logo-subtitle {
            color: #fff7ed;
            font-weight: 800;
            margin-top: .25rem;
            font-size: .95rem;
        }
        .play-card {
            border: 3px solid #fbbf24;
            border-radius: 8px;
            padding: 1rem;
            background: linear-gradient(180deg, #ffffff 0%, #fdf2f8 100%);
            box-shadow: inset 0 -5px 0 rgba(219, 39, 119, .14);
        }
        .tile-row {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 88px));
            justify-content: center;
            gap: .7rem;
            margin: 1rem 0;
        }
        .number-tile {
            aspect-ratio: 1 / 1;
            border-radius: 8px;
            display: grid;
            place-items: center;
            color: white;
            font-size: 2.4rem;
            font-weight: 950;
            border: 3px solid rgba(255, 255, 255, .8);
            box-shadow: 0 8px 0 rgba(88, 28, 135, .28), inset 0 -7px 0 rgba(0, 0, 0, .18);
        }
        .tile-a { background: linear-gradient(180deg, #38bdf8, #2563eb); }
        .tile-b { background: linear-gradient(180deg, #f472b6, #db2777); }
        .tile-c { background: linear-gradient(180deg, #facc15, #f97316); }
        .quest-banner {
            border-radius: 8px;
            border: 2px solid #a855f7;
            background: #faf5ff;
            padding: .85rem;
            color: #581c87;
            font-weight: 850;
            text-align: center;
        }
        .arena {
            border: 0;
            border-radius: 10px;
            background: transparent;
            color: #3b0764;
            padding: 0;
            margin: 0;
            box-shadow: none;
        }
        .arena h2, .arena h3, .arena p, .arena strong {
            color: #3b0764;
        }
        .arena-topline {
            display: flex;
            justify-content: space-between;
            gap: .75rem;
            align-items: center;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }
        .round-pill {
            border: 2px solid #fbbf24;
            border-radius: 999px;
            padding: .35rem .75rem;
            color: #581c87;
            background: #fef3c7;
            font-weight: 950;
        }
        .game-title {
            font-size: 1.55rem;
            font-weight: 900;
            color: #f8fafc;
            margin: 0;
        }
        .duel-row {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: .55rem;
            align-items: stretch;
            margin: .65rem 0;
        }
        .player-panel {
            border: 2px solid #e9d5ff;
            border-radius: 8px;
            background: #ffffff;
            padding: .62rem;
            min-height: 74px;
        }
        .player-name {
            color: #7c2d12;
            font-size: .82rem;
            text-transform: uppercase;
            font-weight: 800;
        }
        .player-line {
            color: #4c1d95;
            font-size: .94rem;
            margin-top: .35rem;
            font-weight: 750;
        }
        .coach-panel {
            border: 3px solid #22c55e;
            border-radius: 8px;
            background: linear-gradient(180deg, #ecfdf5 0%, #dcfce7 100%);
            color: #064e3b;
            padding: .68rem;
            margin: .62rem 0;
            box-shadow: inset 0 -4px 0 rgba(21, 128, 61, .14);
        }
        .coach-panel h3, .coach-panel p, .coach-panel strong {
            color: #064e3b;
        }
        .llm-tip {
            font-size: .95rem;
        }
        .coach-title {
            color: #065f46;
            font-size: 1rem;
            font-weight: 950;
            margin: 0 0 .3rem 0;
        }
        .coach-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: .42rem;
            margin-top: .48rem;
        }
        .coach-chip {
            border: 2px solid rgba(5, 150, 105, .22);
            border-radius: 8px;
            background: #ffffff;
            color: #065f46;
            padding: .42rem;
            text-align: center;
            font-weight: 900;
            min-height: 3.35rem;
        }
        .memory-list {
            display: flex;
            gap: .4rem;
            flex-wrap: wrap;
            margin-top: .5rem;
        }
        .memory-pill {
            border-radius: 999px;
            background: #3b82f6;
            color: white;
            padding: .28rem .58rem;
            font-weight: 900;
        }
        .clue-board {
            margin-top: .7rem;
            display: grid;
            gap: .35rem;
        }
        .clue-row {
            display: grid;
            grid-template-columns: 72px 1fr 1fr;
            gap: .45rem;
            align-items: center;
            border: 2px solid rgba(5, 150, 105, .18);
            border-radius: 8px;
            background: #ffffff;
            padding: .38rem .5rem;
            color: #064e3b;
            font-weight: 850;
        }
        .clue-turn {
            color: #047857;
            font-size: .78rem;
            text-transform: uppercase;
            font-weight: 950;
        }
        .clue-guess {
            color: #1d4ed8;
            font-size: 1.05rem;
            font-weight: 950;
            letter-spacing: .08rem;
        }
        .clue-response {
            color: #7c2d12;
            font-weight: 950;
            text-align: right;
        }
        .versus {
            align-self: center;
            border-radius: 999px;
            border: 2px solid #ffffff;
            padding: .55rem .7rem;
            color: #ffffff;
            background: #db2777;
            font-weight: 900;
            box-shadow: 0 5px 0 rgba(157, 23, 77, .35);
        }
        .game-hero, .screen-card, .guess-card, .turn-card {
            border: 1px solid #d6dde8;
            border-radius: 8px;
            background: #ffffff;
            color: #111827;
        }
        .game-hero h3, .screen-card h3,
        .game-hero p, .screen-card p, .guess-card p, .turn-card,
        .game-hero strong, .screen-card strong, .guess-card strong, .turn-card strong {
            color: #111827;
        }
        .game-hero, .screen-card {
            padding: 1.2rem;
            margin-bottom: 1rem;
        }
        .game-hero {
            background: #f8fafc;
        }
        .countdown {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .5rem;
            margin: .75rem 0 1rem 0;
        }
        .countdown div {
            border: 1px solid #d6dde8;
            border-radius: 8px;
            text-align: center;
            padding: .8rem .25rem;
            font-size: 1.35rem;
            font-weight: 800;
            background: white;
            color: #111827;
        }
        .stage-countdown {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .6rem;
            margin-top: 1rem;
            min-height: 4.1rem;
        }
        .countdown-caption {
            text-align: center;
            color: #7c2d12;
            font-weight: 950;
            text-transform: uppercase;
            margin-top: .9rem;
        }
        .stage-countdown div {
            border: 3px solid #ffffff;
            border-radius: 8px;
            padding: .85rem .35rem;
            text-align: center;
            font-size: 1.65rem;
            font-weight: 950;
            color: #ffffff;
            background: linear-gradient(180deg, #fb7185, #db2777);
            box-shadow: 0 8px 0 rgba(136, 19, 55, .25), inset 0 -5px 0 rgba(0, 0, 0, .15);
            opacity: .2;
            transform: translateY(12px) scale(.82);
            animation: count-pop 3.2s ease-in-out infinite;
        }
        .stage-countdown div:nth-child(1) { animation-delay: 0s; }
        .stage-countdown div:nth-child(2) { animation-delay: .55s; }
        .stage-countdown div:nth-child(3) { animation-delay: 1.1s; }
        .stage-countdown div:nth-child(4) {
            animation-delay: 1.65s;
            background: linear-gradient(180deg, #34d399, #16a34a);
        }
        @keyframes count-pop {
            0%, 12% {
                opacity: .2;
                transform: translateY(12px) scale(.82) rotate(-2deg);
                filter: brightness(.85);
            }
            18%, 34% {
                opacity: 1;
                transform: translateY(-8px) scale(1.12) rotate(1deg);
                filter: brightness(1.18);
                box-shadow: 0 13px 0 rgba(136, 19, 55, .25), 0 0 28px rgba(251, 191, 36, .72), inset 0 -5px 0 rgba(0, 0, 0, .15);
            }
            42%, 100% {
                opacity: .35;
                transform: translateY(0) scale(.94);
                filter: brightness(.95);
            }
        }
        .guess-card {
            padding: 1rem;
            margin: .75rem 0;
            border: 0;
            background: transparent;
        }
        .guess-number {
            font-size: 3.4rem;
            line-height: 1;
            font-weight: 800;
            letter-spacing: .18rem;
            color: #111827;
        }
        .turn-card {
            padding: .75rem;
            margin-bottom: .55rem;
        }
        .tiny-label {
            color: #64748b;
            font-size: .82rem;
            text-transform: uppercase;
            font-weight: 700;
        }
        .speech {
            border-radius: 10px;
            padding: .9rem 1rem;
            margin: .75rem 0;
            font-size: 1.04rem;
            line-height: 1.45;
            font-weight: 760;
        }
        .speech-agent {
            background: #dbeafe;
            color: #1e3a8a;
            border: 2px solid #60a5fa;
        }
        .speech-human {
            background: #fef3c7;
            color: #422006;
            border: 2px solid #fbbf24;
        }
        .big-secret {
            border: 2px dashed #a855f7;
            border-radius: 8px;
            padding: .62rem;
            background: #faf5ff;
            color: #581c87;
            font-weight: 850;
        }
        .rules-card {
            border: 2px solid #fbbf24;
            border-radius: 8px;
            background: #fffbeb;
            color: #3b0764;
            padding: .75rem;
            margin: .55rem 0;
            font-weight: 760;
        }
        .action-note {
            color: #dbeafe;
            font-weight: 700;
            margin-top: .5rem;
        }
        div.stButton > button,
        div[data-testid="stFormSubmitButton"] button {
            border: 0;
            border-radius: 8px;
            background: linear-gradient(180deg, #22c55e, #15803d);
            color: white;
            font-weight: 950;
            min-height: 3rem;
            box-shadow: 0 7px 0 rgba(22, 101, 52, .36);
        }
        div.stButton > button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            border: 0;
            color: white;
            filter: brightness(1.05);
        }
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input {
            border-radius: 8px;
            border: 2px solid #a855f7;
            background: #ffffff;
            color: #3b0764;
            font-weight: 900;
            text-align: center;
            font-size: 1.15rem;
        }
        details {
            border-radius: 8px;
        }
        div[data-testid="stDialog"] div[role="dialog"] {
            border-radius: 8px;
            border: 3px solid #fbbf24 !important;
            background: #fffbeb !important;
            color: #3b0764 !important;
        }
        div[data-testid="stDialog"] div[role="dialog"] h2,
        div[data-testid="stDialog"] div[role="dialog"] p,
        div[data-testid="stDialog"] div[role="dialog"] label {
            color: #3b0764 !important;
        }
        @media (max-width: 720px) {
            .top-hud {
                grid-template-columns: 1fr;
            }
            .duel-row {
                grid-template-columns: 1fr;
            }
            .versus {
                justify-self: center;
            }
            .tile-row {
                grid-template-columns: repeat(3, minmax(0, 72px));
            }
            .number-tile {
                font-size: 2rem;
            }
            .game-logo-title {
                font-size: 1.55rem;
            }
            .coach-grid {
                grid-template-columns: 1fr;
            }
            .clue-row {
                grid-template-columns: 1fr;
            }
            .clue-response {
                text-align: left;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_countdown() -> None:
    st.markdown(
        """
        <div class="countdown-caption">Ready... set...</div>
        <div class="stage-countdown">
            <div>1</div>
            <div>2</div>
            <div>3</div>
            <div>GO</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_game_logo() -> None:
    st.markdown(
        """
        <div class="game-logo">
            <p class="game-logo-title">Agent vs Human: Bulls & Cows Blast</p>
            <div class="game-logo-subtitle">Opponent Agent attacks. Coach Agent helps the human fight back.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hud(round_label: str, agent_count: int, player_turn: int) -> None:
    st.markdown(
        f"""
        <div class="top-hud">
            <div class="hud-tile">
                <div class="hud-label">Level</div>
                <div class="hud-value">{round_label}</div>
            </div>
            <div class="hud-tile">
                <div class="hud-label">Agent Pool</div>
                <div class="hud-value">{agent_count}</div>
            </div>
            <div class="hud-tile">
                <div class="hud-label">Your Turn</div>
                <div class="hud-value">{player_turn}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_number_tiles(number: str) -> None:
    tiles = "".join(
        f'<div class="number-tile tile-{tile_class}">{digit}</div>'
        for digit, tile_class in zip(number, ["a", "b", "c"])
    )
    st.markdown(f'<div class="tile-row">{tiles}</div>', unsafe_allow_html=True)


def render_arena_header(round_label: str, prompt: str) -> None:
    st.markdown(
        f"""
        <div class="arena">
            <div class="arena-topline">
                <p class="game-title">Bulls and Cows Arena</p>
                <div class="round-pill">{round_label}</div>
            </div>
            <div class="duel-row">
                <div class="player-panel">
                    <div class="player-name">Opponent Agent</div>
                    <div class="player-line">Solves your secret.</div>
                </div>
                <div class="versus">VS</div>
                <div class="player-panel">
                    <div class="player-name">Human + Coach Agent</div>
                    <div class="player-line">You guess. Coach keeps notes.</div>
                </div>
            </div>
            <div class="big-secret">{prompt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_rules_expander() -> None:
    with st.expander("Rules and selections", expanded=False):
        st.markdown(
            """
            <div class="rules-card">
                <strong>Goal:</strong> Guess the opponent's 3-digit number before the opponent solves yours.<br>
                <strong>Number:</strong> 3 unique digits. First digit cannot be 0.<br>
                <strong>Bull:</strong> right digit, right position.<br>
                <strong>Cow:</strong> right digit, wrong position.<br>
                <strong>Turn flow:</strong> Opponent Agent guesses, you give bulls/cows, then you guess and get a response.
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_coach_panel() -> None:
    notes = build_coach_notes(st.session_state.player_history)
    game_memory = build_current_game_memory(notes)
    maybe_generate_llm_coach_reasoning(notes, game_memory)
    used_digits = ", ".join(notes["used_digits"]) if notes["used_digits"] else "None yet"
    gemini_tip = st.session_state.get("gemini_coach_tip")
    coach_reasoning = st.session_state.get("llm_coach_reasoning")

    st.markdown(
        f"""
        <div class="coach-panel">
            <p class="coach-title">Coach Agent Notes</p>
            <p><strong>Tip:</strong> {notes["tip"]}</p>
            <div class="coach-grid">
                <div class="coach-chip">
                    <div class="hud-label">Attempts</div>
                    <div>{notes["attempts"]}</div>
                </div>
                <div class="coach-chip">
                    <div class="hud-label">Suggested Guess</div>
                    <div>{notes["suggested_guess"]}</div>
                </div>
                <div class="coach-chip">
                    <div class="hud-label">Digits Tried</div>
                    <div>{used_digits}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if gemini_tip:
        source = gemini_tip["source"].title()
        safe_tip = escape(gemini_tip["tip"])
        st.markdown(
            f"""
            <div class="coach-panel llm-tip">
                <p class="coach-title">Gemini Coach</p>
                <p><strong>{source}:</strong> {safe_tip}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if coach_reasoning:
        source = coach_reasoning["source"].title()
        safe_message = escape(coach_reasoning["message"])
        st.markdown(
            f"""
            <div class="coach-panel llm-tip">
                <p class="coach-title">Live Coach Agent</p>
                <p><strong>{source} reasoning:</strong> {safe_message}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    render_gemini_coach_button(notes)
    with st.expander("Coach notebook", expanded=bool(notes["clue_notes"])):
        render_clue_board(notes["clue_notes"])


def build_current_game_memory(notes: dict | None = None) -> dict:
    coach_notes = notes if notes is not None else build_coach_notes(st.session_state.player_history)
    return build_game_memory(
        st.session_state.agent_state,
        st.session_state.player_history,
        coach_notes,
        st.session_state.game_phase,
    )


def maybe_generate_llm_coach_reasoning(notes: dict, game_memory: dict) -> None:
    api_key = get_setting("GOOGLE_API_KEY") or get_setting("GEMINI_API_KEY")
    if not api_key:
        return

    model_name = get_setting("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    agent_history_count = len(game_memory["agent"]["history"])
    human_history_count = len(game_memory["human"]["history"])
    coach_key = (
        f"{notes['attempts']}:{notes['suggested_guess']}:{agent_history_count}:"
        f"{human_history_count}:{game_memory['phase']}:{model_name}"
    )
    if st.session_state.get("llm_coach_key") == coach_key:
        return

    fallback = f"Try {notes['suggested_guess']}. {notes['tip']}"
    result = generate_gemini_agent_message(
        "coach",
        {"notes": notes, "game_memory": game_memory, "fallback": fallback},
        api_key=api_key,
        model_name=model_name,
    )
    st.session_state.llm_coach_reasoning = result
    st.session_state.llm_coach_key = coach_key
    record_llm_agent_message(
        "coach",
        result["source"],
        result["message"],
        {
            "attempts": notes["attempts"],
            "suggested_guess": notes["suggested_guess"],
            "previous_guesses": notes["previous_guesses"],
            "game_memory": game_memory,
        },
    )


def render_gemini_coach_button(notes: dict) -> None:
    api_key = get_setting("GOOGLE_API_KEY") or get_setting("GEMINI_API_KEY")
    model_name = get_setting("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)

    if not api_key:
        st.caption("Set GOOGLE_API_KEY or GEMINI_API_KEY to enable Gemini Coach.")
        return

    if st.button("Ask Gemini Coach", use_container_width=True):
        with st.spinner("Gemini Coach is reading the clue notebook..."):
            st.session_state.gemini_coach_tip = generate_gemini_coach_tip(
                notes,
                api_key=api_key,
                model_name=model_name,
                game_memory=build_current_game_memory(notes),
            )
        st.rerun()


def render_clue_board(clue_notes: list[dict]) -> None:
    clue_rows = "".join(
        f"""
        <div class="clue-row">
            <div class="clue-turn">Turn {item["turn"]}</div>
            <div class="clue-guess">{item["guess"]}</div>
            <div class="clue-response">{item["response"]}</div>
        </div>
        """
        for item in clue_notes
    )
    if not clue_rows:
        clue_rows = """
        <div class="clue-row">
            <div class="clue-turn">Notes</div>
            <div class="clue-guess">Empty</div>
            <div class="clue-response">Make your first guess</div>
        </div>
        """
    st.markdown(f'<div class="clue-board">{clue_rows}</div>', unsafe_allow_html=True)


def render_langsmith_panel() -> None:
    tracing = get_setting("LANGSMITH_TRACING").lower() == "true"
    project = get_setting("LANGSMITH_PROJECT", "bulls-and-cows-agent")
    gemini_enabled = bool(get_setting("GOOGLE_API_KEY") or get_setting("GEMINI_API_KEY"))

    st.subheader("LangSmith")
    st.caption("Each live turn is traced: LangGraph feedback, human guesses, and Gemini agent messages.")
    st.metric("Tracing", "Enabled" if tracing else "Not enabled")
    st.metric("Project", project)
    st.metric("Gemini Coach", "Enabled" if gemini_enabled else "No API key")
    st.markdown(
        "- Agent feedback calls run through LangGraph and trace nodes like `receive_feedback`, `filter_candidates`, and `choose_next_guess`.\n"
        "- Human guesses are logged as `human_guess_turn` with bulls/cows results.\n"
        "- Gemini messages are logged as `llm_agent_message` with role, source, and game context."
    )


def render_history(title: str, history: list[dict]) -> None:
    st.subheader(title)
    if not history:
        st.info("No turns yet.")
        return
    for item in reversed(history):
        st.markdown(
            f"""
            <div class="turn-card">
                <div class="tiny-label">Turn {item["turn"]}</div>
                <strong>Guess:</strong> {item["guess"]} &nbsp; | &nbsp;
                <strong>Bulls:</strong> {item["bulls"]} &nbsp; | &nbsp;
                <strong>Cows:</strong> {item["cows"]}
            </div>
            """,
            unsafe_allow_html=True,
        )


@st.dialog("Enter bulls and cows")
def render_agent_feedback_dialog() -> None:
    state = st.session_state.agent_state
    st.write(f"My guess is **{state['current_guess']}**.")
    st.write("For your secret number, how many bulls and cows did I get?")

    bulls = st.selectbox("Bulls", options=[0, 1, 2, 3], index=0, key="feedback_bulls")
    cows = st.selectbox(
        "Cows",
        options=list(range(0, 4 - int(bulls))),
        index=0,
        key=f"feedback_cows_for_{bulls}_bulls",
    )
    feedback_is_valid = is_valid_feedback(int(bulls), int(cows))
    if not feedback_is_valid:
        st.warning("Bulls and cows must be between 0 and 3, and cannot total more than 3.")
    submitted = st.button(
        "Submit feedback",
        disabled=not feedback_is_valid,
        use_container_width=True,
    )

    if submitted and feedback_is_valid:
        updated = run_traced_agent_feedback_turn(
            state,
            CandidateFeedback(int(bulls), int(cows)),
        )
        st.session_state.agent_state = updated
        st.session_state.gemini_coach_tip = None
        st.session_state.llm_opponent_message = None
        st.session_state.llm_opponent_key = None
        st.session_state.referee_help = None
        st.session_state.game_phase = next_phase_after_agent_feedback(updated["status"])
        st.rerun()
    elif submitted:
        st.warning("Invalid feedback was not submitted.")


@st.dialog("Bulls and cows result")
def render_human_result_dialog() -> None:
    feedback = st.session_state.human_feedback
    if feedback is None:
        st.write("No result yet.")
        return

    if feedback["won"]:
        st.success(f"You solved my number: {st.session_state.secret}.")
        button_label = "Start a new game"
    else:
        st.info(
            f"For **{feedback['guess']}**: {feedback['bulls']} bulls and "
            f"{feedback['cows']} cows."
        )
        button_label = "Continue to agent turn"

    if st.button(button_label, use_container_width=True):
        if feedback["won"]:
            reset_game()
        else:
            st.session_state.game_phase = next_phase_after_human_guess(False)
            st.session_state.human_feedback = None
        st.rerun()


def render_intro_screen() -> None:
    st.markdown('<div class="game-shell">', unsafe_allow_html=True)
    render_game_logo()
    render_hud("Ready", len(st.session_state.agent_state["candidates"]), 1)
    render_arena_header(
        "Ready",
        "Pick your secret number. Coach Agent will help you guess mine.",
    )
    render_rules_expander()
    st.markdown(
        """
        <div class="speech speech-agent">
            I go first. Then Coach helps you fight back.
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_coach_panel()
    render_countdown()
    if st.button("Start game", use_container_width=True):
        st.session_state.game_phase = start_game_phase()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_agent_turn() -> None:
    state = st.session_state.agent_state
    opponent_message = get_or_create_opponent_message(state)

    st.markdown('<div class="game-shell">', unsafe_allow_html=True)
    render_game_logo()
    render_hud(
        f"Agent {state['turn']}",
        len(state["candidates"]),
        len(st.session_state.player_history) + 1,
    )
    render_arena_header(
        f"Agent turn {state['turn']}",
        f"Opponent Agent has {len(state['candidates'])} possible numbers left.",
    )
    render_rules_expander()
    render_coach_panel()
    safe_opponent_message = escape(opponent_message["message"])
    opponent_source = opponent_message["source"].title()
    st.markdown(
        f"""
        <div class="speech speech-agent">
            <strong>{opponent_source} Opponent:</strong> {safe_opponent_message}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if state["current_guess"] is None:
        st.error("No valid candidate remains. The feedback history is contradictory.")
    else:
        st.markdown(
            f"""
            <div class="guess-card">
                <div class="tiny-label">Agent says</div>
                <div class="quest-banner">Match these tiles against your secret number.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_number_tiles(state["current_guess"])

    render_referee_helper(state)

    if st.button("Enter bulls and cows for my guess", use_container_width=True):
        render_agent_feedback_dialog()

    with st.expander("What the agent learned", expanded=False):
        st.write(state["reasoning"])
        render_history("Agent turns so far", state["history"])
    st.markdown("</div>", unsafe_allow_html=True)


def render_referee_helper(state: dict) -> None:
    if state.get("current_guess") is None:
        return

    with st.expander("Need help responding to the agent?", expanded=False):
        st.caption("Enter your secret number and ask Gemini what bulls/cows to submit.")
        with st.form("referee_helper_form"):
            secret = st.text_input(
                "Your secret number",
                max_chars=3,
                placeholder="427",
                type="password",
                help="Used to calculate the exact response to the agent's current guess.",
            )
            question = st.text_area(
                "Ask Gemini",
                value="How many bulls and cows should I respond with?",
                height=80,
            )
            submitted = st.form_submit_button("Ask referee helper")

        if submitted:
            normalized_secret = secret.strip()
            if not is_valid_secret(normalized_secret):
                st.session_state.referee_help = {
                    "source": "error",
                    "message": "Enter a valid 3-digit number with unique digits. First digit cannot be 0.",
                }
            else:
                feedback = score_guess(normalized_secret, state["current_guess"])
                api_key = get_setting("GOOGLE_API_KEY") or get_setting("GEMINI_API_KEY")
                result = generate_gemini_referee_help(
                    secret=normalized_secret,
                    agent_guess=state["current_guess"],
                    bulls=feedback.bulls,
                    cows=feedback.cows,
                    question=question.strip() or "How many bulls and cows should I respond with?",
                    api_key=api_key,
                    model_name=get_setting("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
                    game_memory=build_current_game_memory(),
                )
                result["bulls"] = feedback.bulls
                result["cows"] = feedback.cows
                result["agent_guess"] = state["current_guess"]
                st.session_state.referee_help = result

        referee_help = st.session_state.get("referee_help")
        if referee_help and referee_help.get("agent_guess", state["current_guess"]) == state["current_guess"]:
            source = referee_help["source"].title()
            safe_message = escape(referee_help["message"])
            bulls = referee_help.get("bulls")
            cows = referee_help.get("cows")
            if bulls is not None and cows is not None:
                st.success(f"Submit: {bulls} bulls, {cows} cows")
            st.markdown(
                f"""
                <div class="coach-panel llm-tip">
                    <p class="coach-title">Referee Helper</p>
                    <p><strong>{source}:</strong> {safe_message}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def get_or_create_opponent_message(state: dict) -> dict:
    api_key = get_setting("GOOGLE_API_KEY") or get_setting("GEMINI_API_KEY")
    guess = state.get("current_guess")
    model_name = get_setting("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    notes = build_coach_notes(st.session_state.player_history)
    game_memory = build_current_game_memory(notes)
    message_key = (
        f"{state.get('turn')}:{guess}:{len(state.get('candidates', []))}:"
        f"{len(game_memory['human']['history'])}:{len(game_memory['agent']['history'])}:"
        f"{game_memory['phase']}:{model_name}"
    )

    if st.session_state.get("llm_opponent_key") == message_key:
        return st.session_state.llm_opponent_message

    fallback = f"I am trying {guess}. Your secret has fewer places to hide now."
    result = generate_gemini_agent_message(
        "opponent",
        {
            "current_guess": guess,
            "turn": state.get("turn", 1),
            "candidate_count": len(state.get("candidates", [])),
            "reasoning": state.get("reasoning", ""),
            "game_memory": game_memory,
            "fallback": fallback,
        },
        api_key=api_key,
        model_name=model_name,
    )
    st.session_state.llm_opponent_message = result
    st.session_state.llm_opponent_key = message_key
    record_llm_agent_message(
        "opponent",
        result["source"],
        result["message"],
        {
            "turn": state.get("turn", 1),
            "guess": guess,
            "candidate_count": len(state.get("candidates", [])),
            "reasoning": state.get("reasoning", ""),
            "game_memory": game_memory,
        },
    )
    return result


def render_human_turn() -> None:
    st.markdown('<div class="game-shell">', unsafe_allow_html=True)
    render_game_logo()
    render_hud(
        f"You {len(st.session_state.player_history) + 1}",
        len(st.session_state.agent_state["candidates"]),
        len(st.session_state.player_history) + 1,
    )
    render_arena_header(
        f"Your turn {len(st.session_state.player_history) + 1}",
        "Read Coach Notes. Make one guess.",
    )
    render_rules_expander()
    render_coach_panel()
    st.markdown(
        """
        <div class="speech speech-human">
            Your move. Enter one guess.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("human_guess_form", clear_on_submit=True):
        guess = st.text_input("Your 3-digit guess", max_chars=3, placeholder="427")
        submitted = st.form_submit_button("Reveal my bulls and cows")

    if submitted:
        normalized = guess.strip()
        if not is_valid_secret(normalized):
            st.error("That is not a valid game number. Try something like 427.")
        else:
            feedback = score_guess(st.session_state.secret, normalized)
            won = feedback.bulls == 3
            st.session_state.player_history.append(
                {
                    "turn": len(st.session_state.player_history) + 1,
                    "guess": normalized,
                    "bulls": feedback.bulls,
                    "cows": feedback.cows,
                    "status": "won" if won else "playing",
                }
            )
            st.session_state.human_feedback = {
                "guess": normalized,
                "bulls": feedback.bulls,
                "cows": feedback.cows,
                "won": won,
            }
            record_human_guess_turn(
                normalized,
                feedback.bulls,
                feedback.cows,
                won,
                len(st.session_state.player_history),
            )
            st.session_state.gemini_coach_tip = None
            st.session_state.llm_coach_reasoning = None
            st.session_state.llm_coach_key = None
            st.session_state.game_phase = "human_result"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_agent_result() -> None:
    state = st.session_state.agent_state
    if state["status"] == "won":
        st.success(f"I solved your number: {state['current_guess']}.")
    else:
        st.error("The feedback does not match any valid 3-digit number.")
    st.write(state["reasoning"])
    render_history("Agent turns", state["history"])

    if st.button("Start a new game", use_container_width=True):
        reset_game()
        st.rerun()


def render_game_screen() -> None:
    phase = st.session_state.game_phase
    if phase == "intro":
        render_intro_screen()
    elif phase == "agent_turn":
        render_agent_turn()
    elif phase == "human_turn":
        render_human_turn()
    elif phase == "human_result":
        render_human_result_dialog()
        render_human_turn()
    elif phase == "agent_result":
        render_agent_result()


def main() -> None:
    st.set_page_config(page_title="Bulls and Cows Agent", page_icon="BC", layout="wide")
    apply_settings_to_environment()
    ensure_session()
    render_game_styles()

    render_game_screen()
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("Reset full game", use_container_width=True):
            reset_game()
            st.rerun()
    with col_b:
        st.caption("LangSmith is backstage for the demo, not part of the game board.")

    with st.expander("Backstage: LangSmith trace panel", expanded=False):
        render_langsmith_panel()


if __name__ == "__main__":
    main()
