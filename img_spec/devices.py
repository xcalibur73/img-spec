"""
Device definitions and responsive viewport configurations for ImgSpec.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class DeviceViewport:
    id: str
    name: str
    width: int
    height: int
    device_pixel_ratio: float
    user_agent: str
    is_mobile: bool


CHROME_MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
)

CHROME_DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

STANDARD_VIEWPORTS: Dict[str, DeviceViewport] = {
    "compact": DeviceViewport(
        id="compact",
        name="Compact Mobile (iPhone 5/SE Legacy)",
        width=320,
        height=568,
        device_pixel_ratio=2.0,
        user_agent=CHROME_MOBILE_UA,
        is_mobile=True,
    ),
    "iphone_se": DeviceViewport(
        id="iphone_se",
        name="iPhone SE (2nd/3rd Gen)",
        width=375,
        height=667,
        device_pixel_ratio=2.0,
        user_agent=CHROME_MOBILE_UA,
        is_mobile=True,
    ),
    "iphone_standard": DeviceViewport(
        id="iphone_standard",
        name="iPhone 14 / 15 Standard",
        width=390,
        height=844,
        device_pixel_ratio=3.0,
        user_agent=CHROME_MOBILE_UA,
        is_mobile=True,
    ),
    "tablet": DeviceViewport(
        id="tablet",
        name="Tablet (iPad Mini / Air)",
        width=768,
        height=1024,
        device_pixel_ratio=2.0,
        user_agent=CHROME_MOBILE_UA,
        is_mobile=False,
    ),
    "desktop": DeviceViewport(
        id="desktop",
        name="Desktop (Standard Display)",
        width=1440,
        height=900,
        device_pixel_ratio=1.0,
        user_agent=CHROME_DESKTOP_UA,
        is_mobile=False,
    ),
}


def get_viewport(key: str) -> DeviceViewport:
    """Retrieve viewport by identifier, defaulting to iphone_se."""
    return STANDARD_VIEWPORTS.get(key, STANDARD_VIEWPORTS["iphone_se"])


def get_all_viewports() -> List[DeviceViewport]:
    """Retrieve list of all 5 standard viewports."""
    return list(STANDARD_VIEWPORTS.values())
