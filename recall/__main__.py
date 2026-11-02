import argparse
import csv

from . import config, store


def cmd_power(a):
    from .power import required_n
    paired, independent = required_n(a.d, a.alpha, a.power)
    print(f"two-sided t-test, d={a.d}, alpha={a.alpha}, power={a.power}")
    print(f"  paired (same sample measured in both languages): {paired} samples")
    print(f"  independent groups:                              {independent} per group ({2 * independent} total)")


def cmd_run(a):
    from .collect import run_session
    run_session(a.samples)
    cmd_status(a)


def cmd_status(_):
    trials = store.read_trials()
    samples = store.summarize_samples(trials)
    valid = sum(s["valid"] for s in samples)
    near = sum(t["near_miss"] == "True" for t in trials)
    print(f"samples collected: {len(samples)} / {config.TARGET_SAMPLES} target")
    print(f"valid samples:     {valid} / {config.REQUIRED_VALID_SAMPLES} required by power analysis")
    left = max(config.TARGET_SAMPLES - len(samples), 0)
    sessions = -(-left // config.SAMPLES_PER_SESSION)
    print(f"remaining:         {left} samples (~{sessions} session(s) of {config.SAMPLES_PER_SESSION})")
    if near:
        print(f"{near} near-miss response(s) to check: python3 -m recall review")
    if len(samples) >= config.TARGET_SAMPLES and valid < config.REQUIRED_VALID_SAMPLES:
        print("target reached but too few valid samples: collect the shortfall, then stop.")


def cmd_review(_):
    seen = set()
    for t in store.read_trials():
        if t["correct"] != "True" and t["response"] and (t["concept_id"], t["language"], t["response"]) not in seen:
            seen.add((t["concept_id"], t["language"], t["response"]))
            flag = "near-miss" if t["near_miss"] == "True" else "wrong"
            print(f"{t['emoji']} {t['language']}  typed {t['response']!r:20} accepted {t['accepted']}  [{flag}]")
    print("Add legitimate variants in recall/vocab.py, then: python3 -m recall rescore")


def cmd_rescore(_):
    trials = store.read_trials()
    print(f"{store.rescore(trials)} trial(s) re-graded")
    store.write_trials(trials)


def cmd_export(_):
    rows = store.summarize_samples(store.read_trials())
    if not rows:
        raise SystemExit("no samples yet")
    with open(config.SAMPLES_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {config.SAMPLES_CSV}")


def main():
    p = argparse.ArgumentParser(prog="recall", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("power", help="required sample size")
    s.add_argument("--d", type=float, default=config.EFFECT_SIZE)
    s.add_argument("--alpha", type=float, default=config.ALPHA)
    s.add_argument("--power", type=float, default=config.POWER)
    s.set_defaults(fn=cmd_power)
    s = sub.add_parser("run", help="collect one session")
    s.add_argument("--samples", type=int, default=config.SAMPLES_PER_SESSION)
    s.set_defaults(fn=cmd_run)
    for name, fn, h in [("status", cmd_status, "progress toward target"),
                        ("review", cmd_review, "list wrong answers worth a second look"),
                        ("rescore", cmd_rescore, "re-grade after editing accepted answers"),
                        ("export", cmd_export, "write data/samples.csv, one row per sample")]:
        sub.add_parser(name, help=h).set_defaults(fn=fn)
    a = p.parse_args()
    a.fn(a)


main()
