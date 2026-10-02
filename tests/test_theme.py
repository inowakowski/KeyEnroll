from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QColorDialog

from test_enroll import FakeSource
from keyenroll.config import ConfigStore, Instance
from keyenroll.secrets_store import TokenStore
from keyenroll.ui import theme
from keyenroll.ui.common import AppContext
from keyenroll.ui.main_window import MainWindow, PAGE_INSTANCES


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


contrast = theme.contrast


def test_contrast_ratio_reference_values():
    assert contrast("#000000", "#ffffff") == pytest.approx(21)
    assert contrast("#777777", "#ffffff") == pytest.approx(4.48, abs=0.01)
    assert contrast("#123456", "#123456") == pytest.approx(1)


def test_presets_are_light_dark_and_yubico():
    assert theme.PRESETS == ("light", "dark", "yubico")
    name, yubico = theme.build_tokens("yubico")
    assert name == "yubico" and yubico["accent"] == "#9aca3c"
    assert yubico["bg"] == theme.THEMES["dark"]["bg"]
    assert theme.build_tokens("light")[1]["accent"] == theme.THEMES["light"]["accent"]


def test_every_scheme_defines_the_same_tokens():
    keys = set(theme.THEMES["light"])
    assert set(theme.THEMES["dark"]) == keys
    for setting in ("yubico", "custom"):
        assert set(theme.build_tokens(setting)[1]) == keys


@pytest.mark.parametrize(
    "setting,base,accent",
    [
        ("light", "", ""),
        ("dark", "", ""),
        ("yubico", "", ""),
        ("custom", "light", "#d6336c"),
        ("custom", "dark", "#ffd43b"),  # very light accent
        ("custom", "light", "#0b2545"),  # very dark accent
        ("custom", "dark", "#12b886"),
        ("custom", "light", "#ff0000"),
        ("custom", "dark", "#808080"),
    ],
)
def test_text_stays_readable(setting, base, accent):
    _, t = theme.build_tokens(setting, base, accent)
    assert contrast(t["on_accent"], t["accent"]) >= 3, "label on a primary button"
    assert contrast(t["text"], t["bg"]) >= 7
    assert contrast(t["text"], t["accent_soft"]) >= 4.5, "selected table row"


def test_invalid_custom_values_fall_back():
    name, t = theme.build_tokens("custom", "purple", "not-a-colour")
    assert name == "custom"
    assert t["accent"] == theme.DEFAULT_CUSTOM_ACCENT and t["bg"] == theme.THEMES["dark"]["bg"]
    assert theme.valid_color("#A1b2C3") and not theme.valid_color("#abc")


@pytest.mark.parametrize("setting", ["auto", "light", "dark", "yubico", "custom"])
def test_schemes_apply_without_errors(app, setting):
    applied = theme.apply_theme(app, setting, "light", "#d6336c")
    assert applied in ("light", "dark", "yubico", "custom")
    sheet = app.styleSheet()
    assert "$" not in sheet  # every token was substituted
    assert theme.token("accent") in sheet


def test_settings_switch_the_scheme_live_and_remember_it(app, tmp_path, monkeypatch):
    config = ConfigStore(tmp_path / "config.json")
    config.upsert_instance(Instance(name="Prod", kind="okta"))
    ctx = AppContext(config, TokenStore(), source=FakeSource())
    window = MainWindow(ctx)
    window.nav.setCurrentRow(PAGE_INSTANCES)
    page = window.pages.currentWidget()
    labels = [page.theme.itemText(i) for i in range(page.theme.count())]
    assert labels == ["System default", "Light", "Dark", "Yubico", "Custom"]
    assert page.custom_row.isHidden()

    page.theme.setCurrentIndex(page.theme.findData("yubico"))
    assert theme.token("accent") == "#9aca3c" and "#9aca3c" in app.styleSheet()
    assert ConfigStore(config.path).theme == "yubico"

    page.theme.setCurrentIndex(page.theme.findData("custom"))
    assert not page.custom_row.isHidden()
    monkeypatch.setattr(QColorDialog, "getColor", staticmethod(lambda *a, **k: QColor("#d6336c")))
    page.accent_button.click()
    page.custom_base.setCurrentIndex(page.custom_base.findData("light"))

    saved = ConfigStore(config.path)
    assert (saved.theme, saved.custom_base, saved.custom_accent) == ("custom", "light", "#d6336c")
    assert theme.token("accent") == "#d6336c"
    assert theme.token("bg") == theme.THEMES["light"]["bg"]

    # A cancelled colour dialog changes nothing.
    monkeypatch.setattr(QColorDialog, "getColor", staticmethod(lambda *a, **k: QColor()))
    page.accent_button.click()
    assert ConfigStore(config.path).custom_accent == "#d6336c"
    window.close()
    theme.apply_theme(app, "light")
