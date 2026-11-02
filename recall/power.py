import math

from . import config


def required_n(d=config.EFFECT_SIZE, alpha=config.ALPHA, power=config.POWER):
    try:
        from statsmodels.stats.power import TTestIndPower, TTestPower
    except ImportError:
        raise SystemExit("power needs statsmodels: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt")
    paired = TTestPower().solve_power(effect_size=d, alpha=alpha, power=power, alternative="two-sided")
    independent = TTestIndPower().solve_power(effect_size=d, alpha=alpha, power=power, ratio=1, alternative="two-sided")
    return math.ceil(paired), math.ceil(independent)
