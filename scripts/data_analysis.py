from statsmodels.stats.power import TTestPower
from statsmodels import api
import matplotlib.pyplot as plt
from pathlib import Path

import pandas as pd
from scipy.stats import t as t_dist, ttest_rel, shapiro

SAMPLES_CSV = Path(__file__).resolve().parent.parent / "data" / "samples.csv"
alpha = 0.05

def calculate_power():
    """
    Documenting the use of the statsmodel Power Analysis to define the numbers of samples needed.

    Returns the missing value from the power analysis computation, in this case the sample size
    """
    effect_size = 0.4  # From literature cited in ../docs/reflection.md

    analysis = TTestPower()

    n = analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=0.80,
        alternative='two-sided'
    )

    return n

def check_normality(means_df):
    """
    Since I have a small sample size, I need to verify that the assumption of normality holds to run my paired ttest
    """
    res = shapiro(means_df)

    fig, ax= plt.subplots(figsize=(12, 5))

    api.qqplot(means_df, fit=True, ax=ax, line='45')

    plt.show()

    print(f"Shapiro-Wilk: W={res.statistic:.4f}, p={res.pvalue:.4f}")

    return res.statistic


def run_ttest(samples_csv=SAMPLES_CSV):
    """Two-tailed paired t-test of Spanish vs English mean log first-key latency.

    Uses valid samples from data/samples.csv (run `./recall.sh export` first).
    A positive mean difference means Spanish was slower.
    """
    df = pd.read_csv(samples_csv)
    df = df[df["valid"]]

    es, en = df["ES_mean_log_ms"], df["EN_mean_log_ms"]
    result = ttest_rel(es, en, alternative='two-sided')

    diff = es - en
    n = len(diff)
    sem = diff.std(ddof=1) / n ** 0.5
    margin = t_dist.ppf(1 - alpha / 2, n - 1) * sem

    check_normality(diff)

    return {
        "n": n,
        "mean_log_ms_en": en.mean(),
        "mean_log_ms_es": es.mean(),
        "mean_diff": diff.mean(),
        "ci": (diff.mean() - margin, diff.mean() + margin),
        "t": result.statistic,
        "df": n - 1,
        "p_value": result.pvalue,
        "cohens_dz": diff.mean() / diff.std(ddof=1),
        "reject_h0": result.pvalue < alpha,
    }


if __name__ == "__main__":
    samples = calculate_power()
    print("Number of samples required: ", samples)

    results = run_ttest()
    print(results)
