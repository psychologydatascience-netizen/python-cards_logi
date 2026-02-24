"""
card_generator.py
-----------------
Generates all trial data for the card-matching experiment.

Card representation:
    A card is a list of 4 ints, e.g. [2, 4, 4, 1].
    Position index 0-3 maps to symbol slots 1-4.
    Value 0 means the symbol is absent (used for 3-symbol cards at position 3).
    Values 1-4 are the four possible forms of each symbol.

Stage 1  (Rules 1-2):  3-symbol cards -> active_positions = [0, 1, 2]
Stage 2  (Rules 3-19): 4-symbol cards -> active_positions = [0, 1, 2, 3]

Option-card specs per rule
--------------------------
Rule 1:     correct=2rf  |  0-match, 1-match, 2-not-rule
Rule 2:     correct=2rf  |  1-match, 2-not-rule, 2-not-rule
Rule 3:     correct=2rf  |  0-match, 1-match, 2-not-rule
Rule 4:     correct=2rf  |  1-match, 1-match, 2-not-rule
Rule 5:     correct=2rf  |  1-match, 2-not-rule, 2-not-rule
Rules 6-19: correct=2rf  |  2-not-rule, 2-not-rule, 2-not-rule

"2rf"        = exactly the 2 rule-feature positions match, rest differ.
"2-not-rule" = 2 total matches, but NOT both rule-feature positions.

Transition: for the first TRANSITION_TRIALS trials of a new rule one wrong card
is replaced by a transition card matching the main on the previous rule's features.
"""

import random
from itertools import combinations

TOTAL_RULES      = 19
TRANSITION_TRIALS = 3


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def get_different_value(current):
    return random.choice([v for v in range(1, 5) if v != current])


def generate_random_card(active_positions):
    card = [0, 0, 0, 0]
    for p in active_positions:
        card[p] = random.randint(1, 4)
    return card


def card_to_code(card):
    return "".join(str(v) for v in card)


def count_matches(main, other, positions):
    return sum(1 for p in positions if main[p] == other[p])


# ---------------------------------------------------------------------------
# Core card-generation primitives
# ---------------------------------------------------------------------------

def generate_matching_card(main, active_positions, n_match,
                            must_match=None, must_differ=None):
    must_match  = set(must_match  or [])
    must_differ = set(must_differ or [])

    if must_match & must_differ:
        raise ValueError(f"must_match and must_differ overlap: {must_match & must_differ}")

    free    = [p for p in active_positions if p not in must_match and p not in must_differ]
    n_extra = n_match - len(must_match)

    if n_extra < 0 or n_extra > len(free):
        raise ValueError(
            f"Cannot achieve {n_match} matches with "
            f"must_match={must_match}, must_differ={must_differ}, free={free}"
        )

    card = [0, 0, 0, 0]
    for p in must_match:
        card[p] = main[p]
    for p in must_differ:
        card[p] = get_different_value(main[p])

    extra_match = set(random.sample(free, n_extra))
    for p in free:
        card[p] = main[p] if p in extra_match else get_different_value(main[p])

    return card


def generate_not_both_rule_match(main, active_positions, rule_features, n_match=2):
    """2 total matches where NOT both rule features are among them."""
    rule_features = list(rule_features)
    non_rule = [p for p in active_positions if p not in rule_features]

    max_rf = min(len(rule_features) - 1, n_match)
    min_rf = max(0, n_match - len(non_rule))
    n_rf   = random.randint(min_rf, max_rf)

    matched_rf   = set(random.sample(rule_features, n_rf))
    unmatched_rf = set(rule_features) - matched_rf

    return generate_matching_card(main, active_positions, n_match,
                                  must_match=matched_rf,
                                  must_differ=unmatched_rf)


# ---------------------------------------------------------------------------
# Per-rule option generation
# ---------------------------------------------------------------------------

def _build_correct(main, rf, non_rf, active_positions):
    """Correct card: exactly the 2 rule features match, all others differ."""
    return generate_matching_card(main, active_positions, 2,
                                  must_match=set(rf),
                                  must_differ=set(non_rf))


