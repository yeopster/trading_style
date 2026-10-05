import pandas as pd
import pytest

from xauquant.data.lockbox import LockboxViolation, assert_no_lockbox, dev_slice, open_lockbox
from xauquant.experiments import registry
from xauquant.experiments.gates import evaluate_gates


def frame():
    idx = pd.date_range("2022-12-30", "2023-01-02", freq="15min", tz="UTC")
    return pd.DataFrame({"close": 1.0}, index=idx)


def test_dev_slice_excludes_lockbox(cfg):
    dev = dev_slice(frame(), cfg)
    assert_no_lockbox(dev.index, cfg)
    with pytest.raises(LockboxViolation):
        assert_no_lockbox(frame().index, cfg)


def test_lockbox_opens_once_per_hypothesis(cfg, tmp_path):
    log = tmp_path / "log.jsonl"
    out = open_lockbox(frame(), cfg, hypothesis_id="H99", frozen_commit="abc", reason="t", log_path=log)
    assert out.index.min() >= pd.Timestamp("2023-01-01", tz="UTC")
    with pytest.raises(LockboxViolation):
        open_lockbox(frame(), cfg, hypothesis_id="H99", frozen_commit="abc", reason="t", log_path=log)


def test_registry_requires_kill_criteria(tmp_path):
    con = registry.connect(tmp_path / "r.db")
    (tmp_path / "H98_x.md").write_text("# H98 — x\n\n## Statement\nfoo\n\n## Kill criteria (before)\n"
                                       "Any failed gate in `gates.py` rejects.\n-\n")
    with pytest.raises(ValueError):
        registry.register_from_file(con, "H98", tmp_path)
    (tmp_path / "H97_y.md").write_text("# H97 — y\n\n## Statement\nfoo\n\n## Kill criteria\n- AUC < 0.55\n")
    registry.register_from_file(con, "H97", tmp_path)
    registry.log_run(con, "H97", {"a": 1}, {"m": 1}, {}, "reject")
    assert registry.n_trials(con) == 1
    assert con.execute("select status from hypotheses").fetchone()[0] == "rejected"


def test_gates_fail_on_missing_metrics():
    results, passed = evaluate_gates({})
    assert not passed and not any(r["pass"] for r in results.values())


def test_seed_hypotheses_register(tmp_path):
    con = registry.connect(tmp_path / "r.db")
    for h in ("H01", "H02"):
        registry.register_from_file(con, h)
