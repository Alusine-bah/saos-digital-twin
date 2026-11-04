"""The Streamlit demo must start and render for every preset without an exception."""
import os, sys
import pytest
st_testing = pytest.importorskip("streamlit.testing.v1")
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)


def test_app_renders_default_and_all_presets():
    at = st_testing.AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=180).run()
    assert not at.exception, at.exception
    assert len(at.metric) == 6
    presets = at.sidebar.selectbox[0].options
    for name in presets:
        at.sidebar.selectbox[0].select(name)
        at.run()
        assert not at.exception, f"{name}: {at.exception}"
        assert len(at.metric) == 6
