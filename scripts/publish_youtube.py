"""Commit YouTube data to the primary store before publishing its public projection."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import tempfile

from radar_core.publication import PublicationError, SubprocessGitRepository, publish_with_retry, snapshot_revision
from radar_core.storage import primary
from radar_core.storage.sql import StorageError

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_URL = "https://github.com/danielet087/game-trend-radar.git"
PATH = "data/youtube_live.json"


def _observed(value):
    if not isinstance(value, str):
        raise ValueError("YouTube observation time is required")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("YouTube observation time is invalid") from None
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("YouTube observation time requires a timezone")
    return stamp


def apply_snapshot(payload, destination, *, require_clock=True):
    path = Path(destination) / PATH
    incoming = _observed(payload.get("generated_at")) if require_clock or "generated_at" in payload else None
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(existing, dict):
            raise ValueError("Existing YouTube data is invalid")
        previous = _observed(existing.get("generated_at")) if require_clock or "generated_at" in existing else None
        if incoming is not None and previous is not None:
            if incoming < previous:
                return
            if incoming == previous and existing != payload:
                raise ValueError("Conflicting YouTube observations for the same time")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def run_publication(snapshot, environment):
    if not environment.get("FRONTEND_REPO_TOKEN", "").strip():
        raise SystemExit("FRONTEND_REPO_TOKEN is not configured; no data published.")
    source = Path(snapshot).resolve()
    output = source.with_name("youtube_publication.json")
    if output == source:
        raise ValueError("Publication receipt must not replace the collected snapshot")
    output.unlink(missing_ok=True)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Collected YouTube snapshot must be an object")
    revision = snapshot_revision(payload)
    require_clock = primary.enabled()
    if require_clock:
        _observed(payload.get("generated_at"))
    with tempfile.TemporaryDirectory(prefix="radar-youtube-publish.", dir=environment.get("RUNNER_TEMP") or None) as temporary:
        frontend = Path(temporary) / "frontend"
        subprocess.run(["git", "clone", "--depth", "1", "--branch", "main", FRONTEND_URL, str(frontend)],
                       check=True, env=dict(environment))
        for key, value in (("user.name", "github-actions[bot]"), ("user.email", "41898282+github-actions[bot]@users.noreply.github.com")):
            subprocess.run(["git", "-C", str(frontend), "config", key, value], check=True, env=dict(environment))
        repository = SubprocessGitRepository(frontend, disposable_checkout=True, environment=environment,
            push_command_prefix=("bash", str(ROOT / "scripts/git_frontend_auth.sh")))
        receipt = publish_with_retry(repository, lambda root: apply_snapshot(payload, root, require_clock=require_clock),
            paths=(PATH,), message="data: update youtube live metrics", input_revision=revision,
            payload_revision=revision, max_attempts=5)
    output.write_text(json.dumps(receipt.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if receipt.attempts > 1:
        print(f"Push rejected; retrying against latest frontend succeeded on attempt {receipt.attempts}.")
    print("Published YouTube database projection with acknowledged Git revision.")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", nargs="?", default="output/youtube_live.json")
    args = parser.parse_args()
    try:
        run_publication(args.snapshot, os.environ)
    except (ValueError, OSError, subprocess.SubprocessError, PublicationError, StorageError):
        raise SystemExit("YouTube publication failed; collected JSON remains available for retry.") from None


if __name__ == "__main__":
    main()
