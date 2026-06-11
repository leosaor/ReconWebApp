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
    command = run.call_args.args[0]
    assert command[:3] == ["httpx", "-l", command[2]]
    assert "-json" in run.call_args.args[0]


def test_aceita_lista_de_targets_via_arquivo_temporario():
    mock_result = MagicMock(
        returncode=0,
        stdout='{"url":"https://api.example.com","status_code":200}\n',
        stderr="",
    )

    with patch("subprocess.run", return_value=mock_result) as run:
        result = run_httpx(["example.com", "api.example.com"])

    assert result == [{"url": "https://api.example.com", "status_code": 200}]
    command = run.call_args.args[0]
    assert command[:2] == ["httpx", "-l"]
    assert command[2].endswith(".txt")


def test_aceita_subdominio_com_underscore():
    mock_result = MagicMock(
        returncode=0,
        stdout='{"url":"https://iconapi_elb.dbt.svs.nike.com","status_code":200}\n',
        stderr="",
    )

    with patch("subprocess.run", return_value=mock_result) as run:
        result = run_httpx("iconapi_elb.dbt.svs.nike.com")

    assert result == [{"url": "https://iconapi_elb.dbt.svs.nike.com", "status_code": 200}]
    command = run.call_args.args[0]
    assert command[:2] == ["httpx", "-l"]


def test_remove_targets_duplicados_preservando_ordem():
    mock_result = MagicMock(returncode=0, stdout="", stderr="")

    with patch("subprocess.run", return_value=mock_result) as run:
        run_httpx(["example.com", "EXAMPLE.com", "api.example.com"])

    command = run.call_args.args[0]
    assert command[:2] == ["httpx", "-l"]


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


def test_match_code_200_sem_follow_redirects_por_padrao():
    mock_result = MagicMock(
        returncode=0,
        stdout='{"url":"https://example.com","status_code":200}\n',
        stderr="",
    )

    with patch("subprocess.run", return_value=mock_result) as run:
        run_httpx("example.com", match_code="200")

    command = run.call_args.args[0]
    assert "-fr" not in command
    assert "-mc" in command
    assert command[command.index("-mc") + 1] == "200"


def test_follow_redirects_quando_solicitado():
    mock_result = MagicMock(returncode=0, stdout="", stderr="")

    with patch("subprocess.run", return_value=mock_result) as run:
        run_httpx("example.com", follow_redirects=True)

    command = run.call_args.args[0]
    assert "-fr" in command
