from unittest.mock import MagicMock, patch

import pytest

from app.services.httpx_runner import run_httpx


def test_retorna_resultados_jsonl():
    mock_result = MagicMock(
        returncode=0,
        stdout='{"url":"https://example.com","status_code":200,"title":"Home"}\n',
        stderr="",
    )

    with patch("subprocess.run", return_value=mock_result) as run:
        result = run_httpx("example.com")

    assert result == [{"url": "https://example.com", "status_code": 200, "title": "Home"}]
    run.assert_called_once()
    assert run.call_args.args[0][:3] == ["httpx", "-u", "example.com"]
    assert "-json" in run.call_args.args[0]


def test_ignora_linhas_vazias():
    mock_result = MagicMock(
        returncode=0,
        stdout='\n{"url":"https://example.com","status_code":200}\n  \n',
        stderr="",
    )

    with patch("subprocess.run", return_value=mock_result):
        result = run_httpx("example.com")

    assert result == [{"url": "https://example.com", "status_code": 200}]


def test_target_invalido_levanta_value_error():
    with pytest.raises(ValueError):
        run_httpx("https://bad target")


def test_subprocess_falha_levanta_runtime_error():
    mock_result = MagicMock(returncode=1, stdout="", stderr="failed")

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="httpx exited 1"):
            run_httpx("example.com")


def test_json_invalido_levanta_runtime_error():
    mock_result = MagicMock(returncode=0, stdout="not-json\n", stderr="")

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Invalid httpx JSON output"):
            run_httpx("example.com")


def test_subprocess_nao_usa_shell():
    mock_result = MagicMock(returncode=0, stdout="", stderr="")

    with patch("subprocess.run", return_value=mock_result) as run:
        run_httpx("example.com")

    _, kwargs = run.call_args
    assert kwargs.get("shell") is None
    assert isinstance(run.call_args.args[0], list)
