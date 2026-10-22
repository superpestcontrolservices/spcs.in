# Image implementation report

## Mapping and page updates

- HTML pages updated for image and metadata handling: 529
- Supplied image files staged under `images/`: 30; 16 pre-existing byte-identical copies were preserved.
- Of 63 district-child campaign paths, 26 active template pages were retained and 37 redirect files were left unchanged.

| Image category | Page types using it | Pages updated |
|---|---|---:|
| ant | service: 1 | 1 |
| bed-bug | industry: 3, local campaign: 6, locality: 80, service: 1 | 90 |
| cockroach | industry: 1, local campaign: 2, locality: 48, service: 1 | 52 |
| fly | locality: 47, service: 1 | 48 |
| fogging | industry: 4, local campaign: 11, locality: 65, service: 1 | 81 |
| general | district: 41, home/about/contact: 2, industry: 1, local campaign: 1, locality: 32, other: 1, service: 4 | 82 |
| rodent | local campaign: 3, locality: 62, service: 1 | 66 |
| termite | local campaign: 2, locality: 68, service: 3 | 73 |
| wasp | service: 1 | 1 |
| wood-borer | local campaign: 1, locality: 33, service: 1 | 35 |

## Topic-specific photo gaps and fallbacks

These entries identify pages without a dedicated supplied photo, or a support slot where no second unique subject-matched asset was available.

| Page / group | Page type | Fallback or omission |
|---|---|---|
| `/services/ant-control/` | service | No second distinct ant-treatment photo was supplied; no unrelated fallback was added. |
| `/services/bed-bug-eradication/` | service | No second distinct bed-bug photo was supplied; no unrelated fallback was added. |
| `/services/commercial-amc-ipm/` | service | `spray-warehouse.webp` |
| `/services/commercial-fumigation/` | service | `spray-warehouse.webp` |
| `/services/sanitization-disinfection/` | service | No sanitization-specific or suitable general photo was supplied; no image was added. |
| `/services/scorpion-control/` | service | No scorpion-specific or suitable general photo was supplied; no image was added. |
| `/services/wasp-hornet-nest-removal/` | service | The two existing wasp photos were retained; no unrelated third image was added. |

## Validation

- Broken local `src`/`srcset` paths: **0**
- Content images missing alt text: **0**
- Content images with alt text outside 8–15 words: **0**
- Images missing width/height: **0**
- Content images missing responsive crop styles: **0**
- Incorrect Open Graph, Twitter or JSON-LD image metadata entries: **0**
- Content images missing from the sitemap: **0**
- Duplicate images introduced by new placements: **0**
- Pages with preserved pre-existing repeated content images: **6**
- Sitemap URLs with image entries: **529**
- Total `<image:image>` entries in the sitemap: **1240**

Existing repeated image figures were preserved as approved; they are listed below and are not counted as new duplicate placements.

### Preserved duplicate-image exceptions

- `services/ant-control/: technician-thermal-fogging-outdoor-area.webp × 3`
- `services/bed-bug-eradication/: bedbugs.webp × 2, NIPHM Event-800.webp × 2`
- `services/commercial-fumigation/: NIPHM Event-800.webp × 2`
- `services/pre-construction-anti-termite-treatment/: termite-mud-tubes-on-wall.webp × 3`
- `services/termite-piping-system/: termite-mud-tubes-on-wall.webp × 3`
- `services/wood-borer-control/: wood-borer-beetle-close-up.webp × 2, NIPHM Event-800.webp × 2`

## Asset quality notes

All supplied files are WebP, at most 1600 px wide, and below 200 KiB, so responsive derivative copies were not required by the requested thresholds. The two wood-borer furniture-spray source files are byte-identical; only one is used in rotation. Portrait images are cropped by the shared figure styling, so check the selected crop at mobile widths.
