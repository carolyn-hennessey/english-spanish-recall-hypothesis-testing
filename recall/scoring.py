import re
import unicodedata

ARTICLES = {"the", "a", "an", "el", "la", "los", "las", "un", "una"}


def normalize(text):
    """Case, accent and article insensitive, so typing speed isn't spent on diacritics."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    words = re.sub(r"[^\w\s-]", "", text.casefold()).split()
    if len(words) > 1 and words[0] in ARTICLES:
        words = words[1:]
    return " ".join(words)


def _edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def score(response, accepted_names):
    """Return (correct, near_miss). A near miss is a wrong answer one edit from a right one."""
    got = normalize(response)
    if not got:
        return False, False
    targets = [normalize(n) for n in accepted_names]
    if got in targets:
        return True, False
    return False, any(_edit_distance(got, t) <= 1 for t in targets)
