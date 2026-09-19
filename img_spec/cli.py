"""
ImgSpec CLI: Responsive Viewport Breakpoint & LCP Image Auditor.
"""

import argparse
import json
import sys

from img_spec.inspector import inspect_images
from img_spec.auditor import audit_images
from img_spec.report_generator import (
    print_terminal_report,
    export_markdown_report,
    export_json_report,
)


def run_audit(url: str, fast: bool = False, viewport: str = "iphone_se") -> dict:
    """Execute complete image audit pipeline on a URL."""
    inspection = inspect_images(url, force_http=fast, viewport_key=viewport)
    audit = audit_images(inspection)
    return audit


def main():
    from img_spec import __version__
    parser = argparse.ArgumentParser(
        prog="img-spec",
        description="ImgSpec: Responsive Viewport Breakpoint & LCP Image Auditor",
        epilog="Example: python run.py https://webaudits.pro",
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="Target URL to audit for image performance and LCP priority.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ImgSpec v{__version__}",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast HTTP-only analysis mode (skips Chromium headless browser).",
    )
    parser.add_argument(
        "--viewport",
        choices=["compact", "iphone_se", "iphone_standard", "tablet", "desktop"],
        default="iphone_se",
        help="Target viewport breakpoint to emulate (default: iphone_se 375px).",
    )
    parser.add_argument(
        "--output",
        choices=["terminal", "markdown", "json"],
        default="terminal",
        help="Output format (default: terminal).",
    )
    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Save report to file path.",
    )

    args = parser.parse_args()
    if not args.url:
        parser.print_help()
        return 0

    target_url = args.url.strip()
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = "https://" + target_url

    print(f"ImgSpec: Auditing images on {target_url} (viewport: {args.viewport})...")

    try:
        audit_result = run_audit(target_url, fast=args.fast, viewport=args.viewport)
    except Exception as e:
        print(f"[ERROR] Audit failed: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output == "terminal":
        print_terminal_report(audit_result)

    elif args.output == "markdown":
        md = export_markdown_report(audit_result)
        if args.save:
            with open(args.save, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"Markdown report saved to: {args.save}")
        else:
            print(md)

    elif args.output == "json":
        data = export_json_report(audit_result)
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        if args.save:
            with open(args.save, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"JSON report saved to: {args.save}")
        else:
            print(json_str)


if __name__ == "__main__":
    main()
