"""第六批：覆盖 adaptive_hybrid / sensitivity 的 __main__ 与 demo 块"""
import os
import sys
import runpy

os.environ["MPLBACKEND"] = "Agg"

import matplotlib

matplotlib.use("Agg")


def test_adaptive_hybrid_main_block():
    old = sys.argv
    sys.argv = ["adaptive_hybrid.py"]
    try:
        runpy.run_module("algorithms.optimization.adaptive_hybrid", run_name="__main__")
    except SystemExit:
        pass
    finally:
        sys.argv = old


def test_sensitivity_main_block(tmp_path, monkeypatch):
    monkeypatch.setattr("matplotlib.pyplot.show", lambda: None)
    monkeypatch.chdir(tmp_path)
    old = sys.argv
    sys.argv = ["sensitivity.py"]
    try:
        runpy.run_module("algorithms.validation.sensitivity", run_name="__main__")
    except SystemExit:
        pass
    finally:
        sys.argv = old
    assert (tmp_path / "tornado.png").exists()