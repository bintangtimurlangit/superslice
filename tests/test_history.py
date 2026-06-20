"""Tests for the opt-in SQLite slicing history."""
from app.models import SliceResponse
from app.services import history
from app.services.slicing import SliceParams


def _response():
    return SliceResponse(
        success=True,
        print_time_minutes=10.0,
        print_time_formatted="10m 0s",
        filament_length_mm=100.0,
        filament_volume_cm3=2.0,
        filament_weight_g=2.48,
        filament_type="PLA",
        layer_height=0.2,
        infill_density=20,
        wall_count=3,
    )


def test_history_records_and_reads(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_ENABLED", True)
    monkeypatch.setattr(history, "HISTORY_DB_PATH", tmp_path / "history.db")
    history._reset_for_tests()
    history.init()
    try:
        params = SliceParams(0.2, 20, 3, "PLA", None)
        history.record(params, _response(), "model.stl")
        history.record(params, _response(), "model2.stl")

        assert history.count() == 2
        items = history.list_records()
        assert len(items) == 2
        assert items[0]["filament_type"] == "PLA"
        assert items[0]["print_time_seconds"] == 600

        record_id = items[0]["id"]
        fetched = history.get_record(record_id)
        assert fetched["filename"] in ("model.stl", "model2.stl")
    finally:
        history._reset_for_tests()


def test_history_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(history, "HISTORY_ENABLED", False)
    history._reset_for_tests()
    # Should not raise and should report nothing.
    history.record(SliceParams(0.2, 20, 3), _response(), "x.stl")
    assert history.count() == 0
    assert history.list_records() == []
