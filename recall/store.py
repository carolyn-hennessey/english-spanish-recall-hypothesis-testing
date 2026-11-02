import csv
import math
from collections import defaultdict
from statistics import mean

from . import config
from .vocab import CONCEPTS, LANGUAGES, accepted, concept_id
from .scoring import score

TRIAL_FIELDS = [
    "sample_id", "session_id", "timestamp", "block_position", "trial_in_block",
    "language", "concept_id", "emoji", "accepted", "response", "correct", "near_miss",
    "first_key_ms", "total_ms", "timed_out",
]  # sample_id 0 = practice


def read_trials():
    if not config.TRIALS_CSV.exists():
        return []
    with open(config.TRIALS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def append_trials(rows):
    config.DATA_DIR.mkdir(exist_ok=True)
    new = not config.TRIALS_CSV.exists()
    with open(config.TRIALS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, TRIAL_FIELDS)
        if new:
            w.writeheader()
        w.writerows(rows)


def write_trials(rows):
    with open(config.TRIALS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, TRIAL_FIELDS)
        w.writeheader()
        w.writerows(rows)


def next_sample_id(trials):
    return max((int(t["sample_id"]) for t in trials), default=0) + 1


def usage_counts(trials):
    """How often each concept has been cued per language, to keep the pool balanced."""
    counts = {concept_id(c): dict.fromkeys(LANGUAGES, 0) for c in CONCEPTS}
    for t in trials:
        if int(t["sample_id"]) > 0:
            counts[t["concept_id"]][t["language"]] += 1
    return counts


def _usable(t):
    return (t["correct"] == "True" and t["timed_out"] != "True"
            and t["first_key_ms"] != "" and float(t["first_key_ms"]) >= config.MIN_LATENCY_MS)


def summarize_samples(trials):
    """One row per sample: mean log latency of usable trials per language, plus validity."""
    by_sample = defaultdict(list)
    for t in trials:
        if int(t["sample_id"]) > 0:
            by_sample[int(t["sample_id"])].append(t)
    rows = []
    for sid, ts in sorted(by_sample.items()):
        row = {"sample_id": sid, "first_language": min(ts, key=lambda t: int(t["block_position"]))["language"]}
        valid = True
        for lang in LANGUAGES:
            lt = [t for t in ts if t["language"] == lang]
            good = [t for t in lt if _usable(t)]
            row[f"{lang}_n_usable"] = len(good)
            row[f"{lang}_accuracy"] = round(sum(t["correct"] == "True" for t in lt) / len(lt), 3)
            row[f"{lang}_mean_log_ms"] = round(mean(math.log(float(t["first_key_ms"])) for t in good), 4) if good else ""
            valid &= len(good) >= config.MIN_VALID_TRIALS
        row["valid"] = valid
        row["log_diff_es_minus_en"] = round(row["ES_mean_log_ms"] - row["EN_mean_log_ms"], 4) if valid else ""
        rows.append(row)
    return rows


def rescore(trials):
    """Re-grade stored responses against the current vocab (after adding accepted variants)."""
    lookup = {concept_id(c): c for c in CONCEPTS}
    changed = 0
    for t in trials:
        names = accepted(lookup[t["concept_id"]], t["language"])
        correct, near = score(t["response"], names)
        if (str(correct), str(near)) != (t["correct"], t["near_miss"]):
            changed += 1
        t.update(correct=correct, near_miss=near, accepted="|".join(names))
    return changed
