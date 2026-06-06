from unittest.mock import MagicMock, patch

import pytest

from app.services.subfinder_runner import run_subfinder


def test_retorna_lista_de_subdominios():
    mock_result = MagicMock(
        returncode=0,
        stdout="api.example.com\nmail.example.com\n",
        stderr="",
    )

    with patch("subprocess.run", return_value=mock_result) as run:
        result = run_subfinder("example.com")

    assert result == ["api.example.com", "mail.example.com"]
    run.assert_called_once_with(
        ["subfinder", "-d", "example.com", "-silent"],
        capture_output=True,
        text=True,
        timeout=300,
    )


def test_ignora_linhas_vazias():
    mock_result = MagicMock(returncode=0, stdout="api.example.com\n\n  \n", stderr="")

    with patch("subprocess.run", return_value=mock_result):
        result = run_subfinder("example.com")

    assert result == ["api.example.com"]


def test_dominio_invalido_levanta_value_error():
    with pytest.raises(ValueError):
        run_subfinder("not a domain!")


def test_subprocess_falha_levanta_runtime_error():
    mock_result = MagicMock(returncode=1, stdout="", stderr="failed")

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="subfinder exited 1"):
            run_subfinder("example.com")


def test_subprocess_nao_usa_shell():
    mock_result = MagicMock(returncode=0, stdout="", stderr="")

    with patch("subprocess.run", return_value=mock_result) as run:
        run_subfinder("example.com")

    _, kwargs = run.call_args
    assert kwargs.get("shell") is None
    assert isinstance(run.call_args.args[0], list)
