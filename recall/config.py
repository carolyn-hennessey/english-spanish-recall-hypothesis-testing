"""Pre-registered design constants. Change these before collecting, not after."""
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TRIALS_CSV = DATA_DIR / "trials.csv"
SAMPLES_CSV = DATA_DIR / "samples.csv"

# Power analysis inputs
EFFECT_SIZE = 0.4
ALPHA = 0.05
POWER = 0.8

# Collection plan: paired t-test needs 52 valid samples; 60 leaves room for exclusions.
REQUIRED_VALID_SAMPLES = 52
TARGET_SAMPLES = 60

TRIALS_PER_LANGUAGE = 4      # one sample = 4 English + 4 Spanish cued-recall trials
PRACTICE_TRIALS = 4          # per session, not counted
SAMPLES_PER_SESSION = 15     # ~6-8 minutes

TIMEOUT_S = 6.0              # no keystroke by then = miss
MIN_LATENCY_MS = 250         # faster than this = anticipation, trial excluded
MIN_VALID_TRIALS = 3         # per language, else the whole sample is excluded
