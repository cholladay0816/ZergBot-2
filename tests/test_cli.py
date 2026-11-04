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
