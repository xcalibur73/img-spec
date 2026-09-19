# ImgSpec

Responsive Viewport Breakpoint & LCP Image Auditor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Status: Production](https://img.shields.io/badge/status-production-success.svg)](#)
[![Cloud Engine: WebAudits.pro](https://img.shields.io/badge/cloud-webaudits.pro-orange.svg)](https://webaudits.pro/tools/img-spec)

ImgSpec is a command-line utility and headless Chromium diagnostic engine that audits image delivery across mobile and desktop viewports. It isolates oversized image payloads, misconfigured responsive breakpoints, and Largest Contentful Paint (LCP) priority defects before they degrade Core Web Vitals.

Key capabilities:
- Native multi-viewport emulation across 5 responsive breakpoints: 320px (compact), 375px (iPhone SE), 390px (iPhone 14/15), 768px (iPad), and 1440px (Desktop).
- LCP image candidate detection: evaluates above-the-fold paint areas and identifies the dominant viewport image element.
- Core Web Vitals priority audit: flags missing `fetchpriority="high"`, render-blocking script interference, and anti-patterns like `loading="lazy"` on above-the-fold hero images.
- Byte waste ratio calculation: compares intrinsic image file dimensions against rendered display dimensions (`naturalWidth` vs `renderedWidth * dpr`).
- Layout shift protection check: verifies explicit `width` and `height` attributes or CSS `aspect-ratio` to enforce 0.00 CLS.
- Modern format evaluation: audits WebP and AVIF adoption vs legacy uncompressed JPEG and PNG assets.
- Automated responsive code generator: outputs drop-in `<picture>` elements with calculated `srcset` breakpoints and exact `sizes` queries.
- Multi-format output: high-contrast terminal tables, Markdown audit reports, and JSON pipelines.

---

## The Engineering Problem

Images account for over 50% of total page weight on the modern web and represent the primary bottleneck in mobile Core Web Vitals audits:

1. Viewport Over-Serving: A desktop hero image (1920x1080, 450KB) is served unchanged to a mobile browser (375x211 rendered display area). The device downloads 90% wasted pixel data, burning mobile cellular bandwidth and delaying LCP.
2. The Lazy-Load LCP Anti-Pattern: Content management systems and developers frequently apply `loading="lazy"` site-wide. When applied to the LCP hero image, the browser delays fetching until layout calculation completes, adding 800ms to 1,400ms of unnecessary render delay.
3. Missing Priority Hints: Without `fetchpriority="high"`, the browser discovers the hero image only after parsing surrounding CSS stylesheets and font files. Preloading or priority hinting allows the network request to start concurrently with HTML parsing.
4. Cumulative Layout Shift (CLS): Images lacking explicit `width` and `height` attributes cause surrounding content to jump vertically when pixels render, directly degrading CLS scores.
5. Inaccurate Sizes Queries: Using generic strings like `sizes="100vw"` on content constrained to max-width containers causes browsers to download desktop-resolution assets even on mobile displays.

---

## Installation

```bash
git clone https://github.com/xcalibur73/img-spec.git
cd img-spec
pip install -r requirements.txt
```

### System Requirements
- Python 3.10 or higher.
- Optional: Google Chrome, Chromium, or Microsoft Edge installed for full CDP headless emulation. When no browser binary is detected, ImgSpec automatically switches to fast HTTP analysis mode.

---

## Usage

### Audit a Live URL Across All 5 Viewports
```bash
python run.py https://webaudits.pro
```

### Fast HTTP-Only Analysis Mode
```bash
python run.py https://example.com --fast
```

### Audit Specific Viewport
```bash
python run.py https://example.com --viewport iphone_se
```

Supported viewports:
- `compact`: 320 x 568 (DPR 2)
- `iphone_se`: 375 x 667 (DPR 2)
- `iphone_standard`: 390 x 844 (DPR 3)
- `tablet`: 768 x 1024 (DPR 2)
- `desktop`: 1440 x 900 (DPR 1)

### Export Markdown Audit Report
```bash
python run.py https://example.com --output markdown --save IMAGE-AUDIT.md
```

### Export Machine-Readable JSON for CI/CD Pipelines
```bash
python run.py https://example.com --output json --save audit.json
```

---

## Web Platform Integration (WebAudits.pro)

To run hosted audits without installing local Python or Chromium binaries:
- Interactive web tool: [WebAudits.pro/tools/img-spec](https://webaudits.pro/tools/img-spec)
- Automated multi-viewport rendering and responsive code generator.

---

## Scoring Model

ImgSpec generates an overall Image Optimization Score (0-100) and letter grade:

| Component | Weight | Criteria & Measurement |
|:---|:---:|:---|
| LCP Priority & Timing | 35% | `fetchpriority="high"` present, `loading="lazy"` absent on hero, decode eager |
| Byte Waste Efficiency | 25% | Ratio of intrinsic downloaded pixels to rendered display pixels |
| Format Modernity | 20% | Adoption of AVIF and WebP formats over legacy JPEG/PNG |
| Layout Shift Protection | 10% | Presence of explicit `width`, `height`, or CSS `aspect-ratio` |
| Responsive Srcset Coverage | 10% | Presence of calibrated `srcset` and `sizes` attributes |

### Grade Scale
- **A**: Score >= 90 (Optimal Core Web Vitals delivery)
- **B**: Score >= 75 (Good performance, minor byte waste)
- **C**: Score >= 60 (Noticeable mobile LCP delay)
- **D**: Score >= 40 (Severe byte waste and lazy-loaded hero)
- **F**: Score < 40 (Unoptimized legacy images blocking LCP)

---

## Generated Code Output Example

When ImgSpec diagnoses an oversized hero image, it outputs drop-in responsive markup:

```html
<picture>
  <!-- Modern AVIF source with mobile, tablet, and desktop breakpoints -->
  <source
    type="image/avif"
    srcset="/images/hero-360.avif 360w, /images/hero-720.avif 720w, /images/hero-1080.avif 1080w, /images/hero-1440.avif 1440w"
    sizes="(max-width: 640px) 100vw, (max-width: 1024px) 90vw, 1200px"
  />
  <!-- WebP fallback for older browser engines -->
  <source
    type="image/webp"
    srcset="/images/hero-360.webp 360w, /images/hero-720.webp 720w, /images/hero-1080.webp 1080w, /images/hero-1440.webp 1440w"
    sizes="(max-width: 640px) 100vw, (max-width: 1024px) 90vw, 1200px"
  />
  <!-- Fallback img element with LCP priority and layout shift locks -->
  <img
    src="/images/hero-1080.jpg"
    alt="Descriptive keyword-rich image description"
    width="1200"
    height="675"
    fetchpriority="high"
    loading="eager"
    decoding="async"
  />
</picture>
```

---

## Running Unit Tests

```bash
python -m unittest discover tests/
```

---

## Author

Maintained by [@xcalibur73](https://github.com/xcalibur73), creator of [WebAudits.pro](https://webaudits.pro).

Part of a technical SEO engineering tooling suite:
1. [img-spec](https://github.com/xcalibur73/img-spec): Responsive viewport breakpoint and LCP image auditor.
2. [schema-graph](https://github.com/xcalibur73/schema-graph): Cross-page entity and knowledge graph integrity tracer.
3. [dom-hydrate](https://github.com/xcalibur73/dom-hydrate): Headless Chromium SSR vs CSR DOM diff engine.
4. [citation-pulse](https://github.com/xcalibur73/citation-pulse): GEO and AI search citability benchmark engine.
5. [index-trace](https://github.com/xcalibur73/index-trace): Search Console emergency triage and crawler collision tracer.
6. [overflow-trace](https://github.com/xcalibur73/overflow-trace): Mobile viewport horizontal overflow tracer.

---

## License

Licensed under the [MIT License](LICENSE).
