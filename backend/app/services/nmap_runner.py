import re
import subprocess
import xml.etree.ElementTree as ET
from typing import Any

_TARGET_RE = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
    r"|^(\d{1,3}\.){3}\d{1,3}$"
)
NMAP_TIMEOUT = 1800


def _validate_target(target: str) -> None:
    if not _TARGET_RE.match(target) or len(target) > 253:
        raise ValueError(f"Invalid target: {target!r}")


def run_nmap(target: str | list[str]) -> list[dict[str, Any]]:
    targets = [target] if isinstance(target, str) else list(target)
    if not targets:
        return []
    for item in targets:
        _validate_target(item)
    result = subprocess.run(
        ["nmap", "-sT", "-sV", "-oX", "-", *targets],
        capture_output=True,
        text=True,
        timeout=NMAP_TIMEOUT,
    )
    if result.returncode != 0:
        raise RuntimeError(f"nmap exited {result.returncode}: {result.stderr[:200]}")
    return _parse_nmap_xml(result.stdout)


def _parse_nmap_xml(xml_output: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(xml_output)
    except ET.ParseError as exc:
        raise RuntimeError("Invalid nmap XML output") from exc

    results: list[dict[str, Any]] = []
    for host in root.findall("host"):
        host_value = _host_value(host)
        for port in host.findall("./ports/port"):
            state = port.find("state")
            service = port.find("service")
            item = {
                "host": host_value,
                "port": int(port.attrib["portid"]),
                "protocol": port.attrib.get("protocol"),
                "state": state.attrib.get("state") if state is not None else None,
                "service": service.attrib.get("name") if service is not None else None,
                "product": service.attrib.get("product") if service is not None else None,
                "version": service.attrib.get("version") if service is not None else None,
            }
            results.append(item)
    return results


def _host_value(host: ET.Element) -> str | None:
    hostname = host.find("./hostnames/hostname")
    if hostname is not None and hostname.attrib.get("name"):
        return hostname.attrib["name"]
    address = host.find("address")
    if address is not None:
        return address.attrib.get("addr")
    return None
