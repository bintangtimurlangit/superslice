"""Unit tests for G-code parsing and the slicer helpers."""
import textwrap

import pytest

from app.slicer import _parse_time_string, parse_gcode_statistics


class TestParseTimeString:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("45s", 45),
            ("19m 22s", 19 * 60 + 22),
            ("1h 30m 45s", 3600 + 30 * 60 + 45),
            ("2h", 2 * 3600),
            ("1d 2h 3m 4s", 86400 + 2 * 3600 + 3 * 60 + 4),
            ("", 0),
        ],
    )
    def test_parses_various_formats(self, text, expected):
        assert _parse_time_string(text) == expected

    def test_missing_units_do_not_raise(self):
        # Regression: the old implementation called .group() on a missing match.
        assert _parse_time_string("3m") == 180


class TestParseGcodeStatistics:
    def _write_gcode(self, tmp_path, body):
        path = tmp_path / "out.gcode"
        path.write_text(textwrap.dedent(body))
        return str(path)

    def test_extracts_all_fields(self, tmp_path):
        gcode = self._write_gcode(
            tmp_path,
            """\
            ; some header
            G1 X0 Y0
            ; filament used [mm] = 1506.53
            ; filament used [cm3] = 3.62
            ; estimated printing time (normal mode) = 19m 22s
            """,
        )
        stats = parse_gcode_statistics(gcode, filament_density=1.24)

        assert stats["filament_length_mm"] == pytest.approx(1506.53)
        assert stats["filament_volume_cm3"] == pytest.approx(3.62)
        assert stats["print_time_seconds"] == 19 * 60 + 22
        assert stats["print_time_formatted"] == "19m 22s"
        # weight = volume * density
        assert stats["filament_weight_g"] == pytest.approx(3.62 * 1.24)

    def test_missing_fields_default_to_zero(self, tmp_path):
        gcode = self._write_gcode(tmp_path, "; nothing useful here\nG1 X0\n")
        stats = parse_gcode_statistics(gcode, filament_density=1.24)

        assert stats["filament_length_mm"] == 0.0
        assert stats["filament_volume_cm3"] == 0.0
        assert stats["print_time_seconds"] == 0
        assert stats["filament_weight_g"] == 0.0

    def test_weight_scales_with_density(self, tmp_path):
        gcode = self._write_gcode(
            tmp_path, "; filament used [cm3] = 10.0\n"
        )
        pla = parse_gcode_statistics(gcode, filament_density=1.24)
        petg = parse_gcode_statistics(gcode, filament_density=1.27)

        assert pla["filament_weight_g"] == pytest.approx(12.4)
        assert petg["filament_weight_g"] == pytest.approx(12.7)
