import subprocess
from unittest.mock import MagicMock, patch

import pytest

from app.services.subfinder_runner import run_subfinder


def _mock_run(stdout: str, returncode: int = 0) -> MagicMock:
    m = MagicMock()
    m.stdout = stdout
    m.stderr = ""
    m.returncode = returncode
    return m


@patch("app.services.subfinder_runner.subprocess.run")
def test_retorna_lista_de_subdominios(mock_run):
    mock_run.return_value = _mock_run("sub1.example.com\nsub2.example.com\n")
    result = run_subfinder("example.com")
    assert result == ["sub1.example.com", "sub2.example.com"]


@patch("app.services.subfinder_runner.subprocess.run")
def test_ignora_linhas_vazias(mock_run):
    mock_run.return_value = _mock_run("sub1.example.com\n\n   \nsub2.example.com\n")
    result = run_subfinder("example.com")
    assert result == ["sub1.example.com", "sub2.example.com"]


@patch("app.services.subfinder_runner.subprocess.run")
def test_retorna_lista_vazia_sem_output(mock_run):
    mock_run.return_value = _mock_run("")
    result = run_subfinder("example.com")
    assert result == []


@pytest.mark.parametrize("domain", [
    "invalid domain",
    "-startwithdash.com",
    "a" * 254,
    "",
    "has spaces.com",
])
def test_dominio_invalido_levanta_value_error(domain):
    with pytest.raises(ValueError):
        run_subfinder(domain)


@patch("app.services.subfinder_runner.subprocess.run")
def test_subprocess_com_erro_levanta_runtime_error(mock_run):
    m = _mock_run("", returncode=1)
    m.stderr = "permission denied"
    mock_run.return_value = m
    with pytest.raises(RuntimeError, match="subfinder exited 1"):
        run_subfinder("example.com")


@patch("app.services.subfinder_runner.subprocess.run")
def test_subprocess_chamado_sem_shell(mock_run):
    mock_run.return_value = _mock_run("sub.example.com")
    run_subfinder("example.com")
    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert isinstance(cmd, list), "comando deve ser lista, nao string"
    assert kwargs.get("shell") is not True
    assert "subfinder" in cmd[0]
    assert "-d" in cmd
    assert "example.com" in cmd
