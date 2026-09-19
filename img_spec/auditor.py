"""
Core image performance, byte waste, and LCP priority auditing engine for ImgSpec.
"""

from typing import Dict, Any, List, Optional
from img_spec.inspector import is_modern_format


def calculate_byte_waste(natural_w: int, natural_h: int, rendered_w: int, rendered_h: int, dpr: float = 2.0) -> Dict[str, Any]:
    """
    Calculate wasted pixel data between intrinsic downloaded dimensions and rendered display area.
    Formula:
      effective_display_pixels = rendered_w * rendered_h * (dpr ** 2)
      intrinsic_pixels = natural_w * natural_h
      waste_ratio = max(0, (intrinsic - effective) / intrinsic)
    """
    if natural_w <= 0 or natural_h <= 0 or rendered_w <= 0 or rendered_h <= 0:
        return {
            "intrinsic_pixels": 0,
            "effective_display_pixels": 0,
            "pixel_waste_ratio": 0.0,
            "pixel_waste_percent": 0.0,
            "oversized_factor": 1.0,
            "is_oversized": False,
        }

    intrinsic = natural_w * natural_h
    # Needed pixels at device pixel ratio
    effective = int(rendered_w * rendered_h * (dpr ** 2))

    if intrinsic <= effective:
        return {
            "intrinsic_pixels": intrinsic,
            "effective_display_pixels": effective,
            "pixel_waste_ratio": 0.0,
            "pixel_waste_percent": 0.0,
            "oversized_factor": 1.0,
            "is_oversized": False,
        }

    wasted = intrinsic - effective
    waste_ratio = round(wasted / intrinsic, 3)
    oversized_factor = round(intrinsic / max(1, effective), 2)

    return {
        "intrinsic_pixels": intrinsic,
        "effective_display_pixels": effective,
        "pixel_waste_ratio": waste_ratio,
        "pixel_waste_percent": round(waste_ratio * 100, 1),
        "oversized_factor": oversized_factor,
        "is_oversized": oversized_factor >= 1.5,
    }


