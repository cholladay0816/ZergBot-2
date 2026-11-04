import sys

import pytest

from zergbot.__main__ import main


@pytest.mark.parametrize(
    "option,value",
    [("--worker-defenders", "-1"), ("--burrow-escape-frames", "-1"), ("--regroup-roaches", "12")],
)
def test_invalid_experiment_controls_fail_before_game_launch(monkeypatch, capsys, option, value):
    monkeypatch.setattr(sys, "argv", ["zergbot2", option, value])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert "error:" in capsys.readouterr().err


def test_library_converted_startup_failure_returns_nonzero_exit(monkeypatch, tmp_path):
    import json

    import sc2.main
    import sc2.maps
    from sc2.data import Result

    def converted_failure(map_data, players, **kwargs):
        recorder = players[0].ai.telemetry.recorder
        recorder.error_type = "RuntimeError"
        recorder.termination = "startup_failed"
        return Result.Defeat

    monkeypatch.setattr(sc2.maps, "get", lambda name: object())
    monkeypatch.setattr(sc2.main, "run_game", converted_failure)
    monkeypatch.setattr(sys, "argv", ["zergbot2", "--diagnostics-dir", str(tmp_path)])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1
    payload = json.loads(next(tmp_path.glob("*/match.json")).read_text())
    assert payload["termination"] == "startup_failed"
