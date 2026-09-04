import base64
import subprocess
from typing import Any

from rich.console import Console
from rich.text import Text

from app.core.validation import validate_target_value

DNS_TIMEOUT = 15


def _clean_domain(target: str) -> str:
    domain = target.removeprefix("https://").removeprefix("http://").split("/")[0]
    return domain.strip()


def _query_txt(domain: str) -> str:
    result = subprocess.run(
        ["host", "-t", "txt", domain],
        capture_output=True,
        text=True,
        timeout=DNS_TIMEOUT,
    )
    return (result.stdout + result.stderr).strip()


def _to_svg_b64(lines: list[tuple[str, str]], title: str) -> str:
    console = Console(record=True, width=100, force_terminal=True)
    text = Text()
    for content, style in lines:
        text.append(content + "\n", style=style)
    console.print(text)
    svg = console.export_svg(title=title)
    return base64.b64encode(svg.encode()).decode()


def run_domain_spoofing(target: str) -> list[dict[str, Any]]:
    validate_target_value(target)
    domain = _clean_domain(target)
    results: list[dict[str, Any]] = []

    # SPF
    spf_raw = _query_txt(domain)
    spf_found = any("v=spf1" in line.lower() for line in spf_raw.splitlines())
    spf_lines: list[tuple[str, str]] = [
        (f"# host -t txt {domain}", "bold cyan"),
        ("", ""),
    ]
    for line in spf_raw.splitlines():
        style = "green" if "v=spf1" in line.lower() else "white"
        spf_lines.append((line, style))
    spf_lines.append(("", ""))
    if spf_found:
        spf_lines.append(("[+] SPF record found", "bold green"))
    else:
        spf_lines.append(("[-] SPF record missing — domain may be spoofable", "bold red"))

    results.append({
        "check": "SPF",
        "domain": domain,
        "status": "found" if spf_found else "missing",
        "svg_b64": _to_svg_b64(spf_lines, f"SPF — {domain}"),
    })

    # DMARC
    dmarc_domain = f"_dmarc.{domain}"
    dmarc_raw = _query_txt(dmarc_domain)
    dmarc_found = any("v=dmarc1" in line.lower() for line in dmarc_raw.splitlines())
    dmarc_lines: list[tuple[str, str]] = [
        (f"# host -t txt {dmarc_domain}", "bold cyan"),
        ("", ""),
    ]
    for line in dmarc_raw.splitlines():
        style = "green" if "v=dmarc1" in line.lower() else "white"
        dmarc_lines.append((line, style))
    dmarc_lines.append(("", ""))
    if dmarc_found:
        dmarc_lines.append(("[+] DMARC record found", "bold green"))
    else:
        dmarc_lines.append(("[-] DMARC record missing — no DMARC policy", "bold red"))

    results.append({
        "check": "DMARC",
        "domain": dmarc_domain,
        "status": "found" if dmarc_found else "missing",
        "svg_b64": _to_svg_b64(dmarc_lines, f"DMARC — {dmarc_domain}"),
    })

    return results