def audit_lcp_candidate(lcp_img: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Audit the Largest Contentful Paint (LCP) image candidate for Core Web Vitals priority."""
    if not lcp_img:
        return {
            "has_lcp_image": False,
            "lcp_score": 100.0,
            "defects": [],
            "verdict": "No image-based LCP candidate detected.",
        }

    defects = []
    deductions = 0.0

    # Defect 1: Lazy-loaded LCP image (Severe anti-pattern)
    loading = lcp_img.get("loading", "eager").lower()
    if loading == "lazy":
        defects.append("CRITICAL: LCP hero image has loading='lazy'. This delays image download until layout calculation completes, adding 800ms-1,400ms to mobile LCP.")
        deductions += 45.0

    # Defect 2: Missing fetchpriority="high"
    fetchpriority = lcp_img.get("fetchpriority", "auto").lower()
    if fetchpriority != "high":
        defects.append("WARNING: LCP hero image is missing fetchpriority='high'. Browser discovers the asset late in the network waterfall.")
        deductions += 25.0

    # Defect 3: Missing explicit dimensions (CLS risk)
    if not lcp_img.get("has_explicit_dimensions"):
        defects.append("WARNING: LCP hero image lacks explicit width and height attributes, risking layout shift (CLS).")
        deductions += 15.0

    # Defect 4: Legacy format on hero
    src = lcp_img.get("current_src") or lcp_img.get("src", "")
    has_modern_sources = any(
        is_modern_format(s.get("type", "") + s.get("srcset", ""))
        for s in lcp_img.get("picture_sources", [])
    )
    if not is_modern_format(src) and not has_modern_sources:
        defects.append("INFO: LCP hero image is served in legacy format (JPEG/PNG). Converting to AVIF/WebP reduces transfer size by 35%-60%.")
        deductions += 15.0

    score = max(0.0, round(100.0 - deductions, 1))

    return {
        "has_lcp_image": True,
        "lcp_score": score,
        "src": src,
        "loading": loading,
        "fetchpriority": fetchpriority,
        "has_explicit_dimensions": lcp_img.get("has_explicit_dimensions", False),
        "is_modern_format": is_modern_format(src) or has_modern_sources,
        "defects": defects,
        "verdict": "Optimal LCP Delivery" if score >= 85 else ("Sub-optimal LCP Hints" if score >= 55 else "Critical LCP Bottleneck"),
    }


def audit_images(inspection_data: Dict[str, Any], target_dpr: float = 2.0) -> Dict[str, Any]:
    """Full performance audit across all discovered images."""
    images = inspection_data.get("images", [])
    lcp_candidate = inspection_data.get("lcp_candidate")

    lcp_audit = audit_lcp_candidate(lcp_candidate)

    image_audits = []
    total_byte_waste_pct = 0.0
    modern_format_count = 0
    explicit_dimension_count = 0
    responsive_srcset_count = 0
    oversized_count = 0

    for img in images:
        nat_w = img.get("natural_width", 0)
        nat_h = img.get("natural_height", 0)
        ren_w = img.get("rendered_width", 0)
        ren_h = img.get("rendered_height", 0)

        waste_info = calculate_byte_waste(nat_w, nat_h, ren_w, ren_h, dpr=target_dpr)
        total_byte_waste_pct += waste_info["pixel_waste_percent"]
        if waste_info["is_oversized"]:
            oversized_count += 1

        src = img.get("current_src") or img.get("src", "")
        has_modern_src = is_modern_format(src) or any(
            is_modern_format(s.get("type", "") + s.get("srcset", ""))
            for s in img.get("picture_sources", [])
        )
        if has_modern_src:
            modern_format_count += 1

        if img.get("has_explicit_dimensions"):
            explicit_dimension_count += 1

        has_srcset = bool(img.get("srcset")) or any(bool(s.get("srcset")) for s in img.get("picture_sources", []))
        if has_srcset:
            responsive_srcset_count += 1

        image_audits.append({
            "index": img.get("index"),
            "src": src,
            "alt": img.get("alt", ""),
            "is_lcp": bool(lcp_candidate and img.get("index") == lcp_candidate.get("index")),
            "natural_dimensions": f"{nat_w}x{nat_h}",
            "rendered_dimensions": f"{ren_w}x{ren_h}",
            "waste_info": waste_info,
            "has_modern_format": has_modern_src,
            "has_explicit_dimensions": img.get("has_explicit_dimensions", False),
            "has_srcset": has_srcset,
            "loading": img.get("loading", "eager"),
            "fetchpriority": img.get("fetchpriority", "auto"),
        })

    total_count = max(1, len(images))
    avg_byte_waste_pct = round(total_byte_waste_pct / total_count, 1)

    # Component scores:
    # 1. LCP Priority (35%)
    lcp_score = lcp_audit["lcp_score"]

    # 2. Byte Waste Efficiency (25%): 100 - avg waste %
    waste_score = max(0.0, round(100.0 - avg_byte_waste_pct, 1))

    # 3. Format Modernity (20%): ratio of modern formats
    format_score = round((modern_format_count / total_count) * 100.0, 1)

    # 4. Layout Shift Protection (10%): ratio of explicit dimensions
    cls_score = round((explicit_dimension_count / total_count) * 100.0, 1)

    # 5. Responsive Srcset Coverage (10%): ratio of srcset usage
    srcset_score = round((responsive_srcset_count / total_count) * 100.0, 1)

    overall = round(
        (lcp_score * 0.35)
        + (waste_score * 0.25)
        + (format_score * 0.20)
        + (cls_score * 0.10)
        + (srcset_score * 0.10),
        1
    )

    grade = (
        "A" if overall >= 90.0
        else "B" if overall >= 75.0
        else "C" if overall >= 60.0
        else "D" if overall >= 40.0
        else "F"
    )

    # Recommendations synthesis
    recommendations = []
    if lcp_audit.get("defects"):
        for d in lcp_audit["defects"]:
            recommendations.append(d)

    if oversized_count > 0:
        recommendations.append(f"Generate responsive srcset breakpoints for {oversized_count} oversized image(s) to stop serving desktop dimensions to mobile viewports.")

    if format_score < 70.0:
        recommendations.append(f"Convert legacy images ({total_count - modern_format_count} file(s)) to next-gen WebP or AVIF format to reduce byte transfer size by up to 50%.")

    if cls_score < 100.0:
        recommendations.append(f"Add explicit 'width' and 'height' attributes on {total_count - explicit_dimension_count} image(s) to eliminate Cumulative Layout Shift (CLS).")

    if srcset_score < 50.0:
        recommendations.append("Implement responsive <picture> or <img> srcset with accurate sizes queries to allow mobile devices to select calibrated resolution assets.")

    if not recommendations:
        recommendations.append("All images adhere to modern Core Web Vitals delivery budgets and responsive standards.")

    return {
        "url": inspection_data.get("url"),
        "mode": inspection_data.get("mode"),
        "total_images": len(images),
        "overall_score": overall,
        "grade": grade,
        "component_scores": {
            "lcp_priority": lcp_score,
            "byte_waste_efficiency": waste_score,
            "format_modernity": format_score,
            "layout_shift_protection": cls_score,
            "responsive_srcset_coverage": srcset_score,
        },
        "stats": {
            "oversized_images": oversized_count,
            "average_byte_waste_percent": avg_byte_waste_pct,
            "modern_format_count": modern_format_count,
            "explicit_dimensions_count": explicit_dimension_count,
            "responsive_srcset_count": responsive_srcset_count,
        },
        "lcp_audit": lcp_audit,
        "image_audits": image_audits,
        "recommendations": recommendations[:6],
    }
