import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import time
from card_generator import generate_all_trials, check_answer

# ──────────────────────────────────────────────────────────────────────────────
# Session state initialisation
# ──────────────────────────────────────────────────────────────────────────────

def _init_state():
    st.session_state.trials = generate_all_trials(
        trials_per_rule=10,
        transition_trials=3,
    )
    st.session_state.trial = 0
    st.session_state.score = 0
    st.session_state.feedback = None
    st.session_state.show_feedback = False
    st.session_state.consecutive_correct = 0
    st.session_state.rule_end_message = False  # True when we need to show "rule ended" msg


if "trials" not in st.session_state:
    _init_state()

TRIALS = st.session_state.trials


def _advance_to_next_rule():
    """Jump the trial index to the first trial of the next rule (or end)."""
    current_rule = TRIALS[st.session_state.trial]["rule"]
    # Find first trial whose rule number is greater
    for i, t in enumerate(TRIALS):
        if t["rule"] > current_rule:
            st.session_state.trial = i
            return
    # No next rule → experiment is over
    st.session_state.trial = len(TRIALS)


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
# Rule-end message display (10th trial reached)
# ──────────────────────────────────────────────────────────────────────────────

if st.session_state.rule_end_message:
    st.info("### השלב הסתיים, עוברים לשלב הבא")
    time.sleep(2)
    st.session_state.rule_end_message = False
    _advance_to_next_rule()
    st.session_state.consecutive_correct = 0
    st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# Answer feedback display & advance logic
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
    st.session_state.show_feedback = False
    st.session_state.feedback = None

    # ── Decide what happens next ────────────────────────────────────────────
    is_last_trial_in_rule = trial_data["trial_index_in_rule"] == 9
    streak = st.session_state.consecutive_correct

    if streak >= 3:
        # Silent rule advance — already handled in the button logic below;
        # we land here after the feedback sleep, just rerun to show new trial.
        st.session_state.consecutive_correct = 0
        st.rerun()
    elif is_last_trial_in_rule:
        # Show the rule-end message on next render
        st.session_state.rule_end_message = True
        st.session_state.trial += 1  # advance past this trial so the message fires once
        st.rerun()
    else:
        st.session_state.trial += 1
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
                st.session_state.consecutive_correct += 1
            else:
                st.session_state.consecutive_correct = 0  # reset streak on any non-correct

            # If streak just hit 3 — advance to next rule immediately after feedback
            if st.session_state.consecutive_correct >= 3:
                _advance_to_next_rule()

            st.session_state.feedback = fb
            st.session_state.show_feedback = True
            st.rerun()
