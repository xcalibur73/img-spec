# ImgSpec

Responsive viewport breakpoint and Largest Contentful Paint (LCP) image auditor.

Part of the [WebAudits.pro](https://webaudits.pro) technical intelligence platform.

---

## What it does

ImgSpec audits image asset delivery, responsive viewport adaptation, and Largest Contentful Paint (LCP) performance. It inspects:
- Pixel waste ratios by comparing intrinsic image dimensions against rendered CSS display dimensions across viewports.
- Largest Contentful Paint (LCP) hero image priority, detecting anti-patterns such as `loading="lazy"` on hero images or missing `fetchpriority="high"`.
- Modern image format adoption (AVIF, WebP vs. legacy JPEG, PNG).
- Layout shift protection (explicit `width` and `height` attributes or CSS aspect ratios preventing Cumulative Layout Shift).
- Generates drop-in, zero-CLS responsive `<picture>` and `<source srcset>` HTML markup tailored to measured breakpoints.

---

## Why it exists

Images remain the single largest contributor to mobile Largest Contentful Paint (LCP) failures. Sites frequently:
- Serve 2,400px desktop hero images to 375px mobile viewports due to missing `srcset` attributes or improper `sizes` declarations (such as `sizes="100vw"` instead of responsive clamps).
- Apply blanket `loading="lazy"` across all images, artificially delaying the hero element until after client-side hydration and scroll calculation.
- Omit explicit aspect ratios, triggering layout recalculations that degrade Core Web Vitals scores.

ImgSpec isolates image bloat across real viewports and generates optimized responsive replacement markup.

---

## Key features

- **Multi-Viewport Emulation:** Inspects images across 5 calibrated responsive viewports: 320px (compact), 375px (iPhone SE), 390px (iPhone 14/15), 768px (iPad/tablet), and 1440px (desktop).
- **LCP Candidate Detection:** Automatically locates the largest visual element in the viewport and audits its priority headers and decoding attributes.
- **Pixel Waste Calculation:** Measures exact mathematical wasted pixel area and byte overhead resulting from oversized asset delivery.
- **Responsive Markup Synthesis:** Generates complete drop-in `<picture>` tags with AVIF/WebP MIME type negotiation and fluid `sizes` queries.
- **Fast Static Fallback:** Supports an optional HTTP-only inspection mode for high-throughput headless scans.

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

ImgSpec executes three primary modules:
1. `inspector.py`: Manages CDP browser sessions, emulates screen metrics, captures image natural and client dimensions, and flags LCP candidates.
2. `auditor.py`: Evaluates pixel waste, format modernity, layout shift protections, and computes the 5-component optimization score.
3. `markup_generator.py`: Synthesizes production-ready responsive picture tags using mathematical aspect ratio preservation and optimal breakpoints.

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Google Chrome or Chromium installed and available in system PATH

### Install from Source
```bash
git clone https://github.com/xcalibur73/img-spec.git
cd img-spec
pip install -r requirements.txt
pip install -e .
```

---

## Usage

### Basic CLI Invocation
```bash
# Audit images on a target URL with default iPhone SE viewport (375px)
img-spec https://webaudits.pro

# Audit using a specific viewport breakpoint
img-spec https://example.com --viewport tablet

# Fast static inspection mode (skips headless browser)
img-spec https://example.com --fast

# Export JSON report for CI/CD asset verification
img-spec https://example.com --output json --save img-report.json

# Check installed version
img-spec --version
```

---

## Example output

```text
+-------------------------------------------------------------------------------+
| ImgSpec: Responsive Viewport Breakpoint & LCP Image Auditor                   |
| Target URL: https://webaudits.pro                                             |
| Image Optimization Score: 100.0/100 (Grade: A)                                |
| Mode: cdp_headless | Discovered Images: 6 | Oversized: 0 | Avg Pixel Waste: 0% |
+-------------------------------------------------------------------------------+

Largest Contentful Paint (LCP) Candidate:
- Asset: /hero-banner.webp
- Verdict: PASS (LCP Score: 100.0/100)
- Loading: eager | FetchPriority: high | Modern Format: True

Discovered Image Assets & Viewport Efficiency:
+---+----------------------+-----------+----------+-------------+--------+----------+----------+
| # | Asset Source         | Intrinsic | Rendered | Pixel Waste | Format | CLS Lock | Role     |
+---+----------------------+-----------+----------+-------------+--------+----------+----------+
| 1 | /hero-banner.webp    | 750x422   | 375x211  | 0.0%        | Modern | Yes      | LCP HERO |
| 2 | /logo.svg            | 180x40    | 180x40   | 0.0%        | Modern | Yes      | Content  |
+---+----------------------+-----------+----------+-------------+--------+----------+----------+
```

---

## Benchmark / methodology

### Empirical 12-Site Viewport & LCP Study
- **Dataset:** 12 production web properties across editorial media, e-commerce, and SaaS landing pages.
- **Command Used:** `python run.py <url> --viewport iphone_se --output json`
- **Tool Version:** ImgSpec v1.0.0
- **Environment:** Windows 11, Chromium 128.0, Python 3.12, unthrottled fiber network.
- **Calculation Formula:**
  - Intrinsic pixel area: `naturalWidth * naturalHeight`
  - Rendered display area: `(clientWidth * dpr) * (clientHeight * dpr)`
  - Pixel waste percentage: `max(0, (intrinsic_area - rendered_area) / intrinsic_area) * 100`
- **Results:**
  - 58.4% of downloaded image pixels were discarded on mobile viewports due to desktop-sized hero images served without `srcset` breakpoints.
  - Complete study dataset: [BENCHMARKS.md](BENCHMARKS.md).

---

## Limitations

- **Geometric Waste Approximation:** Pixel waste calculations assume standard bitmap images (JPEG, PNG, WebP, AVIF). Vector formats (SVG) are not penalized for high intrinsic viewBox dimensions.
- **CDN Dynamic Negotiation:** ImgSpec evaluates the asset delivered to the emulated browser session. CDNs utilizing `Client Hints` (`Sec-CH-DPR`, `Sec-CH-Width`) may adapt responses differently if headers are stripped by intermediary proxies.
- **Local Network Timings:** Measures in-browser decode timing; it does not measure network round-trip time (RTT) from edge caches in different geographic regions.

---

## Accuracy / standards

ImgSpec evaluates image performance against official web standards and geometric formulas:

| Metric / Check | Classification | Authority / Standard |
|:---|:---|:---|
| Fetch Priority (`fetchpriority`) | Web Standard | W3C HTML Priority Hints |
| Lazy Loading (`loading="lazy"`) | Web Standard | HTML Living Standard (WHATWG) |
| Modern Format Negotiation | Web Standard | W3C / IETF MIME Types (AVIF, WebP) |
| Layout Shift Prevention (CLS) | Google / Web Standard | Google Web Vitals Specification |
| Pixel Waste Ratio | Project-Derived Heuristic | Geometric rendered area differential |
| Composite Image Score | Project-Derived Heuristic | 5-factor weighted efficiency formula |

---

## Testing

ImgSpec includes unit tests covering viewport emulation, pixel waste calculation, LCP hero detection, and markup generation:

```bash
# Run unit test suite
python -m unittest discover -s tests

# Test execution output
# Ran 11 tests in 0.000s
# OK
```

Continuous integration runs automatically across Linux and Windows runners via GitHub Actions.

---

## Roadmap

- [x] Initial release with CDP 5-viewport emulation and responsive markup generator.
- [x] PEP 621 packaging, CLI `--version`, and Windows cp1252 encoding safety.
- [ ] Direct automated image compression and AVIF/WebP generation via Pillow.
- [ ] CSS `background-image` responsive `image-set()` resolution.
- [ ] WebAudits.pro continuous LCP regression monitoring.

---

## License

MIT License. See [LICENSE](LICENSE) for full details.
