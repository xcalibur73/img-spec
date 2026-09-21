"""
Browser discovery and Chrome DevTools Protocol (CDP) controller for ImgSpec.
"""

import asyncio
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.request
from typing import Dict, Any, Optional, List
import websockets

from img_spec.devices import DeviceViewport

CANDIDATE_BROWSER_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "brave-browser",
]


def find_browser_executable() -> Optional[str]:
    """Find a local Chromium-based browser executable."""
    for path in CANDIDATE_BROWSER_PATHS:
        if os.path.isabs(path):
            if os.path.exists(path) and os.path.isfile(path):
                return path
        else:
            resolved = shutil.which(path)
            if resolved:
                return resolved
    return None


def find_free_port(start_port: int = 9550) -> int:
    """Find an unbound local port for Chrome remote debugging."""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


class CDPClient:
    """Lightweight Chrome DevTools Protocol WebSocket client."""

    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self._msg_id = 0

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=20 * 1024 * 1024)

    async def send(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._msg_id += 1
        msg = {"id": self._msg_id, "method": method, "params": params or {}}
        await self.ws.send(json.dumps(msg))

        while True:
            raw = await self.ws.recv()
            resp = json.loads(raw)
            if resp.get("id") == self._msg_id:
                if "error" in resp:
                    raise RuntimeError(f"CDP error on {method}: {resp['error']}")
                return resp.get("result", {})

    async def close(self):
        if self.ws:
            await self.ws.close()


class ChromeRunner:
    """Manages a headless Chromium process for multi-viewport image inspections."""

    def __init__(self, browser_path: Optional[str] = None):
        self.browser_path = browser_path or find_browser_executable()
        self.proc: Optional[subprocess.Popen] = None
        self.port: Optional[int] = None
        self.user_data_dir: Optional[str] = None

    def start(self, port: Optional[int] = None):
        if not self.browser_path:
            raise RuntimeError("No Chromium browser executable found on system.")

        self.port = port or find_free_port()
        self.user_data_dir = os.path.join(
            os.environ.get("TEMP", "/tmp"), f"imgspec_chrome_{self.port}_{int(time.time())}"
        )
        os.makedirs(self.user_data_dir, exist_ok=True)

        cmd = [
            self.browser_path,
            "--headless=new",
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-translate",
            "--hide-scrollbars",
            "--disable-gpu",
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "about:blank",
        ]

        self.proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        for _ in range(40):
            time.sleep(0.1)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/version", timeout=1) as resp:
                    if resp.status == 200:
                        return
            except Exception:
                continue

        self.stop()
        raise TimeoutError("Timed out waiting for Chromium remote debugging endpoint to become ready.")

    def get_tab_ws_url(self) -> str:
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/list", timeout=2) as resp:
            tabs = json.loads(resp.read().decode())
            for t in tabs:
                if t.get("type") == "page" and "webSocketDebuggerUrl" in t:
                    return t["webSocketDebuggerUrl"]
        raise RuntimeError("No open tab found in Chromium process.")

    def stop(self):
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=2)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None

        if self.user_data_dir and os.path.exists(self.user_data_dir):
            try:
                shutil.rmtree(self.user_data_dir, ignore_errors=True)
            except Exception:
                pass


IMAGE_EXTRACTION_SCRIPT = """
(() => {
    const images = [];
    const elements = Array.from(document.querySelectorAll('img, picture img'));
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    elements.forEach((el, index) => {
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);

        // Check visibility
        const isVisible = style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
        const isAboveFold = rect.top < vh && rect.bottom > 0 && rect.left < vw && rect.right > 0;
        const paintArea = Math.max(0, rect.width) * Math.max(0, rect.height);

        // Source resolution
        const currentSrc = el.currentSrc || el.src || '';
        const rawSrc = el.getAttribute('src') || '';
        const srcset = el.getAttribute('srcset') || '';
        const sizes = el.getAttribute('sizes') || '';

        // Check if inside picture
        const pictureEl = el.closest('picture');
        const pictureSources = [];
        if (pictureEl) {
            pictureEl.querySelectorAll('source').forEach(s => {
                pictureSources.push({
                    type: s.getAttribute('type') || '',
                    srcset: s.getAttribute('srcset') || '',
                    sizes: s.getAttribute('sizes') || '',
                    media: s.getAttribute('media') || ''
                });
            });
        }

        images.push({
            index: index + 1,
            src: rawSrc,
            current_src: currentSrc,
            alt: el.getAttribute('alt') || '',
            loading: el.getAttribute('loading') || 'eager',
            fetchpriority: el.getAttribute('fetchpriority') || 'auto',
            decoding: el.getAttribute('decoding') || 'auto',
            width_attr: el.getAttribute('width'),
            height_attr: el.getAttribute('height'),
            has_explicit_dimensions: Boolean(el.getAttribute('width') && el.getAttribute('height')),
            natural_width: el.naturalWidth || 0,
            natural_height: el.naturalHeight || 0,
            rendered_width: Math.round(rect.width),
            rendered_height: Math.round(rect.height),
            is_visible: isVisible,
            is_above_the_fold: isAboveFold,
            paint_area: Math.round(paintArea),
            srcset: srcset,
            sizes: sizes,
            is_picture_child: Boolean(pictureEl),
            picture_sources: pictureSources
        });
    });

    return images;
})()
"""
