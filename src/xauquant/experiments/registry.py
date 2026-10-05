"""Experiment registry (SQLite, stdlib). Every run is recorded — including
failures — so the number of trials is known when deflating Sharpe ratios.
Optionally mirrored to MLflow if installed and MLFLOW_TRACKING_URI is set."""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from xauquant.config import ROOT

DB = ROOT / "experiments" / "registry.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS hypotheses (
    hypothesis_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    statement TEXT NOT NULL,          -- falsifiable claim
    rationale TEXT,                   -- economic / behavioural reason
    kill_criteria TEXT NOT NULL,      -- what result rejects it (set BEFORE running)
    status TEXT NOT NULL DEFAULT 'proposed',  -- proposed|testing|rejected|survived|lockbox_pass|lockbox_fail|paper|live
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hypothesis_id TEXT NOT NULL REFERENCES hypotheses(hypothesis_id),
    started_at TEXT NOT NULL,
    git_commit TEXT,
    git_dirty INTEGER,
    data_range TEXT,
    config_json TEXT NOT NULL,
    metrics_json TEXT,
    gates_json TEXT,
    verdict TEXT,                     -- reject|survive|error
    notes TEXT
);
"""


def connect(path: Path = DB) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    return con


def _git() -> tuple[str | None, int | None]:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = int(bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()))
        return commit, dirty
    except Exception:
        return None, None


def register_hypothesis(con, hypothesis_id: str, title: str, statement: str, kill_criteria: str,
                        rationale: str = "") -> None:
    con.execute(
        "INSERT OR IGNORE INTO hypotheses VALUES (?,?,?,?,?, 'proposed', ?)",
        (hypothesis_id, title, statement, rationale, kill_criteria, datetime.now(timezone.utc).isoformat()),
    )
    con.commit()


def log_run(con, hypothesis_id: str, config: dict, metrics: dict, gates: dict, verdict: str,
            data_range: str = "", notes: str = "") -> int:
    commit, dirty = _git()
    cur = con.execute(
        "INSERT INTO runs (hypothesis_id, started_at, git_commit, git_dirty, data_range, config_json,"
        " metrics_json, gates_json, verdict, notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (hypothesis_id, datetime.now(timezone.utc).isoformat(), commit, dirty, data_range,
         json.dumps(config, default=str), json.dumps(metrics, default=str), json.dumps(gates, default=str),
         verdict, notes),
    )
    con.execute("UPDATE hypotheses SET status=? WHERE hypothesis_id=?",
                ("survived" if verdict == "survive" else "rejected" if verdict == "reject" else "testing",
                 hypothesis_id))
    con.commit()
    _mirror_mlflow(hypothesis_id, config, metrics, verdict)
    return int(cur.lastrowid)


def n_trials(con) -> int:
    return int(con.execute("SELECT COUNT(*) FROM runs").fetchone()[0])


def _mirror_mlflow(hypothesis_id, config, metrics, verdict) -> None:
    if not os.environ.get("MLFLOW_TRACKING_URI"):
        return
    try:
        import mlflow
    except ImportError:
        return
    mlflow.set_experiment("xauusd-meta")
    with mlflow.start_run(run_name=hypothesis_id):
        mlflow.set_tag("verdict", verdict)
        mlflow.log_params({k: str(v)[:250] for k, v in _flatten(config).items()})
        mlflow.log_metrics({k: float(v) for k, v in _flatten(metrics).items()
                            if isinstance(v, (int, float)) and v == v and abs(v) != float("inf")})


def _flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, key + "."))
        else:
            out[key] = v
    return out


def register_from_file(con, hypothesis_id: str, directory: Path = ROOT / "research" / "hypotheses") -> None:
    """Register a hypothesis from its Markdown file. Refuses to run without written
    kill criteria: deciding what failure looks like after seeing results is how
    backtests get overfit."""
    matches = sorted(directory.glob(f"{hypothesis_id}_*.md"))
    if not matches:
        raise FileNotFoundError(f"no research/hypotheses/{hypothesis_id}_*.md — write the hypothesis first")
    text = matches[0].read_text()
    sections = _sections(text)
    kill = sections.get("kill criteria", "")
    if not any(line.strip().lstrip("-").strip() for line in kill.splitlines()
               if not line.strip().startswith(("Any failed gate in", "_"))):
        raise ValueError(f"{matches[0].name}: 'Kill criteria' section is empty")
    title = text.splitlines()[0].lstrip("# ").strip()
    register_hypothesis(con, hypothesis_id, title, sections.get("statement", "").strip(), kill.strip(),
                        sections.get("mechanism", "").strip())


def _sections(md: str) -> dict[str, str]:
    out, key = {}, None
    for line in md.splitlines():
        if line.startswith("## "):
            key = line[3:].split("(")[0].split("/")[0].strip().lower()
            out[key] = ""
        elif key:
            out[key] += line + "\n"
    return out
