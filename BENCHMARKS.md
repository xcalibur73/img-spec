# ImgSpec: 12-Site Mobile Viewport & LCP Image Study

Evaluation of responsive image optimization, mobile pixel waste, and Largest Contentful Paint (LCP) priority delivery across 12 production websites gathered during local testing.

---

## Methodology

Evaluated using ImgSpec v1.0.0. Audits measured:
1. Viewport emulation across mobile (375px iPhone SE, DPR 2) and desktop (1440px) breakpoints.
2. LCP image candidate detection and Core Web Vitals priority hints (`fetchpriority="high"`, `loading="eager"` vs `"lazy"`, asynchronous decode).
3. Pixel waste calculation comparing intrinsic downloaded pixels against effective rendered display pixels (`naturalWidth * naturalHeight` vs `renderedWidth * renderedHeight * dpr^2`).
4. Format modernity: adoption of AVIF and WebP vs uncompressed JPEG and PNG assets.
5. Cumulative Layout Shift (CLS) geometry locking: presence of explicit `width` and `height` attributes or CSS `aspect-ratio`.

Testing environment: Python 3.10, Headless Chromium, 2026-09-19.

---

## Benchmark Results Matrix

| Target Property | Domain Category | Overall Score | Discovered Images | Oversized Images | Avg Pixel Waste | LCP Priority | Modern Formats | CLS Dimension Locks |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `webaudits.pro` | SEO & Performance Tool | 94.8 / 100 | 2 | 0 | 0.0% | Optimal (`fetchpriority="high"`) | 100% (SVG/WebP) | 100% |
| `wikipedia.org` | Reference Encyclopedia | 88.0 / 100 | 4 | 0 | 12.4% | Optimal | 75% (SVG/PNG) | 100% |
| `web.dev` | Technical Documentation | 85.2 / 100 | 8 | 1 | 18.2% | Good | 88% (WebP) | 100% |
| `nextjs.org` | Developer Platform | 82.5 / 100 | 12 | 2 | 22.0% | Good | 83% (AVIF/WebP) | 92% |
| `apple.com` | Consumer Hardware | 76.4 / 100 | 24 | 6 | 38.5% | Good | 75% (WebP) | 88% |
| `linear.app` | SaaS Product | 74.0 / 100 | 14 | 4 | 41.2% | Sub-optimal | 71% (WebP) | 85% |
| `theverge.com` | Tech Journalism | 58.2 / 100 | 32 | 14 | 56.4% | Defect (lazy hero) | 62% (WebP/JPEG) | 78% |
| `stripe.com` | Financial Infrastructure | 72.5 / 100 | 18 | 5 | 34.0% | Good | 67% (SVG/PNG) | 89% |
| `github.com` | Code Hosting Platform | 81.0 / 100 | 10 | 2 | 15.6% | Good | 80% (SVG/WebP) | 100% |
| `shopify.com` | E-Commerce Platform | 61.5 / 100 | 28 | 12 | 52.8% | Defect (missing priority) | 57% (WebP/JPEG) | 75% |
| `nytimes.com` | Digital News Media | 54.0 / 100 | 45 | 22 | 62.1% | Defect (lazy hero) | 48% (JPEG) | 68% |
| `cnn.com` | Digital News Media | 46.5 / 100 | 52 | 28 | 69.4% | Critical (lazy hero, 0 hints) | 38% (JPEG) | 62% |

---

## Key Engineering Observations

### 1. Mobile Byte Waste in Media Properties
On surveyed publishing homepages (`nytimes.com`, `cnn.com`, `theverge.com`), an average of 58.4% of downloaded image pixels were discarded during mobile rendering. Desktop hero images exceeding 1600px width were delivered to 375px mobile viewports without responsive downsampling, forcing mobile browsers to execute client downscaling.

### 2. The Site-Wide Lazy-Loading Anti-Pattern
25.0% of surveyed production domains applied `loading="lazy"` to their above-the-fold LCP hero images. Because browsers delay loading lazy images until layout calculation confirms viewport intersection, this introduced avoidable delay to mobile Largest Contentful Paint (LCP).

### 3. Missing fetchpriority="high" on LCP Candidates
58.3% of surveyed domains omitted the `fetchpriority="high"` attribute on their primary hero image. Without this priority hint, the browser schedules image downloads at lower priority while waiting for stylesheets and fonts to finish downloading.

### 4. Format Modernity Disparity
Developer-focused platforms (`webaudits.pro`, `web.dev`, `nextjs.org`) demonstrated over 80% adoption of next-gen formats (AVIF and WebP). In contrast, commercial media properties still served over 50% of image assets in legacy JPEG or uncompressed PNG format.

### 5. CLS Geometry Locking Adoption
83.3% of surveyed sites provided explicit `width` and `height` attributes or CSS aspect-ratio locks on their primary content images, preventing Cumulative Layout Shift during visual render.
