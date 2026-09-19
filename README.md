# ImgSpec

Responsive viewport breakpoint and Largest Contentful Paint (LCP) image auditor.

Part of the [WebAudits.pro](https://webaudits.pro) technical intelligence platform.

---

## Quickstart

Install in editable mode and audit responsive image breakpoints in seconds:

```bash
# Clone and install
git clone https://github.com/xcalibur73/img-spec.git
cd img-spec
pip install -r requirements.txt
pip install -e .

# Audit target URL with default mobile viewport (375px)
img-spec https://example.com

# Audit specific tablet or desktop viewport
img-spec https://example.com --viewport tablet
```

---

## What It Does & Why It Matters

ImgSpec audits image asset delivery, responsive viewport adaptation, and Largest Contentful Paint (LCP) performance. 

Images remain the single largest contributor to mobile LCP failures. Websites frequently serve 2,400px desktop hero images to 375px mobile screens due to missing `srcset` attributes or oversized `sizes` queries, while blanket `loading="lazy"` delays above-the-fold hero rendering.

ImgSpec isolates image bloat across real viewports and synthesizes drop-in replacement markup:
- **Multi-Viewport Emulation:** Inspects images across 5 calibrated responsive viewports: 320px (compact), 375px (iPhone SE), 390px (iPhone 14/15), 768px (iPad/tablet), and 1440px (desktop).
- **LCP Candidate Detection:** Identifies the largest visual element in the viewport and audits priority attributes (`fetchpriority="high"`, `loading="eager"`).
- **Pixel Waste Calculation:** Measures exact mathematical wasted pixel area and byte overhead resulting from oversized asset delivery.
- **Modern Format Adoption:** Audits AVIF and WebP adoption against legacy JPEG and PNG formats.
- **Responsive Markup Synthesis:** Generates complete drop-in `<picture>` tags with AVIF/WebP MIME type negotiation and fluid `sizes` queries.

---

## Usage & CLI Options

```bash
# Audit with default mobile viewport (375px)
img-spec https://webaudits.pro

# Audit across specific viewports (compact, mobile, mobile-large, tablet, desktop)
img-spec https://example.com --viewport desktop

# Fast static inspection mode (skips headless browser launch)
img-spec https://example.com --fast

# Export machine-readable JSON for CI/CD performance gates
img-spec https://example.com --output json --save img-audit.json

# Check installed version
img-spec --version
```

---

## Example Output

```text
+-------------------------------------------------------------------------------+
| ImgSpec: Responsive Viewport & LCP Image Auditor                              |
| Target URL: https://webaudits.pro                                             |
| Overall Image Optimization Score: 98.2/100 (Grade: A)                         |
| Viewport: mobile (375x667) | Total Images: 6 | LCP Candidate: Verified        |
+-------------------------------------------------------------------------------+

Component Score Breakdown:
+------------------------------------+--------+------------+
| Component Dimension                | Weight | Score      |
+------------------------------------+--------+------------+
| Intrinsic Sizing & Pixel Waste     | 30%    | 100.0/100  |
| LCP Hero Priority Hygiene          | 25%    | 100.0/100  |
| Next-Gen Format Adoption           | 20%    | 95.0/100   |
| CLS Dimension Stability            | 15%    | 100.0/100  |
| Responsive Breakpoint Coverage     | 10%    | 92.0/100   |
+------------------------------------+--------+------------+

Largest Contentful Paint (LCP) Candidate:
- Hero Element: /images/hero-architecture.webp
- Rendered Dimensions: 375x250px | Intrinsic: 750x500px (Pixel Density: 2x Optimal)
- Priority Attributes: fetchpriority="high", loading="eager", decoding="async"
- Anti-Patterns Detected: None (Clean LCP setup)
```

---

## Architecture

```text
[Target URL + Viewport Parameter]
               |
               v
     [Chromium CDP Engine]
               |
               +---> Viewport Emulation & Layout Settlement
               +---> DOM Image Node Discovery (img, picture, background-image)
               +---> LCP Candidate Detection & Metric Capture
               |
               v
      [Image Auditor Engine]
               |
               +---> Intrinsic vs. Rendered Dimension Comparison
               +---> Pixel Waste Calculation
               +---> Priority & Anti-Pattern Audit (lazy hero, missing fetchpriority)
               +---> CLS Dimension Verification
               |
               v
   [Markup & Report Generator]
               |
               +---> Drop-in Responsive <picture> Element
               +---> Terminal Report / Markdown / JSON Pipeline Output
```

- `inspector.py`: Manages CDP browser sessions, emulates screen metrics, captures image natural and client dimensions, and flags LCP candidates.
- `auditor.py`: Evaluates pixel waste, format modernity, layout shift protections, and computes the 5-component optimization score.
- `markup_generator.py`: Synthesizes production-ready responsive picture tags using mathematical aspect ratio preservation and optimal breakpoints.

---

## Standards & Heuristics

ImgSpec evaluates image delivery against official W3C specifications and project heuristics:

| Metric / Check | Classification | Authority / Basis |
|:---|:---|:---|
| LCP Candidate Selection | Web Standard | W3C Largest Contentful Paint API |
| Responsive Picture Syntax | Web Standard | HTML5 `<picture>` and `srcset` Specifications |
| Explicit Width & Height CLS Budget | Core Web Vitals Standard | Chrome Web Vitals Layout Stability Guidelines |
| Pixel Waste Ratio | Project-Derived Heuristic | Area formula: `(intrinsic_area - rendered_area) / intrinsic_area` |
| Viewport Optimization Score | Project-Derived Heuristic | 5-factor weighted efficiency formula |

---

## Limitations

- **Chromium Dependency:** Full viewport emulation and rendered CSS dimension capture require Google Chrome or Chromium installed on the host machine.
- **CSS Background Images:** Audits `background-image` CSS properties on visible DOM containers, but cannot generate automated replacement `<picture>` tags for CSS background rules.
- **Lazy Load Triggering:** Focuses on above-the-fold assets visible upon initial settlement; images located deep in the document scroll require full scroll simulation.

---

## Testing & CI

```bash
# Run unit tests
python -m unittest discover -s tests

# Output
# Ran 11 tests in 0.002s
# OK
```

Continuous integration runs automatically across Ubuntu and Windows runners on every commit via GitHub Actions.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
