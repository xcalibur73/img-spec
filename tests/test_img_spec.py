"""
Unit tests for ImgSpec image auditing, byte waste calculation, and markup generation.
"""

import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from img_spec.auditor import calculate_byte_waste, audit_lcp_candidate, audit_images
from img_spec.markup_generator import (
    calculate_srcset_breakpoints,
    generate_sizes_query,
    generate_responsive_picture_markup,
)
from img_spec.devices import get_viewport, get_all_viewports


class TestDeviceViewports(unittest.TestCase):

    def test_all_viewports_available(self):
        vps = get_all_viewports()
        self.assertEqual(len(vps), 5)
        ids = {vp.id for vp in vps}
        self.assertIn("compact", ids)
        self.assertIn("iphone_se", ids)
        self.assertIn("iphone_standard", ids)
        self.assertIn("tablet", ids)
        self.assertIn("desktop", ids)

    def test_iphone_se_metrics(self):
        vp = get_viewport("iphone_se")
        self.assertEqual(vp.width, 375)
        self.assertEqual(vp.device_pixel_ratio, 2.0)
        self.assertTrue(vp.is_mobile)


class TestByteWasteCalculator(unittest.TestCase):

    def test_exact_fit_no_waste(self):
        # 375px display * 2 DPR = 750px needed
        waste = calculate_byte_waste(750, 400, 375, 200, dpr=2.0)
        self.assertEqual(waste["pixel_waste_percent"], 0.0)
        self.assertFalse(waste["is_oversized"])

    def test_oversized_desktop_image_on_mobile(self):
        # 1920x1080 downloaded, displayed at 375x211 on DPR 2 (750x422 needed)
        waste = calculate_byte_waste(1920, 1080, 375, 211, dpr=2.0)
        self.assertGreaterEqual(waste["pixel_waste_percent"], 80.0)
        self.assertTrue(waste["is_oversized"])
        self.assertGreaterEqual(waste["oversized_factor"], 5.0)

    def test_zero_dimensions_handling(self):
        waste = calculate_byte_waste(0, 0, 100, 100)
        self.assertEqual(waste["pixel_waste_percent"], 0.0)
        self.assertFalse(waste["is_oversized"])


class TestLCPAuditor(unittest.TestCase):

    def test_optimal_lcp_hero(self):
        hero = {
            "src": "https://example.com/hero.avif",
            "current_src": "https://example.com/hero.avif",
            "loading": "eager",
            "fetchpriority": "high",
            "has_explicit_dimensions": True,
            "picture_sources": [],
        }
        res = audit_lcp_candidate(hero)
        self.assertEqual(res["lcp_score"], 100.0)
        self.assertEqual(len(res["defects"]), 0)
        self.assertEqual(res["verdict"], "Optimal LCP Delivery")

    def test_lazy_loaded_lcp_penalty(self):
        hero = {
            "src": "https://example.com/hero.jpg",
            "current_src": "https://example.com/hero.jpg",
            "loading": "lazy",  # Critical defect
            "fetchpriority": "auto",
            "has_explicit_dimensions": False,
            "picture_sources": [],
        }
        res = audit_lcp_candidate(hero)
        self.assertLess(res["lcp_score"], 50.0)
        self.assertTrue(any("loading='lazy'" in d for d in res["defects"]))
        self.assertTrue(any("fetchpriority='high'" in d for d in res["defects"]))


class TestMarkupGenerator(unittest.TestCase):

    def test_srcset_breakpoints(self):
        tiers = calculate_srcset_breakpoints(1200)
        self.assertIn(360, tiers)
        self.assertIn(720, tiers)
        self.assertIn(1200, tiers)
        self.assertNotIn(1600, tiers)

    def test_sizes_query_full_width(self):
        sizes = generate_sizes_query(1200, is_full_width=True)
        self.assertIn("100vw", sizes)
        self.assertIn("1200px", sizes)

    def test_responsive_picture_markup(self):
        img_data = {
            "src": "/assets/hero.jpg",
            "alt": "Modern architecture living room",
            "natural_width": 1200,
            "natural_height": 675,
            "rendered_width": 800,
        }
        markup = generate_responsive_picture_markup(img_data, is_lcp=True)
        self.assertIn("<picture>", markup)
        self.assertIn('type="image/avif"', markup)
        self.assertIn('type="image/webp"', markup)
        self.assertIn('fetchpriority="high"', markup)
        self.assertIn('loading="eager"', markup)
        self.assertIn('width="1200"', markup)
        self.assertIn('height="675"', markup)


class TestCompositeImageAuditor(unittest.TestCase):

    def test_composite_score_calculation(self):
        inspection = {
            "url": "https://example.com",
            "mode": "test",
            "lcp_candidate": {
                "index": 1,
                "src": "https://example.com/hero.avif",
                "loading": "eager",
                "fetchpriority": "high",
                "has_explicit_dimensions": True,
                "picture_sources": [],
            },
            "images": [
                {
                    "index": 1,
                    "src": "https://example.com/hero.avif",
                    "current_src": "https://example.com/hero.avif",
                    "natural_width": 800,
                    "natural_height": 450,
                    "rendered_width": 400,
                    "rendered_height": 225,
                    "has_explicit_dimensions": True,
                    "srcset": "hero.avif 800w",
                    "loading": "eager",
                    "fetchpriority": "high",
                    "picture_sources": [],
                }
            ],
        }
        audit = audit_images(inspection, target_dpr=2.0)
        self.assertGreaterEqual(audit["overall_score"], 90.0)
        self.assertEqual(audit["grade"], "A")
        self.assertEqual(audit["stats"]["oversized_images"], 0)


if __name__ == "__main__":
    unittest.main()
