import pytest

from app.core.validation import (
    assert_public_target,
    is_public_target_allowed,
    validate_target_url_or_value,
    validate_target_value,
)


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


def test_assert_public_target_accepts_public_hostname_without_dns_resolution() -> None:
    assert_public_target("clavis.com.br", resolve_dns=False)


@pytest.mark.parametrize(
    "target",
    [
        "127.0.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.0.1",
        "169.254.169.254",
        "localhost",
        "metadata.google.internal",
    ],
)
def test_assert_public_target_rejects_internal_targets(target: str) -> None:
    with pytest.raises(ValueError):
        assert_public_target(target, resolve_dns=False)


def test_is_public_target_allowed_rejects_hostname_resolving_to_private_ip(monkeypatch) -> None:
    def fake_getaddrinfo(*args, **kwargs):
        return [(None, None, None, "", ("10.0.0.10", 0))]

    monkeypatch.setattr("socket.getaddrinfo", fake_getaddrinfo)

    assert is_public_target_allowed("private.example.com") is False
