from pathlib import Path

from coloured_drawings.utils import make_output_dir, slugify


def test_slugify_removes_accents_and_symbols():
    assert slugify("Aladino da Disney!") == "aladino-da-disney"
    assert slugify("Sereia & Príncipe") == "sereia-principe"


def test_slugify_empty_falls_back():
    assert slugify("???") == "desenho"


def test_make_output_dir_is_unique_per_call(tmp_path: Path):
    d = make_output_dir(tmp_path, "gato")
    assert d.exists()
    assert d.name.startswith("gato-")
