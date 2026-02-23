import streamlit as st
import time
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from card_generator import generate_all_trials, check_answer

# ──────────────────────────────────────────────────────────────────────────────
# Session state initialisation
# ──────────────────────────────────────────────────────────────────────────────

def _init_state():
    """Generate a fresh set of trials and reset all counters."""
    st.session_state.trials = generate_all_trials(
        trials_per_rule=10,
        transition_trials=3,
        # seed=42,  # uncomment for reproducible runs during development
    )
    st.session_state.trial = 0
    st.session_state.score = 0
    st.session_state.feedback = None
    st.session_state.show_feedback = False


if "trials" not in st.session_state:
    _init_state()

TRIALS = st.session_state.trials

# ──────────────────────────────────────────────────────────────────────────────
# End screen
# ──────────────────────────────────────────────────────────────────────────────

if st.session_state.trial >= len(TRIALS):
    st.title("Done 🎉")
    st.write(f"Final score: {st.session_state.score} / {len(TRIALS)}")
    if st.button("Restart"):
        _init_state()
        st.rerun()
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Current trial
# ──────────────────────────────────────────────────────────────────────────────

trial_data = TRIALS[st.session_state.trial]
rule_num = trial_data["rule"]
stage = 1 if rule_num <= 2 else 2

st.title(f"Trial {st.session_state.trial + 1}")
st.caption(f"Stage {stage} · Rule {rule_num} · Trial {trial_data['trial_index_in_rule'] + 1}/10")

# Main card
st.image(trial_data["main_path"], width=260)

# ──────────────────────────────────────────────────────────────────────────────
# Feedback display & advance logic
# ──────────────────────────────────────────────────────────────────────────────

if st.session_state.show_feedback:
    fb = st.session_state.feedback

    if fb == "correct":
        st.success("# ✅ Correct!", icon="✅")
    elif fb == "half_correct":
        st.warning("# 🟡 Close! One rule feature matches", icon="⚠️")
    else:
        st.error("# ❌ Incorrect", icon="❌")

    time.sleep(1.2)
    st.session_state.trial += 1
    st.session_state.feedback = None
    st.session_state.show_feedback = False
    st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# Option cards
# ──────────────────────────────────────────────────────────────────────────────

st.write("### Choose a card:")

cols = st.columns(4)
for i, col in enumerate(cols):
    with col:
        st.image(trial_data["option_paths"][i], width=120)
        if st.button("Select", key=f"opt_{st.session_state.trial}_{i}"):
            fb = check_answer(trial_data, i)
            if fb == "correct":
                st.session_state.score += 1
            st.session_state.feedback = fb
            st.session_state.show_feedback = True
            st.rerun()
