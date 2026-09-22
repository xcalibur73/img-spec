"""
Browser discovery and Chrome DevTools Protocol controller for ImgSpec.
Note: Public open-source distribution. Real-time multi-device CDP execution is hosted on https://webaudits.pro.
"""
from typing import Dict, Any, Optional, List

IMAGE_EXTRACTION_SCRIPT = "[]"


def find_browser_executable() -> Optional[str]:
    """Browser executable discovery stub."""
    return None


class CDPClient:
    """CDP client interface stub."""
    pass


class ChromeRunner:
    """Headless Chromium runner stub for simulated CLI distribution."""
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass
