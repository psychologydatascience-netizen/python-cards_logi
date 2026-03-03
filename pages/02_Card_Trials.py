import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import time
from card_generator import generate_all_trials, check_answer, is_perseveration

MAX_COUNTED_TRIALS = 40


def _init_state():
    st.session_state.trials                   = generate_all_trials(trials_per_rule=10, transition_trials=3)
    st.session_state.trial                    = 0
    st.session_state.counted_trials           = 0
    st.session_state.score                    = 0
    st.session_state.consecutive_correct      = 0
    st.session_state.rules_found              = 0
    st.session_state.perseveration_errors     = 0
    st.session_state.non_perseveration_errors = 0
    st.session_state.feedback                 = None
    st.session_state.show_feedback            = False
    st.session_state.rule_end_message         = False
    # ── Timing ──────────────────────────────────────────────────────────────
    st.session_state.trial_start_time         = time.time()
    st.session_state.experiment_start_time    = time.time()
    st.session_state.trial_times              = []   # list of (trial_number, seconds)


if "trials" not in st.session_state:
    _init_state()

TRIALS = st.session_state.trials


def _is_first_trial_of_rule(trial_data):
    return trial_data["trial_index_in_rule"] == 0


def _advance_to_next_rule():
    """Jump to the first trial of the next rule and always reset the streak."""
    current_rule = TRIALS[st.session_state.trial]["rule"]
    st.session_state.consecutive_correct = 0
    for i, t in enumerate(TRIALS):
        if t["rule"] > current_rule:
            st.session_state.trial = i
            return
    st.session_state.trial = len(TRIALS)


def _game_over():
    return (st.session_state.counted_trials >= MAX_COUNTED_TRIALS or
            st.session_state.trial >= len(TRIALS))


def _fmt(seconds):
    """Format seconds as mm:ss.t  (e.g. 01:24.3)"""
    m, s = divmod(seconds, 60)
    return f"{int(m):02d}:{s:04.1f}"


# ── End screen ──────────────────────────────────────────────────────────────
if _game_over():
    total_elapsed = time.time() - st.session_state.experiment_start_time

    st.title("Done!")
    st.write(f"**Total trials:** {st.session_state.counted_trials} / {MAX_COUNTED_TRIALS}")
    st.write(f"**Correct answers:** {st.session_state.score}")
    st.write(f"**Rules found (3-in-a-row):** {st.session_state.rules_found}")
    st.write(f"**Perseveration errors:** {st.session_state.perseveration_errors}")
    st.write(f"**Non-perseveration errors:** {st.session_state.non_perseveration_errors}")

    # ── Timing summary ───────────────────────────────────────────────────────
    st.divider()
    st.subheader(f"⏱ Total experiment time: {_fmt(total_elapsed)}")

    trial_times = st.session_state.trial_times
    if trial_times:
        avg = sum(t for _, t in trial_times) / len(trial_times)
        slowest_num, slowest_t = max(trial_times, key=lambda x: x[1])
        fastest_num, fastest_t = min(trial_times, key=lambda x: x[1])

        col1, col2, col3 = st.columns(3)
        col1.metric("Average per trial", _fmt(avg))
        col2.metric(f"Slowest (trial {slowest_num})", _fmt(slowest_t))
        col3.metric(f"Fastest (trial {fastest_num})", _fmt(fastest_t))

        st.divider()
        st.write("**Per-trial breakdown:**")

        header = "| Trial | Time |\n|-------|------|\n"
        body   = "\n".join(f"| {n} | {_fmt(t)} |" for n, t in trial_times)
        st.markdown(header + body)

    st.divider()
    if st.button("Restart"):
        _init_state()
        st.rerun()
    st.stop()


trial_data    = TRIALS[st.session_state.trial]
rule_num      = trial_data["rule"]
stage         = 1 if rule_num <= 2 else 2
first_of_rule = _is_first_trial_of_rule(trial_data)

# ── Live timer display ───────────────────────────────────────────────────────
elapsed_this_trial = time.time() - st.session_state.trial_start_time
timer_col, title_col = st.columns([1, 4])
with timer_col:
    st.metric("⏱ This trial", _fmt(elapsed_this_trial))
with title_col:
    st.title(f"Trial {st.session_state.counted_trials + 1} / {MAX_COUNTED_TRIALS}")

st.caption(
    f"Stage {stage} · Rule {rule_num} · "
    f"Trial {trial_data['trial_index_in_rule'] + 1}/10 · "
    f"Counted: {st.session_state.counted_trials}/{MAX_COUNTED_TRIALS}"
)

st.image(trial_data["main_path"], width=260)

# Rule-end message (10th trial exhausted)
if st.session_state.rule_end_message:
    st.info("### השלב הסתיים, עוברים לשלב הבא")
    time.sleep(2)
    st.session_state.rule_end_message = False
    _advance_to_next_rule()
    st.session_state.trial_start_time = time.time()   # reset timer for new trial
    st.rerun()

# Feedback display + advance
if st.session_state.show_feedback:
    fb = st.session_state.feedback
    if fb == "correct":
        st.success("# Correct!", icon="✅")
    elif fb == "half_correct":
        st.warning("# Close! One rule feature matches", icon="⚠️")
    else:
        st.error("# Incorrect", icon="❌")

    time.sleep(1.2)
    st.session_state.show_feedback = False
    st.session_state.feedback = None

    streak        = st.session_state.consecutive_correct
    is_last_trial = trial_data["trial_index_in_rule"] == 9

    if streak >= 3:
        st.rerun()
    elif is_last_trial:
        st.session_state.rule_end_message = True
        st.session_state.trial += 1
        st.rerun()
    else:
        st.session_state.trial += 1
        st.rerun()

# Option cards
st.write("### Choose a card:")
cols = st.columns(4)
for i, col in enumerate(cols):
    with col:
        st.image(trial_data["option_paths"][i], width=120)
        if st.button("Select", key=f"opt_{st.session_state.trial}_{i}"):
            # ── Record trial time ────────────────────────────────────────────
            elapsed = time.time() - st.session_state.trial_start_time
            trial_number = st.session_state.counted_trials + 1
            st.session_state.trial_times.append((trial_number, elapsed))
            st.session_state.trial_start_time = time.time()   # reset for next trial

            fb = check_answer(trial_data, i)

            st.session_state.counted_trials += 1

            if first_of_rule:
                st.session_state.consecutive_correct = 0
            else:
                if fb == "correct":
                    st.session_state.score += 1
                    st.session_state.consecutive_correct += 1
                else:
                    st.session_state.consecutive_correct = 0
                    if is_perseveration(trial_data, i):
                        st.session_state.perseveration_errors += 1
                    else:
                        st.session_state.non_perseveration_errors += 1

            if st.session_state.consecutive_correct >= 3:
                st.session_state.rules_found += 1
                _advance_to_next_rule()

            st.session_state.feedback      = fb
            st.session_state.show_feedback = True
            st.rerun()