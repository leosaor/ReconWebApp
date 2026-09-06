import pytest

from app.core.validation import validate_target_url_or_value, validate_target_value


def test_validate_target_value_accepts_hostname() -> None:
    assert validate_target_value("clavis.com.br") == "clavis.com.br"


def test_validate_target_value_rejects_url() -> None:
    with pytest.raises(ValueError):
        validate_target_value("https://clavis.com.br")


def test_validate_target_url_or_value_accepts_http_url() -> None:
    assert (
        validate_target_url_or_value("https://clavis.com.br")
        == "https://clavis.com.br"
    )


def test_validate_target_url_or_value_rejects_non_http_url() -> None:
    with pytest.raises(ValueError):
        validate_target_url_or_value("javascript:alert(1)")
