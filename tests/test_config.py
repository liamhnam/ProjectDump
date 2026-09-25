from __future__ import annotations

import sys

import pytest

from codeappendix.config import (
    CONFIG_FILENAME,
    Config,
    ConfigError,
    apply,
    flatten_toml,
    render_template,
    resolve,
)

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib


def test_defaults_are_vietnamese_thesis():
    cfg, used = resolve(__import__("pathlib").Path("/nonexistent-dir"))
    assert used is None
    assert cfg.page_size == "A4" and cfg.font == "Times New Roman" and cfg.font_size == 13
    assert cfg.effective_title == "PHỤ LỤC A. MÃ NGUỒN CHƯƠNG TRÌNH"


def test_titles():
    assert apply(Config(), {"language": "en", "label": "B"}).effective_title == "APPENDIX B. SOURCE CODE"
    assert apply(Config(), {"label": ""}).effective_title == "MÃ NGUỒN CHƯƠNG TRÌNH"
    assert apply(Config(), {"title": "Phụ lục 2"}).effective_title == "Phụ lục 2"


def test_precedence_preset_file_cli(tmp_path):
    (tmp_path / CONFIG_FILENAME).write_text(
        'preset = "compact"\n[code]\ncode_size = 9\n[document]\nlabel = "C"\n', encoding="utf-8"
    )
    cfg, used = resolve(tmp_path, overrides={"label": "D"})
    assert used == tmp_path / CONFIG_FILENAME
    assert cfg.margin_left == 2.5      # from the compact preset
    assert cfg.code_size == 9          # file beats preset
    assert cfg.label == "D"            # CLI beats file
    cfg, _ = resolve(tmp_path, preset_name="us-letter")
    assert cfg.page_size == "Letter"   # explicit preset beats the file's preset


@pytest.mark.parametrize(
    "values, message",
    [
        ({"highlight": "rainbow"}, "must be one of"),
        ({"code_size": -1}, "positive number"),
        ({"line_numbers": "yes"}, "true or false"),
        ({"max_lines": 1.5}, "whole number"),
        ({"include": [1]}, "list of glob"),
        ({"code_sise": 9}, "did you mean 'code_size'"),
    ],
)
def test_validation(values, message):
    with pytest.raises(ConfigError, match=message):
        apply(Config(), values)


def test_choice_case_insensitive_and_string_list():
    cfg = apply(Config(), {"page_size": "letter", "exclude": "tests/"})
    assert cfg.page_size == "Letter" and cfg.exclude == ["tests/"]


def test_unknown_section_and_key():
    with pytest.raises(ConfigError, match="unknown section"):
        flatten_toml({"docs": {}}, "x.toml")
    with pytest.raises(ConfigError, match="unknown key 'font' in \\[code\\]"):
        flatten_toml({"code": {"font": "Arial"}}, "x.toml")


def test_unknown_theme(tmp_path):
    with pytest.raises(ConfigError, match="Unknown theme"):
        resolve(tmp_path, overrides={"theme": "no-such-theme"})


def test_invalid_toml(tmp_path):
    (tmp_path / CONFIG_FILENAME).write_text("[code\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid TOML"):
        resolve(tmp_path)


@pytest.mark.parametrize("preset", ["vn-thesis", "compact", "us-letter"])
def test_template_round_trips(preset, tmp_path):
    text = render_template(preset)
    data = tomllib.loads(text)
    name, flat = flatten_toml(data, "template")
    assert name == preset
    cfg = apply(resolve(tmp_path, preset_name=preset)[0], flat)
    assert cfg == resolve(tmp_path, preset_name=preset)[0]
