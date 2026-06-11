from unittest.mock import MagicMock, patch

import pytest

from app.services.nmap_runner import run_nmap

_XML_TWO_PORTS = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <hostnames><hostname name="example.com" type="user"/></hostnames>
    <address addr="93.184.216.34" addrtype="ipv4"/>
    <ports>
      <port protocol="tcp" portid="80">
        <state state="open"/>
        <service name="http" product="nginx" version="1.24.0"/>
      </port>
      <port protocol="tcp" portid="443">
        <state state="open"/>
        <service name="https" product="nginx" version="1.24.0"/>
      </port>
    </ports>
  </host>
</nmaprun>"""

_XML_EMPTY = """<?xml version="1.0"?><nmaprun></nmaprun>"""

_XML_NO_HOSTNAME = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <address addr="10.0.0.1" addrtype="ipv4"/>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh"/>
      </port>
    </ports>
  </host>
</nmaprun>"""


def _mock_run(stdout: str, returncode: int = 0) -> MagicMock:
    m = MagicMock()
    m.stdout = stdout
    m.stderr = ""
    m.returncode = returncode
    return m


@patch("app.services.nmap_runner.subprocess.run")
def test_retorna_lista_de_portas(mock_run):
    mock_run.return_value = _mock_run(_XML_TWO_PORTS)
    result = run_nmap("example.com")
    assert len(result) == 2
    ports = {r["port"] for r in result}
    assert ports == {80, 443}


@patch("app.services.nmap_runner.subprocess.run")
def test_resultado_contem_campos_esperados(mock_run):
    mock_run.return_value = _mock_run(_XML_TWO_PORTS)
    result = run_nmap("example.com")
    port80 = next(r for r in result if r["port"] == 80)
    assert port80["host"] == "example.com"
    assert port80["protocol"] == "tcp"
    assert port80["state"] == "open"
    assert port80["service"] == "http"
    assert port80["product"] == "nginx"
    assert port80["version"] == "1.24.0"


@patch("app.services.nmap_runner.subprocess.run")
def test_host_sem_hostname_usa_ip(mock_run):
    mock_run.return_value = _mock_run(_XML_NO_HOSTNAME)
    result = run_nmap("10.0.0.1")
    assert result[0]["host"] == "10.0.0.1"
    assert result[0]["port"] == 22


@patch("app.services.nmap_runner.subprocess.run")
def test_retorna_lista_vazia_sem_hosts(mock_run):
    mock_run.return_value = _mock_run(_XML_EMPTY)
    result = run_nmap("example.com")
    assert result == []


@pytest.mark.parametrize("target", [
    "invalid target",
    "-startwithdash.com",
    "a" * 254,
    "",
    "has spaces.com",
])
def test_target_invalido_levanta_value_error(target):
    with pytest.raises(ValueError):
        run_nmap(target)


@patch("app.services.nmap_runner.subprocess.run")
def test_subprocess_com_erro_levanta_runtime_error(mock_run):
    m = _mock_run("", returncode=1)
    m.stderr = "permission denied"
    mock_run.return_value = m
    with pytest.raises(RuntimeError, match="nmap exited 1"):
        run_nmap("example.com")


@patch("app.services.nmap_runner.subprocess.run")
def test_xml_invalido_levanta_runtime_error(mock_run):
    mock_run.return_value = _mock_run("not xml at all")
    with pytest.raises(RuntimeError, match="Invalid nmap XML"):
        run_nmap("example.com")


@patch("app.services.nmap_runner.subprocess.run")
def test_subprocess_chamado_sem_shell(mock_run):
    mock_run.return_value = _mock_run(_XML_EMPTY)
    run_nmap("example.com")
    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert isinstance(cmd, list), "comando deve ser lista, nao string"
    assert kwargs.get("shell") is not True
    assert "nmap" in cmd[0]
    assert "example.com" in cmd


@patch("app.services.nmap_runner.subprocess.run")
def test_aceita_ip_como_target(mock_run):
    mock_run.return_value = _mock_run(_XML_EMPTY)
    result = run_nmap("192.168.1.1")
    assert result == []


@patch("app.services.nmap_runner.subprocess.run")
def test_usa_input_file_quando_solicitado(mock_run):
    mock_run.return_value = _mock_run(_XML_EMPTY)
    result = run_nmap(["example.com", "api.example.com"], use_input_file=True)
    assert result == []

    args, _ = mock_run.call_args
    cmd = args[0]
    assert "-iL" in cmd
    assert cmd[cmd.index("-iL") + 1].endswith(".txt")
    assert "example.com" not in cmd
