"""
Image DOM inspector and LCP candidate detection for ImgSpec.
Supports both Chrome CDP emulation and fast HTTP parsing.
"""

import asyncio
import json
import re
import urllib.parse
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup

from img_spec.devices import DeviceViewport, get_all_viewports, get_viewport
from img_spec.browser import ChromeRunner, CDPClient, IMAGE_EXTRACTION_SCRIPT, find_browser_executable


def is_modern_format(url_or_mime: str) -> bool:
    """Check if image uses modern AVIF, WebP, SVG format, or auto-format image CDN."""
    lower = url_or_mime.lower()
    return (
        "image/avif" in lower
        or "image/webp" in lower
        or "image/svg" in lower
        or lower.endswith(".avif")
        or lower.endswith(".webp")
        or lower.endswith(".svg")
        or ".avif?" in lower
        or ".webp?" in lower
        or ".svg?" in lower
        or "/_next/image" in lower
        or "res.cloudinary.com" in lower
        or "cloudinary" in lower
        or ".imgix.net" in lower
        or "images.unsplash.com" in lower
        or "cdn-cgi/image/" in lower
        or ".imagekit.io" in lower
        or ".twicpics.com" in lower
        or "f_auto" in lower
        or "auto=format" in lower
        or "format=webp" in lower
        or "format=avif" in lower
        or "fm=webp" in lower
        or "fm=avif" in lower
        or "output=webp" in lower
        or "shopify.com" in lower
        or "wixstatic.com" in lower
    )


