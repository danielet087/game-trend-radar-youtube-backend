"""Observation ordering and staged database publication contracts."""
import json
from pathlib import Path

import pytest
from scripts.publish_youtube import PATH, apply_snapshot


def test_late_youtube_result_cannot_replace_newer_primary_snapshot(tmp_path):
    fresh = {"generated_at": "2026-10-15T10:00:00Z", "top_games": [{"name": "new"}]}
    old = {"generated_at": "2026-10-15T09:00:00Z", "top_games": [{"name": "old"}]}
    apply_snapshot(fresh, tmp_path)
    apply_snapshot(old, tmp_path)
    assert json.loads((tmp_path / PATH).read_text()) == fresh


def test_conflicting_same_time_result_and_missing_clock_are_rejected(tmp_path):
    snapshot = {"generated_at": "2026-10-15T10:00:00Z", "top_games": []}
    apply_snapshot(snapshot, tmp_path)
    apply_snapshot(snapshot, tmp_path)
    with pytest.raises(ValueError, match="Conflicting"):
        apply_snapshot({**snapshot, "top_games": [{}]}, tmp_path)
    for value in ({}, {"generated_at": "2026-10-15T10:00:00"}, {"generated_at": "bad"}):
        with pytest.raises(ValueError): apply_snapshot(value, tmp_path)
    assert json.loads((tmp_path / PATH).read_text()) == snapshot


def test_youtube_keeps_manual_trigger_with_staged_primary_and_pause_gate():
    text = (Path(__file__).resolve().parents[1] / ".github/workflows/collect.yml").read_text()
    assert "workflow_dispatch:" in text and "  schedule:" not in text
    assert "if: vars.RADAR_DATABASE_MIGRATION_PAUSE != '1'" in text
    assert "RADAR_DATABASE_PRIMARY: ${{ vars.RADAR_DATABASE_PRIMARY || '0' }}" in text
