import base64
from typing import Any

import requests
from playwright.sync_api import sync_playwright

from app.core.validation import validate_target_value

HTTP_TIMEOUT = 15
BROWSER_WAIT_MS = 4000


def _check_headers(url: str) -> tuple[bool, str, str]:
    try:
        resp = requests.get(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
        xfo = resp.headers.get("X-Frame-Options", "")
        csp = resp.headers.get("Content-Security-Policy", "")
        frame_ancestors = next(
            (d.strip() for d in csp.split(";") if "frame-ancestors" in d.lower()), ""
        )
        return bool(xfo) or bool(frame_ancestors), xfo, frame_ancestors
    except Exception:
        return False, "", ""


def _build_html(url: str, vulnerable: bool) -> str:
    color = "#e94560" if vulnerable else "#00b894"
    label = "VULNERAVEL — iframe carregou" if vulnerable else "PROTEGIDO — iframe bloqueado"
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0d1117; font-family: monospace; padding: 24px; }}
    .url {{ color: #58a6ff; font-size: 13px; margin-bottom: 8px; }}
    .badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px;
              background: {color}22; color: {color};
              border: 1px solid {color}; font-size: 12px; font-weight: bold; margin-bottom: 14px; }}
    .frame-wrap {{ border: 2px solid {color}; border-radius: 4px; overflow: hidden; }}
    iframe {{ width: 860px; height: 480px; display: block; border: none; }}
  </style>
</head>
<body>
  <div class="url">Clickjacking Test — {url}</div>
  <div class="badge">{label}</div>
  <div class="frame-wrap">
    <iframe src="{url}"></iframe>
  </div>
</body>
</html>"""


def run_clickjacking(target: str) -> list[dict[str, Any]]:
    validate_target_value(target)
    url = target if target.startswith("http") else f"https://{target}"
    protected, xfo, frame_ancestors = _check_headers(url)
    vulnerable = not protected

    screenshot_b64: str | None = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            page = browser.new_page(viewport={"width": 908, "height": 640})
            page.set_content(_build_html(url, vulnerable))
            page.wait_for_timeout(BROWSER_WAIT_MS)
            png = page.screenshot(full_page=True)
            browser.close()
        screenshot_b64 = base64.b64encode(png).decode()
    except Exception:
        pass

    return [{
        "url": url,
        "vulnerable": vulnerable,
        "x_frame_options": xfo or None,
        "csp_frame_ancestors": frame_ancestors or None,
        "screenshot_b64": screenshot_b64,
    }]
