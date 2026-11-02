"""Terminal cued-recall session: emoji appears, name it in the cued language, press Enter."""
import codecs
import os
import random
import select
import sys
import termios
import time
import tty
from datetime import datetime

from . import config, store
from .scoring import score
from .vocab import CONCEPTS, LANGUAGE_NAMES, LANGUAGES, accepted, concept_id

CLEAR = "\033[2J\033[H"
BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"


class Quit(Exception):
    pass


def read_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        ch = codecs.getincrementaldecoder("utf-8")().decode(os.read(fd, 8))
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if ch in ("\x03", "\x04"):
        raise Quit
    return ch


def read_response(timeout_s):
    """Echo typed text; return (text, first_key_ms, total_ms, timed_out). Timer starts at call."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    decoder = codecs.getincrementaldecoder("utf-8")()
    typed, first = [], None
    try:
        termios.tcflush(fd, termios.TCIFLUSH)
        start = time.perf_counter()
        while True:
            budget = timeout_s if first is None else 15.0
            wait = budget - (time.perf_counter() - (start if first is None else first))
            if wait <= 0 or not select.select([fd], [], [], wait)[0]:
                return "".join(typed), first and (first - start) * 1000, (time.perf_counter() - start) * 1000, True
            now = time.perf_counter()
            for ch in decoder.decode(os.read(fd, 32)):
                if ch in ("\x03", "\x04"):
                    raise Quit
                if ch in ("\r", "\n"):
                    return "".join(typed), first and (first - start) * 1000, (now - start) * 1000, False
                if ch in ("\x7f", "\b"):
                    if typed:
                        typed.pop()
                        sys.stdout.write("\b \b")
                elif ch.isprintable():
                    if first is None:
                        first = now
                    typed.append(ch)
                    sys.stdout.write(ch)
            sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def choose_sample(trials, k):
    """Pick the 2k least-used concepts; give the k most English-heavy ones to Spanish."""
    counts = store.usage_counts(trials)
    ranked = sorted(CONCEPTS, key=lambda c: (sum(counts[concept_id(c)].values()), random.random()))[: 2 * k]
    ranked.sort(key=lambda c: (counts[concept_id(c)]["EN"] - counts[concept_id(c)]["ES"], random.random()), reverse=True)
    return {"ES": ranked[:k], "EN": ranked[k:]}


def run_block(language, concepts, sample_id, session_id, block_position, label):
    rows = []
    sys.stdout.write(f"{CLEAR}\n   {BOLD}{LANGUAGE_NAMES[language]}{RESET}  {DIM}{label}  (Enter = skip){RESET}\n\n   press any key")
    sys.stdout.flush()
    read_key()
    for i, entry in enumerate(concepts, 1):
        sys.stdout.write(f"{CLEAR}\n   {DIM}{LANGUAGE_NAMES[language]}{RESET}\n\n        {entry[0]}\n\n   > ")
        sys.stdout.flush()
        text, first_ms, total_ms, timed_out = read_response(config.TIMEOUT_S)
        names = accepted(entry, language)
        correct, near = score(text, names)
        rows.append({
            "sample_id": sample_id, "session_id": session_id,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "block_position": block_position, "trial_in_block": i, "language": language,
            "concept_id": concept_id(entry), "emoji": entry[0], "accepted": "|".join(names),
            "response": text, "correct": correct, "near_miss": near,
            "first_key_ms": "" if first_ms is None else round(first_ms, 1),
            "total_ms": round(total_ms, 1), "timed_out": timed_out,
        })
        sys.stdout.write(CLEAR)
        sys.stdout.flush()
        time.sleep(random.uniform(0.4, 0.8))
    return rows


def run_session(n_samples):
    if not sys.stdin.isatty():
        sys.exit("run needs an interactive terminal")
    trials = store.read_trials()
    session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    k = config.TRIALS_PER_LANGUAGE
    done = 0
    try:
        sys.stdout.write(f"{CLEAR}\n   Name each emoji in the language shown. First keystroke is timed: type fast, accents optional.\n"
                         f"   Ctrl-C quits (the current sample is discarded).\n\n   press any key to start with practice")
        sys.stdout.flush()
        read_key()
        practice = random.sample(CONCEPTS, config.PRACTICE_TRIALS)
        half = config.PRACTICE_TRIALS // 2
        rows = (run_block("EN", practice[:half], 0, session_id, 1, "practice")
                + run_block("ES", practice[half:], 0, session_id, 2, "practice"))
        store.append_trials(rows)
        for _ in range(n_samples):
            trials = store.read_trials()
            sample_id = store.next_sample_id(trials)
            picks = choose_sample(trials, k)
            order = ("EN", "ES") if sample_id % 2 else ("ES", "EN")
            rows = []
            for pos, lang in enumerate(order, 1):
                random.shuffle(picks[lang])
                rows += run_block(lang, picks[lang], sample_id, session_id, pos, f"sample {sample_id}")
            store.append_trials(rows)  # only complete samples reach disk
            done += 1
    except (Quit, KeyboardInterrupt):
        pass
    finally:
        sys.stdout.write(f"{CLEAR}\n   Session saved: {done} sample(s).\n\n")
