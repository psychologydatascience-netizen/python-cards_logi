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
    st.session_state.extreme_mistakes         = 0
    # ── Prev-answer context (for extreme-mistake detection) ──────────────────
    st.session_state.prev_answer_feedback     = None   # "correct"/"half_correct"/"incorrect"
    st.session_state.prev_matched_positions   = None   # frozenset of matched positions
    st.session_state.prev_answer_rule         = None   # rule number of that answer
    st.session_state.feedback                 = None
    st.session_state.show_feedback            = False
    st.session_state.rule_end_message         = False
    # ── Rule-trial limit (8 base, +1 per correct answer on last trial, max 10) ──
    st.session_state.rule_ends_at_index       = 7   # 0-based; trial 8 is the default last
    st.session_state.pending_rule_end         = False
    # ── Timing ──────────────────────────────────────────────────────────────
    st.session_state.trial_start_time         = time.time()
    st.session_state.test_start_time    = time.time()
    st.session_state.trial_times              = []   # list of (trial_number, seconds)


if "trials" not in st.session_state:
    _init_state()

TRIALS = st.session_state.trials


def _is_first_trial_of_rule(trial_data):
    return trial_data["trial_index_in_rule"] == 0


def _advance_to_next_rule():
    """Jump to the first trial of the next rule and always reset the streak."""
    current_rule = TRIALS[st.session_state.trial]["rule"]
    st.session_state.consecutive_correct    = 0
    st.session_state.rule_ends_at_index     = 7
    st.session_state.prev_answer_feedback   = None   # cross-rule context is cleared
    st.session_state.prev_matched_positions = None
    st.session_state.prev_answer_rule       = None
    for i, t in enumerate(TRIALS):
        if t["rule"] > current_rule:
            st.session_state.trial = i
            return
    st.session_state.trial = len(TRIALS)


def _get_matched_positions(main, selected, active_positions):
    """Return frozenset of positions where main and selected share the same value."""
    return frozenset(p for p in active_positions if main[p] == selected[p])


def _game_over():
    return (st.session_state.counted_trials >= MAX_COUNTED_TRIALS or
            st.session_state.trial >= len(TRIALS))


def _fmt(seconds):
    """Format seconds as mm:ss.t  (e.g. 01:24.3)"""
    m, s = divmod(seconds, 60)
    return f"{int(m):02d}:{s:04.1f}"


# ── End screen ──────────────────────────────────────────────────────────────
if _game_over():
    total_elapsed = time.time() - st.session_state.test_start_time

    st.title("Done!")
    st.write(f"**Total trials:** {st.session_state.counted_trials} / {MAX_COUNTED_TRIALS}")
    st.write(f"**Correct answers:** {st.session_state.score}")
    st.write(f"**Rules found (3-in-a-row):** {st.session_state.rules_found}")
    st.write(f"**Perseveration errors:** {st.session_state.perseveration_errors}")
    st.write(f"**Non-perseveration errors:** {st.session_state.non_perseveration_errors}")
    st.write(f"**Extreme mistakes:** {st.session_state.extreme_mistakes}")

    # ── Timing summary ───────────────────────────────────────────────────────
    st.divider()
    st.subheader(f"⏱ Total test time: {_fmt(total_elapsed)}")

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
#with timer_col:
#    st.metric("⏱ This trial", _fmt(elapsed_this_trial))
with title_col:
    st.title(f"Trial {st.session_state.counted_trials + 1} / {MAX_COUNTED_TRIALS}")

st.caption(
    f"Stage {stage} · Rule {rule_num} · "
    f"Trial {trial_data['trial_index_in_rule'] + 1}/(8+2) · "
    f"Counted: {st.session_state.counted_trials}/{MAX_COUNTED_TRIALS}"
)

st.image(trial_data["main_path"], width=260)

# Rule-end message (10th trial exhausted)
if st.session_state.rule_end_message:
    st.info("### השלב הסתיים, עוברים לשלב הבא")
    time.sleep(2)
    st.session_state.rule_end_message = False
    st.session_state.pending_rule_end = False
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
    is_last_trial = st.session_state.pending_rule_end

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
                # First trial of a new rule: clear prev context (cross-rule doesn't count)
                st.session_state.prev_answer_feedback   = None
                st.session_state.prev_matched_positions = None
                st.session_state.prev_answer_rule       = None
            else:
                active   = trial_data["active_positions"]
                main_c   = trial_data["main"]
                selected_card = trial_data["options"][i]
                cur_matched  = _get_matched_positions(main_c, selected_card, active)

                # ── Extreme mistake detection ────────────────────────────────
                prev_fb   = st.session_state.prev_answer_feedback
                prev_pos  = st.session_state.prev_matched_positions
                prev_rule = st.session_state.prev_answer_rule
                same_rule = (prev_rule == rule_num)

                is_extreme = False

                if fb != "correct":
                    # Case 1: perseveration (also counted in perseveration_errors below)
                    if is_perseveration(trial_data, i):
                        is_extreme = True

                    # Cases 2 & 3: only within the same rule
                    elif same_rule and prev_fb == "half_correct" and prev_pos is not None:
                        complementary = frozenset(active) - prev_pos
                        # Case 2: chose the exact same matching pair again
                        if cur_matched == prev_pos:
                            is_extreme = True
                        # Case 3: chose the complementary pair
                        elif cur_matched == complementary:
                            is_extreme = True

                    # Case 4: previous was fully wrong → this answer is not fully correct
                    elif same_rule and prev_fb == "incorrect":
                        is_extreme = True

                if is_extreme:
                    st.session_state.extreme_mistakes += 1

                # ── Standard scoring ─────────────────────────────────────────
                if fb == "correct":
                    st.session_state.score += 1
                    st.session_state.consecutive_correct += 1
                else:
                    st.session_state.consecutive_correct = 0
                    if is_perseveration(trial_data, i):
                        st.session_state.perseveration_errors += 1
                    else:
                        st.session_state.non_perseveration_errors += 1

                # ── Update prev-answer context for next trial ─────────────────
                st.session_state.prev_answer_feedback   = fb
                st.session_state.prev_matched_positions = cur_matched
                st.session_state.prev_answer_rule       = rule_num

            if st.session_state.consecutive_correct >= 3:
                st.session_state.rules_found += 1
                _advance_to_next_rule()
                st.session_state.pending_rule_end = False
            else:
                # Check whether this was the last allowed trial for this rule
                on_last = trial_data["trial_index_in_rule"] == st.session_state.rule_ends_at_index
                if on_last:
                    # Correct on last trial and still have bonus budget → extend by 1
                    if fb == "correct" and st.session_state.rule_ends_at_index < 9:
                        st.session_state.rule_ends_at_index += 1
                        st.session_state.pending_rule_end = False
                    else:
                        # Wrong answer on last trial, OR budget exhausted → end rule
                        st.session_state.pending_rule_end = True
                else:
                    st.session_state.pending_rule_end = False

            st.session_state.feedback      = fb
            st.session_state.show_feedback = True
            st.rerun()