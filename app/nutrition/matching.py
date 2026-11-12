"""Query normalization and food-name relevance ranking.

Providers return many candidate foods for a search; these helpers pick
the candidate whose name actually matches what the user typed, so a
search for "eggs" selects plain eggs instead of "egg custard" just
because the latter happens to contain the word "egg".
"""

import re
from difflib import SequenceMatcher


# Words that describe the state, preparation or labelling of the SAME
# food (e.g. "Egg, whole, raw, fresh" or "Eggs, Grade A, Large"). They
# never turn a food into a different dish, so a candidate is not
# penalized for containing them, and a query token from this set that
# the candidate lacks ("boiled" in "boiled eggs" vs "Egg, raw") only
# counts as a small miss, not a different food.
NEUTRAL_DESCRIPTORS = frozenset({
    "a", "aa", "all", "added", "and", "average", "baked", "boiled",
    "boneless", "braised", "brown", "canned", "commercial", "cooked",
    "dried", "dry", "enriched", "fresh", "fried", "frozen", "grade",
    "grain", "grilled", "hard", "in", "large", "lean", "long",
    "medium", "natural", "of", "only", "or", "organic", "plain",
    "poached", "raw", "regular", "roasted", "round", "salted",
    "scrambled", "short", "skin", "skinless", "small", "soft",
    "steamed", "stewed", "sweetened", "the", "uncooked", "unenriched",
    "unsalted", "unsweetened", "variety", "white", "whole", "with",
    "without", "year",
})

# Minimum score a candidate must reach before a provider may return it.
# Below this the candidate is considered unrelated to the query, and
# the search falls through to the next provider instead of showing an
# irrelevant food.
MINIMUM_SCORE = 0.55

# Weight of a query token that is only a preparation/descriptor word.
_DESCRIPTOR_WEIGHT = 0.3

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def normalize_query(text):
    """Trim and collapse whitespace; case is handled during tokenizing."""
    if not text:
        return ""

    return re.sub(r"\s+", " ", str(text)).strip()


def singularize(token):
    """Reduce simple English plurals so "eggs" matches "egg"."""
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"

    if token.endswith("oes") and len(token) > 4:
        return token[:-2]

    if len(token) > 4 and token.endswith(("ses", "xes", "zes", "ches", "shes")):
        return token[:-2]

    if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
        return token[:-1]

    return token


def tokenize(text):
    return {
        singularize(token)
        for token in _TOKEN_PATTERN.findall(str(text).lower())
    }


def _tokens_match(query_token, candidate_token):
    if query_token == candidate_token:
        return True

    # Catch close spelling variants such as yoghurt/yogurt.
    if (
        len(query_token) > 3
        and len(candidate_token) > 3
        and SequenceMatcher(None, query_token, candidate_token).ratio() >= 0.85
    ):
        return True

    return False


def score_candidate(query, candidate_name):
    """Relevance of ``candidate_name`` for ``query`` (roughly 0..1).

    - Coverage: how much of the query appears in the candidate. A real
      food word missing from the candidate ("biryani" in "chicken
      biryani" vs plain "Chicken") costs far more than a missing
      preparation word ("boiled" in "boiled eggs" vs "Egg, raw").
    - Extras: candidate words the user never asked for. Descriptor
      words ("raw", "whole", "grade") are free; other words signal a
      different dish ("custard", "salad") and are penalized.
    - A small similarity bonus breaks ties between close names.
    """
    query_tokens = tokenize(query)
    ordered_candidate_tokens = [
        singularize(token)
        for token in _TOKEN_PATTERN.findall(str(candidate_name).lower())
    ]
    candidate_tokens = set(ordered_candidate_tokens)

    if not query_tokens or not candidate_tokens:
        return 0.0

    matched_candidate_tokens = set()
    matched_weight = 0.0
    total_weight = 0.0
    missed_food_word = False

    for query_token in query_tokens:
        weight = (
            _DESCRIPTOR_WEIGHT
            if query_token in NEUTRAL_DESCRIPTORS
            else 1.0
        )
        total_weight += weight

        for candidate_token in candidate_tokens:
            if _tokens_match(query_token, candidate_token):
                matched_candidate_tokens.add(candidate_token)
                matched_weight += weight
                break
        else:
            if weight == 1.0:
                missed_food_word = True

    coverage = matched_weight / total_weight if total_weight else 0.0

    # Superlinear: missing a real food word ("biryani" in "chicken
    # biryani") must push plain "Chicken" well below MINIMUM_SCORE, so
    # a prepared dish is never silently answered with one ingredient.
    coverage = coverage ** 1.5

    def is_significant_extra(token):
        if token in NEUTRAL_DESCRIPTORS:
            return False

        # Bare numbers are quantities ("3.25% milkfat"), not foods.
        if token.isdigit():
            return False

        # Compounds of a query word ("milkfat" for "milk") stay in the
        # same food family and are not a different dish.
        return not any(
            len(query_token) >= 4
            and (
                token.startswith(query_token)
                or token.endswith(query_token)
            )
            for query_token in query_tokens
        )

    extras = candidate_tokens - matched_candidate_tokens
    significant_extras = [
        token for token in extras
        if is_significant_extra(token)
    ]
    extra_penalty = min(0.15 * len(significant_extras), 0.6)

    similarity = SequenceMatcher(
        None,
        " ".join(sorted(query_tokens)),
        " ".join(sorted(candidate_tokens))
    ).ratio()

    # Provider names usually lead with the base food ("Rice, white,
    # long-grain" vs "Fried rice"), so when every real food word in the
    # query matched, reward candidates whose name starts with one.
    prefix_bonus = 0.0

    if not missed_food_word and ordered_candidate_tokens:
        first_token = ordered_candidate_tokens[0]

        if any(
            _tokens_match(query_token, first_token)
            for query_token in query_tokens
        ):
            prefix_bonus = 0.15

    return coverage - extra_penalty + (0.1 * similarity) + prefix_bonus


def best_match(query, candidates, get_name, get_bonus=None,
               minimum_score=MINIMUM_SCORE):
    """Most relevant candidate for ``query``, or None when nothing fits.

    ``get_name`` extracts the display name from a candidate and
    ``get_bonus`` may add a provider-specific score bonus (e.g. USDA
    generic data types). Ties keep the provider's own ordering.
    """
    best_candidate = None
    best_score = minimum_score

    for candidate in candidates:
        name = get_name(candidate)

        if not name:
            continue

        score = score_candidate(query, name)

        if get_bonus is not None:
            score += get_bonus(candidate)

        if score > best_score:
            best_candidate = candidate
            best_score = score

    return best_candidate
