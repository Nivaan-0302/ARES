# Asset provenance and distribution decisions

**Creator and Project Lead:** Nivaan Raina. Original project copyright remains unchanged. This current register connects available evidence with remaining rights and provenance questions. Historical research and later decisions remain separately recorded.

| Material | Current evidence | Required follow-up |
| --- | --- | --- |
| Original ARES code/interface/documentation | Creator attribution remains Nivaan Raina; material ChatGPT development/engineering assistance is disclosed. Original ARES software and documentation use the [MIT License](LICENSE). | Retain attribution, accurate assistance disclosures and copyright/license notices. Original-software licensing does not override third-party rights or dataset terms. |
| `mars_hero.png` | NASA/JPL-Caltech Viking Orbiter mosaic from [NASA Science — Mars Planet Globe](https://science.nasa.gov/resource/mars-planet-globe/). The source JPEG was resized to 600 × 600 and converted to PNG, replacing an image of unverified origin. | Credit NASA/JPL-Caltech and follow [NASA Images and Media Guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/). NASA has not endorsed or certified ARES. The image is outside the original ARES software license. |
| Owner's full MOLA GeoTIFF | Absent from this workspace. The owner later recorded its dimensions, CRS, full-file checksum and two local regional integration passes; see [scientific inputs](docs/SCIENTIFIC_INPUTS.md). | Preserve the original and recorded hash. Original download URL, conversion history and vertical-reference inheritance remain unresolved; the hash does not establish these. |
| Historical real 256 × 256 MOLA sample | Recorded Rasterio/sample tests; all 65,536 values matched a nearest-neighbor virtual warp of a public USGS COG window. | Preserve the exact sample identity and comparison evidence. This window does not establish the entire original file's processing history or independent ground truth. |
| Public PDS/USGS scientific references | Native product-window comparisons and a separate 4 samples/degree global reference were evaluated; sources/methods are in [dataset provenance](docs/DATASET_PROVENANCE.md). | Cite exact products, labels and methods; distinguish native reference observations, transformed derivatives and the owner's original input. |
| NASA Trek Viking MDIM21 basemap | External service URL and visible NASA Mars Trek attribution appear in [script.js](script.js); imagery is distinct from MOLA elevation data. | Check service availability and applicable attribution terms for the event. Browser tests that isolate external tiles do not verify service uptime. |
| Leaflet 1.9.4 | Vendored with the upstream BSD 2-Clause license. | Retain [third-party notices](THIRD_PARTY_NOTICES.md), upstream license and [checksums](vendor/SHA256SUMS). |
| Three.js 0.160.1 and OrbitControls | Vendored with upstream MIT notices. | Retain third-party notices, upstream license and checksums. |
| Globe surface | DEM-derived elevation-colored canvas when data are available, or the identified fallback surface. | Describe it as a visualization, not a photograph or live orbital observation. |
| Application screenshots | Captured interface views are documented in the [gallery](docs/SCREENSHOT_GALLERY.md), including the actual input and displayed state. | Preserve dataset labels and any missing-data or external-imagery limits; never present a fixture or fallback as a measured Mars observation. |

## Historical decisions and current context

The [hero investigation](docs/ASSET_INVESTIGATION.md) preserves its initial unresolved-asset findings and the later completed NASA/JPL-Caltech replacement. Its original candidate discussion describes an earlier stage; it is not a current request to repeat the replacement. The [historical sprint report](docs/SPRINT_REPORT.md) similarly retains what was available during that run.

The original full raster remains absent from this workspace. Its later owner checksum establishes a reproducible local file identity; source/processing history still requires evidence. [Scientific inputs](docs/SCIENTIFIC_INPUTS.md) distinguishes that owner record from the historical sample and public-reference comparisons. A filename is not a scientific citation.

The selected challenge and current access evidence are documented in [competition readiness](docs/COMPETITION_READINESS.md). Review the actual event's publication/submission terms and third-party permissions before external submission. No license, attribution record or development timestamp is changed by this register.
