"""
Report Generator & Formatter for ImgSpec Image & LCP Audits.
Outputs terminal tables, Markdown documents, and JSON objects.
"""

import json
from typing import Dict, Any, List, Optional
from img_spec.markup_generator import generate_responsive_picture_markup

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.syntax import Syntax
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def print_terminal_report(audit_result: Dict[str, Any]) -> None:
    """Print complete image audit report to terminal."""
    if not HAS_RICH:
        _print_plain_report(audit_result)
        return

    console = Console()

    url = audit_result.get("url", "")
    score = audit_result.get("overall_score", 0.0)
    grade = audit_result.get("grade", "F")
    stats = audit_result.get("stats", {})
    lcp = audit_result.get("lcp_audit", {})

    score_color = "green" if score >= 80 else ("yellow" if score >= 55 else "red")

    header = Text()
    header.append("ImgSpec: Responsive Viewport Breakpoint & LCP Image Auditor\n", style="bold magenta")
    header.append(f"Target URL: {url}\n", style="bold white")
    header.append(f"Image Optimization Score: {score}/100 (Grade: {grade})\n", style=f"bold {score_color}")
    header.append(
        f"Mode: {audit_result.get('mode')} | Discovered Images: {audit_result.get('total_images')} | "
        f"Oversized: {stats.get('oversized_images')} | Avg Pixel Waste: {stats.get('average_byte_waste_percent')}%",
        style="dim",
    )

    console.print(Panel(header, border_style="magenta"))

    # Component Scores Table
    comp = audit_result.get("component_scores", {})
    comp_table = Table(title="Component Score Breakdown", show_header=True, header_style="bold cyan")
    comp_table.add_column("Component Dimension", style="white")
    comp_table.add_column("Weight", justify="center", style="dim")
    comp_table.add_column("Score", justify="center")

    for name, weight, key in [
        ("LCP Priority & Timing", "35%", "lcp_priority"),
        ("Byte Waste Efficiency", "25%", "byte_waste_efficiency"),
        ("Format Modernity (AVIF/WebP)", "20%", "format_modernity"),
        ("Layout Shift Protection (CLS)", "10%", "layout_shift_protection"),
        ("Responsive Srcset Coverage", "10%", "responsive_srcset_coverage"),
    ]:
        val = comp.get(key, 0.0)
        c = "green" if val >= 75 else ("yellow" if val >= 50 else "red")
        comp_table.add_row(name, weight, f"[{c}]{val}/100[/{c}]")

    console.print(comp_table)

    # LCP Candidate Status Panel
    if lcp.get("has_lcp_image"):
        lcp_text = Text()
        lcp_text.append("Largest Contentful Paint (LCP) Candidate\n", style="bold yellow")
        lcp_text.append(f"Asset: {lcp.get('src')}\n", style="white")
        lcp_text.append(f"Verdict: {lcp.get('verdict')} (LCP Score: {lcp.get('lcp_score')}/100)\n", style="bold")
        lcp_text.append(f"Loading: {lcp.get('loading')} | FetchPriority: {lcp.get('fetchpriority')} | Modern Format: {lcp.get('is_modern_format')}\n", style="dim")

        if lcp.get("defects"):
            lcp_text.append("\nDetected Priority Defects:\n", style="bold red")
            for d in lcp["defects"]:
                lcp_text.append(f" - {d}\n", style="red")

        console.print(Panel(lcp_text, border_style="yellow" if lcp.get("lcp_score") < 80 else "green"))

    # Image Breakdown Table
    img_audits = audit_result.get("image_audits", [])
    if img_audits:
        img_table = Table(title="Discovered Image Assets & Viewport Efficiency", show_header=True, header_style="bold cyan")
        img_table.add_column("#", justify="center", style="dim")
        img_table.add_column("Asset Source", style="white", max_width=40, overflow="ellipsis")
        img_table.add_column("Intrinsic", justify="center", style="dim")
        img_table.add_column("Rendered", justify="center", style="dim")
        img_table.add_column("Pixel Waste", justify="center")
        img_table.add_column("Format", justify="center")
        img_table.add_column("CLS Lock", justify="center")
        img_table.add_column("Role", justify="center")

        for img in img_audits[:15]:
            waste = img.get("waste_info", {})
            waste_pct = waste.get("pixel_waste_percent", 0.0)
            waste_str = f"[red]{waste_pct}%[/red]" if waste_pct >= 50 else (f"[yellow]{waste_pct}%[/yellow]" if waste_pct > 0 else "[green]0%[/green]")
            fmt_str = "[green]Modern[/green]" if img.get("has_modern_format") else "[yellow]Legacy[/yellow]"
            cls_str = "[green]Yes[/green]" if img.get("has_explicit_dimensions") else "[red]No[/red]"
            role_str = "[bold magenta]LCP HERO[/bold magenta]" if img.get("is_lcp") else "Content"

            img_table.add_row(
                str(img.get("index")),
                img.get("src", ""),
                img.get("natural_dimensions", "-"),
                img.get("rendered_dimensions", "-"),
                waste_str,
                fmt_str,
                cls_str,
                role_str,
            )

        console.print(img_table)

    # Generated Responsive Picture Markup for LCP Hero
    lcp_candidate = None
    for img in audit_result.get("image_audits", []):
        if img.get("is_lcp"):
            lcp_candidate = img
            break

    if lcp_candidate:
        console.print("\n[bold cyan]Recommended Drop-in Responsive Markup (Optimized for LCP & 0 CLS):[/bold cyan]")
        markup = generate_responsive_picture_markup(lcp_candidate, is_lcp=True)
        console.print(Syntax(markup, "html", theme="monokai", line_numbers=False))

    # Recommendations
    recs = audit_result.get("recommendations", [])
    if recs:
        rec_table = Table(title="Core Web Vitals Remediation Steps", show_header=True, header_style="bold green")
        rec_table.add_column("Priority", justify="center", style="dim")
        rec_table.add_column("Actionable Engineering Fix", style="white")
        for i, r in enumerate(recs, 1):
            rec_table.add_row(str(i), r)
        console.print(rec_table)

    console.print()


