import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(ROOT / "scripts")]

from make_synthetic_data import synthetic_m15  # noqa: E402
from xauquant.config import load_config  # noqa: E402


@pytest.fixture(scope="session")
def cfg():
    return load_config()


@pytest.fixture(scope="session")
def m15():
    df = synthetic_m15(start="2020-01-01", end="2020-06-30", seed=3)
    return df.set_index("time")
