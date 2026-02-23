"""
card_generator.py
-----------------
Generates all trial data for the card-matching experiment.

Card representation:
    A card is a list of 4 ints, e.g. [2, 4, 4, 1].
    Position index 0-3 maps to symbol slots 1-4.
    Value 0 means the symbol is absent (used for 3-symbol cards at position 3).
    Values 1-4 are the four possible forms of each symbol.

Stage 1  (Rules 1-2): 3-symbol cards  → active_positions = [0, 1, 2]
Stage 2  (Rules 3-6): 4-symbol cards  → active_positions = [0, 1, 2, 3]

"Rule features" = the 2 position indices that define the rule.
"Correct" card must share those 2 values with the main card.
"Wrong" cards have various partial-match patterns (see each rule below).

Transition: for the first TRANSITION_TRIALS trials of a new rule, one wrong card
is replaced by a "transition card" that matches the main on the *previous* rule's
2 feature positions (so participants experience the old rule ceasing to work).
"""

import random
from itertools import combinations


# ──────────────────────────────────────────────────────────────────────────────
# Low-level helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_different_value(current: int) -> int:
    """Return a random value 1-4 that differs from *current*."""
    return random.choice([v for v in range(1, 5) if v != current])


def generate_random_card(active_positions: list) -> list:
    """Generate a card with random values (1-4) at active positions, 0 elsewhere."""
    card = [0, 0, 0, 0]
    for p in active_positions:
        card[p] = random.randint(1, 4)
    return card


def card_to_code(card: list) -> str:
    """Convert [2,4,4,1] → '2441'."""
    return "".join(str(v) for v in card)


def count_rule_matches(main: list, other: list, rule_features: list) -> int:
    """Count how many rule-feature positions match between main and other."""
    return sum(1 for p in rule_features if main[p] == other[p])


# ──────────────────────────────────────────────────────────────────────────────
# Core card-generation primitive
# ──────────────────────────────────────────────────────────────────────────────

def generate_matching_card(
    main: list,
    active_positions: list,
    n_match: int,
    must_match: set = None,
    must_differ: set = None,
) -> list:
    """
    Create a card that matches *main* on **exactly** n_match active positions.

    Parameters
    ----------
    main            : reference card (list of 4 ints)
    active_positions: positions to consider (non-zero positions)
    n_match         : exact number of matches required
    must_match      : positions that MUST be among the n_match matching ones
    must_differ     : positions that MUST differ from main

    Returns
    -------
    list of 4 ints
    """
    must_match = set(must_match or [])
    must_differ = set(must_differ or [])

    if must_match & must_differ:
        raise ValueError(f"must_match and must_differ overlap: {must_match & must_differ}")

    free = [p for p in active_positions if p not in must_match and p not in must_differ]
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