def _print_plain_report(audit_result: Dict[str, Any]) -> None:
    """Fallback plain text output when rich is not available."""
    print(f"\n=== ImgSpec: Responsive Viewport & LCP Image Audit ===")
    print(f"Target URL: {audit_result.get('url')}")
    print(f"Overall Image Optimization Score: {audit_result.get('overall_score')}/100 (Grade: {audit_result.get('grade')})")
    print(f"Total Discovered Images: {audit_result.get('total_images')}")
    print(f"Average Pixel Waste: {audit_result.get('stats', {}).get('average_byte_waste_percent')}%")

    lcp = audit_result.get("lcp_audit", {})
    if lcp.get("has_lcp_image"):
        print(f"\n--- LCP Candidate ---")
        print(f"Asset: {lcp.get('src')}")
        print(f"Score: {lcp.get('lcp_score')}/100 ({lcp.get('verdict')})")
        for d in lcp.get("defects", []):
            print(f"  * {d}")

    print("\n--- Top Recommendations ---")
    for r in audit_result.get("recommendations", []):
        print(f"  - {r}")
    print()


def export_markdown_report(audit_result: Dict[str, Any]) -> str:
    """Generate Markdown audit report string."""
    lines = []
    lines.append("# ImgSpec: Responsive Viewport Breakpoint & LCP Image Audit\n")
    lines.append(f"**Target URL**: {audit_result.get('url')}\n")
    lines.append(f"**Image Optimization Score**: {audit_result.get('overall_score')}/100 (Grade: {audit_result.get('grade')})\n")

    stats = audit_result.get("stats", {})
    lines.append(f"- Discovered Images: {audit_result.get('total_images')}")
    lines.append(f"- Oversized Images: {stats.get('oversized_images')}")
    lines.append(f"- Average Pixel Waste: {stats.get('average_byte_waste_percent')}%")
    lines.append(f"- Modern Formats (AVIF/WebP): {stats.get('modern_format_count')}/{audit_result.get('total_images')}")
    lines.append(f"- CLS Dimension Locks: {stats.get('explicit_dimensions_count')}/{audit_result.get('total_images')}\n")

    # Component Scores
    lines.append("---\n")
    lines.append("## Component Scores\n")
    lines.append("| Component | Weight | Score |")
    lines.append("|:---|:---:|:---:|")
    comp = audit_result.get("component_scores", {})
    for name, weight, key in [
        ("LCP Priority & Timing", "35%", "lcp_priority"),
        ("Byte Waste Efficiency", "25%", "byte_waste_efficiency"),
        ("Format Modernity", "20%", "format_modernity"),
        ("Layout Shift Protection", "10%", "layout_shift_protection"),
        ("Responsive Srcset Coverage", "10%", "responsive_srcset_coverage"),
    ]:
        lines.append(f"| {name} | {weight} | {comp.get(key, 0)}/100 |")

    # LCP Candidate
    lcp = audit_result.get("lcp_audit", {})
    if lcp.get("has_lcp_image"):
        lines.append("\n---\n")
        lines.append("## LCP Hero Candidate Evaluation\n")
        lines.append(f"- **Asset**: `{lcp.get('src')}`")
        lines.append(f"- **LCP Score**: {lcp.get('lcp_score')}/100")
        lines.append(f"- **Loading**: `{lcp.get('loading')}`")
        lines.append(f"- **FetchPriority**: `{lcp.get('fetchpriority')}`")
        lines.append(f"- **Modern Format**: {lcp.get('is_modern_format')}")

        if lcp.get("defects"):
            lines.append("\n### Priority Defects:")
            for d in lcp["defects"]:
                lines.append(f"- {d}")

    # Recommended Markup
    lcp_candidate = None
    for img in audit_result.get("image_audits", []):
        if img.get("is_lcp"):
            lcp_candidate = img
            break

    if lcp_candidate:
        lines.append("\n---\n")
        lines.append("## Recommended Drop-in Responsive Markup\n")
        lines.append("```html")
        lines.append(generate_responsive_picture_markup(lcp_candidate, is_lcp=True))
        lines.append("```\n")

    # Recommendations
    lines.append("\n---\n")
    lines.append("## Core Web Vitals Remediation Steps\n")
    for i, r in enumerate(audit_result.get("recommendations", []), 1):
        lines.append(f"{i}. {r}")

    lines.append("\n---\n")
    lines.append("*Generated by [ImgSpec](https://github.com/xcalibur73/img-spec) | [WebAudits.pro](https://webaudits.pro/tools/img-spec)*\n")

    return "\n".join(lines)


def export_json_report(audit_result: Dict[str, Any]) -> dict:
    """Build JSON-serializable audit report dict."""
    return {
        "tool": "ImgSpec",
        "version": "1.0.0",
        **audit_result,
    }
