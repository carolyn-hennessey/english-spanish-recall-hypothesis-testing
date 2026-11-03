# English vs Spanish Vocabulary Recall

Hypothesis test of my own vocabulary recall in English (L1) vs Spanish (L2). The design is in [`docs/reflection.md`](docs/reflection.md) and the collection plan is in [`docs/collection-plan.md`](docs/collection-plan.md).


## Replicating the Experiment/Data Collection
Setup your local environment
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the CLI
``` sh
./recall.sh run       # collect one session
./recall.sh status    # progress toward the 60-sample target
./recall.sh export    # build data/samples.csv from data/trials.csv
```

## Replicating the Statistical Analysis
Run the the scripts/data_analysis.py script from the root of the repository and observe terminal output as results.

```sh
python3 scripts/data_analysis.py
```

## Data dictionary

### `data/trials.csv` (raw, one row per trial)

Written by `./recall.sh run`. Rows are appended once a whole sample is complete.

| Column | Values | Description |
|---|---|---|
| `sample_id` | integer; `0` = practice | Which sample the trial belongs to. Practice trials (`0`) are never analyzed. |
| `session_id` | `YYYYMMDD-HHMMSS` | Start time of the `run` session that produced the trial. |
| `timestamp` | ISO 8601, local time | When the trial finished. |
| `block_position` | `1` or `2` | Whether the trial's language block came first or second within the sample. Alternates by sample to counterbalance order. |
| `trial_in_block` | `1`-`4` (`1`-`2` for practice) | Position of the trial within its language block. |
| `language` | `EN` or `ES` | Language the emoji had to be named in. |
| `concept_id` | text, e.g. `dog` | Identifier of the concept, equal to its first English name in `recall/vocab.py`. |
| `emoji` | one emoji | The cue shown. |
| `accepted` | names joined by `\|`, e.g. `cerdo\|puerco\|chancho` | Answers counted as correct for this concept and language when the trial was graded (or last re-graded). |
| `response` | text, may be empty | What was typed, exactly as entered. Empty means skipped or timed out. |
| `correct` | `True` / `False` | Whether `response` matched an accepted answer, ignoring case, accents and a leading article. |
| `near_miss` | `True` / `False` | Wrong, but within one character edit of an accepted answer (likely a typo). Flagged for `./recall.sh review`; not counted as correct. |
| `first_key_ms` | milliseconds, e.g. `812.4`; empty if no key was pressed | **Primary outcome.** Time from the emoji appearing to the first printable keystroke: retrieval latency, independent of word length. |
| `total_ms` | milliseconds | Time from the emoji appearing to pressing Enter (or to the timeout). Includes typing, so it is context only, not the outcome. |
| `timed_out` | `True` / `False` | No keystroke within 6 s, or more than 15 s to finish a word once typing began. |

A trial is **usable** if `correct` is `True`, `timed_out` is `False` and `first_key_ms` is at least 250.

### `data/samples.csv` (derived, one row per sample)

Written by `./recall.sh export`. Never edit by hand; regenerate it from `trials.csv`.

| Column | Values | Description |
|---|---|---|
| `sample_id` | integer, from `1` | Matches `sample_id` in `trials.csv`. Also a time index for checking practice trends. |
| `first_language` | `EN` or `ES` | Language of the first block in the sample. |
| `EN_n_usable` | `0`-`4` | Usable English trials in the sample. |
| `EN_accuracy` | `0`-`1` | Share of the 4 English trials with `correct = True`. Secondary outcome. |
| `EN_mean_log_ms` | natural log of ms; empty if no usable trials | Mean of `ln(first_key_ms)` over usable English trials. |
| `ES_n_usable` | `0`-`4` | Usable Spanish trials in the sample. |
| `ES_accuracy` | `0`-`1` | Share of the 4 Spanish trials with `correct = True`. Secondary outcome. |
| `ES_mean_log_ms` | natural log of ms; empty if no usable trials | Mean of `ln(first_key_ms)` over usable Spanish trials. |
| `valid` | `True` / `False` | `True` if both `EN_n_usable` and `ES_n_usable` are at least 3. Only valid samples enter the analysis. |
| `log_diff_es_minus_en` | log-ms; empty if `valid` is `False` | `ES_mean_log_ms - EN_mean_log_ms`. The paired t-test runs on this column; positive means Spanish was slower. |
