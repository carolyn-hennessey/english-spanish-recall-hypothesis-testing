# Data Collection Plan
** AI USE DISCLAIMER **: Since I was my own test subject I leveraged Claude to write the CLI to run the test and plan the inputs. This document is Claude's output of the experiment designed accepting the `/docs/reflection.md` as input along with the following prompt using Opus 5.5:

```sh
Taking a look at the experiment design that is being drawn up in docs/reflection.md we need to plan the collection of data for me to do myself testing vocabulary recall in English and Spanish. A power analysis used the values provided in the document to know how many samples are needed. Please use the workspace as the guide for this experiment. I need the output to be a plan for collection of the required samples that others could reproduce. It would be cool if the sample collectiion was done via a CLI that I include in the workspace. I also don't want to spend hours on collection of the samples, so optmizing for quick sample collection would be awesome!
```

## Power analysis result
Inputs from `reflection.md`: d = 0.4, power = 0.8, alpha = 0.05, two-tailed. Run `./recall.sh power` to reproduce.

| Design | Samples needed |
|---|---|
| **Paired t-test** (every sample measured in both languages) | **52** (power at n=52 is 0.808) |
| Independent groups | 100 per group, 200 total |

I am the only participant and each sample contains both an English and a Spanish measurement, so the paired design fits and cuts the work roughly in half versus 200. The CLI is built for it.

**Collection target: 60 samples (52 required + ~15% buffer for excluded samples).** The target is fixed before collecting: stop at 60, with no peeking at the language difference in between and no adding "just a few more" afterward.

## What one sample is
One sample = one short cued-recall test of 8 trials:
- 4 emoji named in English and 4 in Spanish, in separate blocks. Block order alternates sample by sample to cancel order effects.
- Emoji cues are language-neutral, so neither language is cued by a translation of the other.
- Outcome: **time to first keystroke** (retrieval latency), averaged over correct trials as mean log-ms per language. The sample's value is `ES - EN` in log-ms, which is what the paired t-test runs on.
- Why latency rather than accuracy: I am proficient in both languages, so accuracy will likely sit near ceiling and carry little signal. Accuracy is still recorded.

The 125-concept pool (`recall/vocab.py`) excludes cognates. Concept use is balanced automatically: the least-used concepts are picked first, and each concept is cued about equally often in each language.

## Time budget
About 30 seconds per sample (estimate; check against the first session), so 15 samples is a 7-8 minute session.

| Step | Time |
|---|---|
| Sessions | 4 x 15 samples = 60 samples |
| Total | roughly 30 minutes of typing |
| Per day | 1-2 sessions, spread across days and times of day |

Spreading sessions out matters: fatigue and time of day may affect L1 and L2 retrieval differently, and mixing them in beats one marathon.

## How to collect
```
./recall.sh run               # one session: 4 practice trials, then 15 samples
./recall.sh run --samples 8   # shorter session
./recall.sh status            # progress vs. target (counts only, no means)
```
Setup for the `power` command only: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`. `run` needs only the standard library.

During a session: type as soon as the word comes to mind, finish the word, press Enter. Accents and capitalization don't matter. Enter on a blank line skips (counts as a miss). No feedback is shown, so answers can't be learned mid-experiment. Ctrl-C quits and discards only the unfinished sample.

## Cleaning rules (fixed in advance)
- A trial is **usable** if correct, a key was pressed within 6 s, and first-key latency is at least 250 ms (faster = anticipation).
- A sample is **valid** if it has at least 3 usable trials in each language. Invalid samples are excluded and replaced by collecting extra.
- Practice trials (sample_id 0) are never analyzed.
- Wrong answers are reviewed once after collection: `./recall.sh review` lists them. Legitimate variants (regional Spanish words, synonyms) get added to `recall/vocab.py`, then `./recall.sh rescore` re-grades everything. Typos one edit away are flagged as near misses. No raw data is deleted.
- `./recall.sh export` writes `data/samples.csv`, one row per sample, ready for the paired t-test (on `log_diff_es_minus_en`, valid rows only).

## Files
- `data/trials.csv`: raw, one row per trial (response, latency, correctness, session, timestamp).
- `data/samples.csv`: derived per-sample table for analysis.
- `recall/config.py`: all design constants (sample sizes, thresholds).

## Caveats to carry into Limitations
- d = 0.4 comes from a different language pair (Chinese/English) and a different measure. If the true paired effect is smaller, 52 samples are underpowered: d = 0.35 needs 67 and d = 0.3 needs 90 (about 15 extra minutes). The target can be raised in `config.py` before collecting, not after seeing results.
- The pool is reused about 4 times per concept. Repetition may help Spanish more than English; concepts are balanced across languages and `sample_id` is recorded so the analysis can check for a practice trend.
- Emoji naming measures picture-to-word retrieval of concrete nouns, not the nuanced phrasing a story-driven game needs. That gap belongs in Interpretation.