def _build_wrong_cards(main, rf, active_positions, rule_num):
    g   = generate_matching_card
    gnr = generate_not_both_rule_match

    if rule_num == 1:
        return [g(main, active_positions, 0),
                g(main, active_positions, 1),
                gnr(main, active_positions, rf, 2)]
    elif rule_num == 2:
        return [g(main, active_positions, 1),
                gnr(main, active_positions, rf, 2),
                gnr(main, active_positions, rf, 2)]
    elif rule_num == 3:
        return [g(main, active_positions, 0),
                g(main, active_positions, 1),
                gnr(main, active_positions, rf, 2)]
    elif rule_num == 4:
        return [g(main, active_positions, 1),
                g(main, active_positions, 1),
                gnr(main, active_positions, rf, 2)]
    elif rule_num == 5:
        return [g(main, active_positions, 1),
                gnr(main, active_positions, rf, 2),
                gnr(main, active_positions, rf, 2)]
    else:
        # Rules 6-19: all three wrong cards have 2 matches, not both rule features
        return [gnr(main, active_positions, rf, 2),
                gnr(main, active_positions, rf, 2),
                gnr(main, active_positions, rf, 2)]


# ---------------------------------------------------------------------------
# Single trial generator
# ---------------------------------------------------------------------------

def generate_trial(rule_num, rule_features, active_positions,
                   prev_rule_features=None, is_transition=False):
    rf     = list(rule_features)
    non_rf = [p for p in active_positions if p not in rf]

    main    = generate_random_card(active_positions)
    correct = _build_correct(main, rf, non_rf, active_positions)
    wrong   = _build_wrong_cards(main, rf, active_positions, rule_num)

    if is_transition and prev_rule_features:
        prf     = list(prev_rule_features)
        non_prf = [p for p in active_positions if p not in prf]
        wrong[-1] = generate_matching_card(main, active_positions, 2,
                                           must_match=set(prf),
                                           must_differ=set(non_prf))

    options = [correct] + wrong
    perm    = list(range(4))
    random.shuffle(perm)
    shuffled      = [options[i] for i in perm]
    correct_index = perm.index(0)

    return {
        "main":               main,
        "main_code":          card_to_code(main),
        "main_path":          f"cards/{card_to_code(main)}.png",
        "options":            shuffled,
        "option_codes":       [card_to_code(c) for c in shuffled],
        "option_paths":       [f"cards/{card_to_code(c)}.png" for c in shuffled],
        "correct":            correct_index,
        "rule":               rule_num,
        "rule_features":      rf,
        "prev_rule_features": list(prev_rule_features) if prev_rule_features else None,
        "active_positions":   active_positions,
        "is_transition":      is_transition,
    }


# ---------------------------------------------------------------------------
# Top-level: generate all trials
# ---------------------------------------------------------------------------

def generate_all_trials(trials_per_rule=10, transition_trials=TRANSITION_TRIALS, seed=None):
    """
    Generate trials for all 19 rules.
    Rules 1-2  -> Stage 1 (3-symbol)
    Rules 3-19 -> Stage 2 (4-symbol)
    The app stops at 60 counted trials; we generate the full buffer.
    """
    if seed is not None:
        random.seed(seed)

    active_3 = [0, 1, 2]
    active_4 = [0, 1, 2, 3]
    pairs_3  = list(combinations(active_3, 2))
    pairs_4  = list(combinations(active_4, 2))

    rule_features = {}
    for r in range(1, TOTAL_RULES + 1):
        pairs = pairs_3 if r <= 2 else pairs_4
        prev  = rule_features.get(r - 1)
        candidates = [p for p in pairs if p != prev] if (prev in pairs) else pairs
        rule_features[r] = random.choice(candidates)

    all_trials = []
    for rule_num in range(1, TOTAL_RULES + 1):
        active  = active_3 if rule_num <= 2 else active_4
        rf      = rule_features[rule_num]
        prev_rf = rule_features.get(rule_num - 1)

        for trial_i in range(trials_per_rule):
            is_trans = (prev_rf is not None) and (trial_i < transition_trials)
            trial = generate_trial(rule_num, rf, active,
                                   prev_rule_features=prev_rf,
                                   is_transition=is_trans)
            trial["trial_index_in_rule"] = trial_i
            all_trials.append(trial)

    return all_trials


# ---------------------------------------------------------------------------
# Answer checking
# ---------------------------------------------------------------------------

def check_answer(trial_data, selected_index):
    """Returns 'correct', 'half_correct', or 'incorrect'."""
    if selected_index == trial_data["correct"]:
        return "correct"
    main     = trial_data["main"]
    selected = trial_data["options"][selected_index]
    n = count_matches(main, selected, trial_data["rule_features"])
    return "half_correct" if n >= 1 else "incorrect"


def is_perseveration(trial_data, selected_index):
    """
    True when a wrong answer matches the main card on BOTH features of the
    *previous* rule — participant is perseverating on the old rule.
    Only meaningful when prev_rule_features is set.
    """
    prf = trial_data.get("prev_rule_features")
    if not prf:
        return False
    main     = trial_data["main"]
    selected = trial_data["options"][selected_index]
    return count_matches(main, selected, prf) == len(prf)