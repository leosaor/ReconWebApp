from unittest.mock import MagicMock, patch

import pytest

from app.services.feroxbuster_runner import run_feroxbuster


def _mock_run(returncode: int = 0, stderr: str = "") -> MagicMock:
    m = MagicMock()
    m.returncode = returncode
    m.stderr = stderr
    m.stdout = ""
    return m


@patch("app.services.feroxbuster_runner.subprocess.run")
def test_usa_http_200_txt_via_stdin_e_grava_saida_nativa(mock_run, tmp_path):
    input_file = tmp_path / "http-200.txt"
    output_file = tmp_path / "feroxbuster.txt"
    input_file.write_text("https://example.com\nhttps://api.example.com\n", encoding="utf-8")

    def run_side_effect(cmd, **kwargs):
        output_file.write_text(
            "200      GET        1l        2w        3c https://example.com/admin\n",
            encoding="utf-8",
        )
        return _mock_run()

    mock_run.side_effect = run_side_effect

    results = run_feroxbuster(input_file, output_file)

    command = mock_run.call_args.args[0]
    _, kwargs = mock_run.call_args
    assert command[:2] == ["feroxbuster", "--stdin"]
    assert "--no-state" in command
    assert "-a" in command
    assert "-w" in command
    assert "-s" in command
    assert command[command.index("-s") + 1] == "200"
    assert "-k" in command
    assert "-q" in command
    assert "-n" in command
    assert "-o" in command
    assert command[command.index("-o") + 1] == str(output_file)
    assert kwargs.get("shell") is None
    assert kwargs["stdin"].name == str(input_file)
    assert results == [
        {
            "url": "https://example.com/admin",
            "status_code": 200,
            "content_length": 3,
            "words": 2,
            "lines": 1,
            "redirect": None,
            "raw": {
                "url": "https://example.com/admin",
                "status_code": 200,
                "lines": 1,
                "words": 2,
                "content_length": 3,
                "raw": "200      GET        1l        2w        3c https://example.com/admin",
            },
        }
    ]


@patch("app.services.feroxbuster_runner.subprocess.run")
def test_subprocess_falha_sem_saida_levanta_runtime_error(mock_run, tmp_path):
    input_file = tmp_path / "http-200.txt"
    output_file = tmp_path / "feroxbuster.txt"
    input_file.write_text("https://example.com\n", encoding="utf-8")
    mock_run.return_value = _mock_run(returncode=2, stderr="missing output")

    with pytest.raises(RuntimeError, match="feroxbuster exited 2"):
        run_feroxbuster(input_file, output_file)
