from unittest.mock import MagicMock, patch

import pytest

from app.services.nmap_runner import run_nmap

_NMAP_XML = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <address addr="93.184.216.34" addrtype="ipv4"/>
    <hostnames>
      <hostname name="example.com" type="user"/>
    </hostnames>
    <ports>
      <port protocol="tcp" portid="80">
        <state state="open"/>
        <service name="http" product="nginx" version="1.24"/>
      </port>
      <port protocol="tcp" portid="443">
        <state state="open"/>
        <service name="https"/>
      </port>
    </ports>
  </host>
</nmaprun>
"""


def test_retorna_portas_do_xml():
    mock_result = MagicMock(returncode=0, stdout=_NMAP_XML, stderr="")

    with patch("subprocess.run", return_value=mock_result) as run:
        result = run_nmap("example.com")

    assert result == [
        {
            "host": "example.com",
            "port": 80,
            "protocol": "tcp",
            "state": "open",
            "service": "http",
            "product": "nginx",
            "version": "1.24",
        },
        {
            "host": "example.com",
            "port": 443,
            "protocol": "tcp",
            "state": "open",
            "service": "https",
            "product": None,
            "version": None,
        },
    ]
    run.assert_called_once_with(
        ["nmap", "-sT", "-sV", "-oX", "-", "example.com"],
        capture_output=True,
        text=True,
        timeout=1800,
    )


def test_usa_ip_quando_hostname_nao_existe():
    xml = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <address addr="127.0.0.1" addrtype="ipv4"/>
    <ports>
      <port protocol="tcp" portid="8000"><state state="open"/></port>
    </ports>
  </host>
</nmaprun>
"""
    mock_result = MagicMock(returncode=0, stdout=xml, stderr="")

    with patch("subprocess.run", return_value=mock_result):
        result = run_nmap("127.0.0.1")

    assert result[0]["host"] == "127.0.0.1"
    assert result[0]["port"] == 8000


def test_target_invalido_levanta_value_error():
    with pytest.raises(ValueError):
        run_nmap("https://example.com/path")


def test_subprocess_falha_levanta_runtime_error():
    mock_result = MagicMock(returncode=1, stdout="", stderr="failed")

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="nmap exited 1"):
            run_nmap("example.com")


def test_xml_invalido_levanta_runtime_error():
    mock_result = MagicMock(returncode=0, stdout="<not-xml", stderr="")

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Invalid nmap XML output"):
            run_nmap("example.com")


def test_subprocess_nao_usa_shell():
    mock_result = MagicMock(returncode=0, stdout="<nmaprun />", stderr="")

    with patch("subprocess.run", return_value=mock_result) as run:
        run_nmap("example.com")

    _, kwargs = run.call_args
    assert kwargs.get("shell") is None
    assert isinstance(run.call_args.args[0], list)
