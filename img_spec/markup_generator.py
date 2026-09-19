"""
Responsive markup generator for ImgSpec.
Generates drop-in standards-compliant <picture> elements and calibrated sizes queries.
"""

import os
from typing import Dict, Any, List, Optional


def calculate_srcset_breakpoints(natural_w: int, max_w: int = 1600) -> List[int]:
    """Calculate logical srcset widths based on standard mobile and desktop responsive tiers."""
    standard_tiers = [360, 480, 720, 960, 1200, 1440, 1600, 1920]
    effective_max = min(natural_w if natural_w > 0 else max_w, max_w)

    breakpoints = [t for t in standard_tiers if t <= effective_max]
    if not breakpoints or breakpoints[-1] < effective_max:
        breakpoints.append(effective_max)

    # Ensure at least mobile and desktop breakpoints exist
    if 360 not in breakpoints:
        breakpoints.insert(0, 360)

    return sorted(list(set(breakpoints)))


def generate_sizes_query(rendered_w: int, is_full_width: bool = False) -> str:
    """Generate accurate sizes media queries to prevent mobile devices from downloading desktop assets."""
    if is_full_width or rendered_w >= 1100:
        return "(max-width: 640px) 100vw, (max-width: 1024px) 90vw, 1200px"
    elif rendered_w >= 600:
        return f"(max-width: 640px) 100vw, (max-width: 1024px) 60vw, {rendered_w}px"
    else:
        return f"(max-width: 640px) 50vw, {rendered_w}px"


def generate_responsive_picture_markup(
    img_data: Dict[str, Any],
    is_lcp: bool = True,
    alt_override: Optional[str] = None,
) -> str:
    """
    Generate drop-in responsive <picture> markup with AVIF/WebP sources,
    calibrated srcset widths, and Core Web Vitals priority attributes.
    """
    raw_src = img_data.get("src") or img_data.get("current_src", "/image.jpg")
    alt_text = alt_override or img_data.get("alt") or "Descriptive keyword-rich image description"

    # Base path without extension
    base_path, _ = os.path.splitext(raw_src)
    if not base_path:
        base_path = "/images/hero"

    nat_w = img_data.get("natural_width") or int(img_data.get("width_attr") or 1200)
    nat_h = img_data.get("natural_height") or int(img_data.get("height_attr") or 675)
    ren_w = img_data.get("rendered_width") or 800

    breakpoints = calculate_srcset_breakpoints(nat_w)
    sizes_query = generate_sizes_query(ren_w, is_full_width=(ren_w >= 900))

    # Build AVIF srcset
    avif_srcset = ", ".join(f"{base_path}-{w}.avif {w}w" for w in breakpoints)
    # Build WebP srcset
    webp_srcset = ", ".join(f"{base_path}-{w}.webp {w}w" for w in breakpoints)

    # Core Web Vitals attributes
    priority_attr = 'fetchpriority="high"' if is_lcp else 'fetchpriority="low"'
    loading_attr = 'loading="eager"' if is_lcp else 'loading="lazy"'

    markup = f"""<picture>
  <!-- Next-Gen AVIF: 50% smaller than JPEG at identical visual fidelity -->
  <source
    type="image/avif"
    srcset="{avif_srcset}"
    sizes="{sizes_query}"
  />
  <!-- Next-Gen WebP: Broad fallback for modern mobile and desktop browsers -->
  <source
    type="image/webp"
    srcset="{webp_srcset}"
    sizes="{sizes_query}"
  />
  <!-- Standard fallback img with strict layout geometry to eliminate CLS -->
  <img
    src="{raw_src}"
    alt="{alt_text}"
    width="{nat_w}"
    height="{nat_h}"
    {priority_attr}
    {loading_attr}
    decoding="async"
  />
</picture>"""
    return markup