def inspect_via_http(url: str, timeout: int = 15) -> Dict[str, Any]:
    """Fallback inspection mode: parses raw HTML via HTTP without Chromium."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    html = resp.text

    soup = BeautifulSoup(html, "html.parser")
    img_tags = soup.find_all("img")

    images = []
    lcp_candidate = None
    max_area = 0

    for idx, el in enumerate(img_tags, 1):
        src = el.get("src", "")
        if not src:
            src = el.get("data-src", "")
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = urllib.parse.urljoin(url, src)

        srcset = el.get("srcset", "")
        sizes = el.get("sizes", "")
        loading = el.get("loading", "eager").lower()
        fetchpriority = el.get("fetchpriority", "auto").lower()
        decoding = el.get("decoding", "auto").lower()
        width_attr = el.get("width")
        height_attr = el.get("height")

        # Estimate area if dimensions present
        w = int(width_attr) if width_attr and width_attr.isdigit() else 800
        h = int(height_attr) if height_attr and height_attr.isdigit() else 450
        est_area = w * h

        # Detect picture wrapper
        parent_picture = el.find_parent("picture")
        picture_sources = []
        if parent_picture:
            for s in parent_picture.find_all("source"):
                picture_sources.append({
                    "type": s.get("type", ""),
                    "srcset": s.get("srcset", ""),
                    "sizes": s.get("sizes", ""),
                    "media": s.get("media", ""),
                })

        img_data = {
            "index": idx,
            "src": src,
            "current_src": src,
            "alt": el.get("alt", ""),
            "loading": loading,
            "fetchpriority": fetchpriority,
            "decoding": decoding,
            "width_attr": width_attr,
            "height_attr": height_attr,
            "has_explicit_dimensions": bool(width_attr and height_attr),
            "natural_width": w,
            "natural_height": h,
            "rendered_width": min(w, 1200),
            "rendered_height": min(h, 675),
            "is_visible": True,
            "is_above_the_fold": idx <= 2,
            "paint_area": est_area,
            "srcset": srcset,
            "sizes": sizes,
            "is_picture_child": bool(parent_picture),
            "picture_sources": picture_sources,
        }

        images.append(img_data)

        # First substantial above-fold image treated as LCP
        if idx == 1 or (img_data["is_above_the_fold"] and est_area > max_area):
            lcp_candidate = img_data
            max_area = est_area

    return {
        "mode": "http_static",
        "url": url,
        "viewport": "default (HTTP)",
        "total_images": len(images),
        "images": images,
        "lcp_candidate": lcp_candidate,
        "viewports_evaluated": ["http_static"],
    }


async def _inspect_viewport_cdp(
    ws_url: str,
    url: str,
    viewport: DeviceViewport,
    timeout: int = 15,
) -> Dict[str, Any]:
    """Emulate a single viewport via CDP and extract image telemetry."""
    client = CDPClient(ws_url)
    await client.connect()

    try:
        # 1. Enable needed domains
        await client.send("Page.enable")
        await client.send("DOM.enable")
        await client.send("CSS.enable")
        await client.send("Network.enable")

        # 2. Set Device Metrics Override
        await client.send("Emulation.setDeviceMetricsOverride", {
            "width": viewport.width,
            "height": viewport.height,
            "deviceScaleFactor": viewport.device_pixel_ratio,
            "mobile": viewport.is_mobile,
        })

        # 3. Set User Agent
        await client.send("Network.setUserAgentOverride", {
            "userAgent": viewport.user_agent,
        })

        # 4. Navigate
        nav_res = await client.send("Page.navigate", {"url": url})

        # 5. Wait for load event
        await asyncio.sleep(2.5)

        # 6. Execute extraction script
        eval_res = await client.send("Runtime.evaluate", {
            "expression": IMAGE_EXTRACTION_SCRIPT,
            "returnByValue": True,
            "awaitPromise": True,
        })

        extracted_images = eval_res.get("result", {}).get("value", [])

        # Find LCP candidate: visible above-fold image with maximum paint area
        lcp_candidate = None
        max_area = -1

        for img in extracted_images:
            if img.get("is_visible") and img.get("is_above_the_fold"):
                area = img.get("paint_area", 0)
                if area > max_area:
                    max_area = area
                    lcp_candidate = img

        return {
            "viewport_id": viewport.id,
            "viewport_name": viewport.name,
            "width": viewport.width,
            "height": viewport.height,
            "dpr": viewport.device_pixel_ratio,
            "images": extracted_images,
            "lcp_candidate": lcp_candidate,
            "total_images": len(extracted_images),
        }

    finally:
        await client.close()


def inspect_via_cdp(
    url: str,
    viewports: Optional[List[DeviceViewport]] = None,
    timeout: int = 20,
) -> Dict[str, Any]:
    """Full CDP multi-viewport image inspection."""
    runner = ChromeRunner()
    runner.start()

    targets = viewports or get_all_viewports()
    results = {}

    try:
        ws_url = runner.get_tab_ws_url()

        for vp in targets:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                vp_result = loop.run_until_complete(
                    _inspect_viewport_cdp(ws_url, url, vp, timeout=timeout)
                )
                results[vp.id] = vp_result
            finally:
                loop.close()

        # Primary viewport for main summary is iphone_se (375px)
        primary_key = "iphone_se" if "iphone_se" in results else list(results.keys())[0]
        primary = results[primary_key]

        return {
            "mode": "cdp_multi_viewport",
            "url": url,
            "primary_viewport": primary_key,
            "total_images": primary["total_images"],
            "images": primary["images"],
            "lcp_candidate": primary["lcp_candidate"],
            "viewport_breakdowns": results,
            "viewports_evaluated": [vp.id for vp in targets],
        }

    finally:
        runner.stop()


def inspect_images(url: str, force_http: bool = False, viewport_key: Optional[str] = None) -> Dict[str, Any]:
    """Main inspection orchestrator: prefers CDP if browser is present and force_http is False."""
    has_browser = bool(find_browser_executable())

    if force_http or not has_browser:
        return inspect_via_http(url)

    if viewport_key:
        vps = [get_viewport(viewport_key)]
    else:
        vps = get_all_viewports()

    try:
        return inspect_via_cdp(url, viewports=vps)
    except Exception as e:
        # Fallback to HTTP on CDP failure
        print(f"[WARN] Chromium CDP inspection failed ({e}), falling back to HTTP parsing.")
        return inspect_via_http(url)