def generate_not_both_rule_match(
    main: list,
    active_positions: list,
    rule_features: list,
    n_match: int = 2,
) -> list:
    """
    Generate a card with *n_match* total matches, where NOT all rule features match.

    "Not both rule features" means at most len(rule_features)-1 of them are in
    the matching set, so the participant cannot use the rule features alone as a
    reason to select this card.
    """
    rule_features = list(rule_features)
    non_rule = [p for p in active_positions if p not in rule_features]

    max_rf = min(len(rule_features) - 1, n_match)          # at most (all-1) rule features
    min_rf = max(0, n_match - len(non_rule))                # forced if non_rule not enough
    n_rf = random.randint(min_rf, max_rf)

    matched_rf = set(random.sample(rule_features, n_rf))
    unmatched_rf = set(rule_features) - matched_rf

    return generate_matching_card(
        main, active_positions, n_match,
        must_match=matched_rf,
        must_differ=unmatched_rf,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Per-rule option generation
# ──────────────────────────────────────────────────────────────────────────────

def _build_correct(main, rf, non_rf, active_positions, rule_num):
    """Build the correct card for a given rule."""
    if rule_num in (5, 6):
        # 2 or 3 total matches; both rule features must be included
        n_extra = random.randint(0, min(1, len(non_rf)))   # 0 or 1 bonus match
        return generate_matching_card(
            main, active_positions, 2 + n_extra,
            must_match=set(rf),
        )
    else:
        # Exactly 2 matches = exactly the 2 rule features
        return generate_matching_card(
            main, active_positions, 2,
            must_match=set(rf),
            must_differ=set(non_rf),
        )


def _build_wrong_cards(main, rf, active_positions, rule_num):
    """
    Build the 3 wrong cards according to the rule specification.

    Rule 1 (3-sym):  0-match, 1-match, 2-match-not-rule
    Rule 2 (3-sym):  1-match, 2-not-rule, 2-not-rule
    Rule 3 (4-sym):  0-match, 1-match, 2-not-rule
    Rule 4 (4-sym):  1-match, 1-match, 2-not-rule
    Rule 5 (4-sym):  1-match, 2-not-rule, 2-not-rule
    Rule 6 (4-sym):  2-or-3-not-rule, 2-not-rule, 2-not-rule
    """
    g = generate_matching_card
    gnr = generate_not_both_rule_match

    if rule_num == 1:
        return [
            g(main, active_positions, 0),
            g(main, active_positions, 1),
            gnr(main, active_positions, rf, 2),
        ]
    elif rule_num == 2:
        return [
            g(main, active_positions, 1),
            gnr(main, active_positions, rf, 2),
            gnr(main, active_positions, rf, 2),
        ]
    elif rule_num == 3:
        return [
            g(main, active_positions, 0),
            g(main, active_positions, 1),
            gnr(main, active_positions, rf, 2),
        ]
    elif rule_num == 4:
        return [
            g(main, active_positions, 1),
            g(main, active_positions, 1),
            gnr(main, active_positions, rf, 2),
        ]
    elif rule_num == 5:
        return [
            g(main, active_positions, 1),
            gnr(main, active_positions, rf, 2),
            gnr(main, active_positions, rf, 2),
        ]
    elif rule_num == 6:
        n = random.choice([2, 3])
        return [
            gnr(main, active_positions, rf, n),
            gnr(main, active_positions, rf, 2),
            gnr(main, active_positions, rf, 2),
        ]
    else:
        raise ValueError(f"Unknown rule number: {rule_num}")


# ──────────────────────────────────────────────────────────────────────────────
# Single trial generator
# ──────────────────────────────────────────────────────────────────────────────

def generate_trial(
    rule_num: int,
    rule_features: tuple,
    active_positions: list,
    is_transition: bool = False,
    prev_rule_features: tuple = None,
) -> dict:
    """
    Generate one trial for the given rule.

    Parameters
    ----------
    rule_num          : 1–6
    rule_features     : tuple of 2 position indices that define this rule
    active_positions  : list of active position indices for this stage
    is_transition     : if True, replace one wrong card with a transition card
    prev_rule_features: required when is_transition=True; the previous rule's features

    Returns
    -------
    dict with keys:
        main, main_code, main_path,
        options (list of 4 cards), option_codes, option_paths,
        correct (index of correct card in options),
        rule, rule_features, active_positions, is_transition
    """
    rf = list(rule_features)
    non_rf = [p for p in active_positions if p not in rf]

    # Generate main card
    main = generate_random_card(active_positions)

    # Build option cards
    correct = _build_correct(main, rf, non_rf, active_positions, rule_num)
    wrong = _build_wrong_cards(main, rf, active_positions, rule_num)

    # ── Transition card ──────────────────────────────────────────────────────
    # Replace the last wrong card with one matching the *previous* rule features.
    # This card naturally fits the "2 matches, not both current-rule features"
    # slot because the previous rule's features differ from the current ones.
    if is_transition and prev_rule_features:
        prf = list(prev_rule_features)
        non_prf = [p for p in active_positions if p not in prf]
        transition = generate_matching_card(
            main, active_positions, 2,
            must_match=set(prf),
            must_differ=set(non_prf),
        )
        wrong[-1] = transition

    # ── Shuffle options ──────────────────────────────────────────────────────
    options = [correct] + wrong          # correct is always index 0 before shuffle
    perm = list(range(4))
    random.shuffle(perm)
    shuffled = [options[i] for i in perm]
    correct_index = perm.index(0)        # where did the correct card land?

    return {
        "main": main,
        "main_code": card_to_code(main),
        "main_path": f"cards/{card_to_code(main)}.png",
        "options": shuffled,
        "option_codes": [card_to_code(c) for c in shuffled],
        "option_paths": [f"cards/{card_to_code(c)}.png" for c in shuffled],
        "correct": correct_index,
        "rule": rule_num,
        "rule_features": rf,
        "active_positions": active_positions,
        "is_transition": is_transition,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Top-level: generate all trials
# ──────────────────────────────────────────────────────────────────────────────

def generate_all_trials(
    trials_per_rule: int = 10,
    transition_trials: int = 3,
    seed: int = None,
) -> list:
    """
    Generate all trials for the full 6-rule experiment.

    Parameters
    ----------
    trials_per_rule  : how many trials per rule (default 10)
    transition_trials: how many of the *first* trials in a new rule include
                       a transition card from the previous rule (default 3)
    seed             : optional random seed for reproducibility

    Returns
    -------
    Flat list of trial dicts, ordered rule 1 → rule 6.
    """
    if seed is not None:
        random.seed(seed)

    active_3 = [0, 1, 2]       # Stage 1 (3-symbol cards)
    active_4 = [0, 1, 2, 3]    # Stage 2 (4-symbol cards)

    pairs_3 = list(combinations(active_3, 2))   # 3 possible pairs
    pairs_4 = list(combinations(active_4, 2))   # 6 possible pairs

    # ── Assign rule features ─────────────────────────────────────────────────
    # Ensure consecutive rules within a stage use different feature pairs.
    rule_features = {}
    for r in range(1, 7):
        pairs = pairs_3 if r <= 2 else pairs_4
        prev = rule_features.get(r - 1)
        # Cross-stage boundary (rule 3): prev is from pairs_3 but we're now in
        # pairs_4 — any pairs_4 choice is inherently different.
        candidates = [p for p in pairs if p != prev] if (prev in pairs) else pairs
        rule_features[r] = random.choice(candidates)

    # ── Rule schedule ────────────────────────────────────────────────────────
    # (rule_num, active_positions, previous_rule_num or None)
    schedule = [
        (1, active_3, None),
        (2, active_3, 1),
        (3, active_4, 2),
        (4, active_4, 3),
        (5, active_4, 4),
        (6, active_4, 5),
    ]

    all_trials = []

    for rule_num, active, prev_rule_num in schedule:
        rf = rule_features[rule_num]
        prf = rule_features[prev_rule_num] if prev_rule_num else None

        for trial_i in range(trials_per_rule):
            is_trans = prf is not None and trial_i < transition_trials

            trial = generate_trial(
                rule_num, rf, active,
                is_transition=is_trans,
                prev_rule_features=prf,
            )
            trial["trial_index_in_rule"] = trial_i
            all_trials.append(trial)

    return all_trials


# ──────────────────────────────────────────────────────────────────────────────
# Answer checking (used by app.py)
# ──────────────────────────────────────────────────────────────────────────────

def check_answer(trial_data: dict, selected_index: int) -> str:
    """
    Evaluate the participant's selection.

    Returns
    -------
    "correct"      – selected the card that matches on both rule features
    "half_correct" – selected a card that matches on exactly 1 rule feature
    "incorrect"    – no rule features match
    """
    if selected_index == trial_data["correct"]:
        return "correct"

    main = trial_data["main"]
    selected = trial_data["options"][selected_index]
    rf = trial_data["rule_features"]

    rule_matches = count_rule_matches(main, selected, rf)

    return "half_correct" if rule_matches >= 1 else "incorrect"
