# Asset provenance and distribution decisions

**Creator and Project Lead:** Nivaan Raina. Original project copyright remains unchanged. This register identifies evidence and unresolved rights; it does not grant a license or assume ownership of third-party materials.

| Material | Current evidence | Required follow-up |
| --- | --- | --- |

| Original ARES code/interface/documentation | Creator attribution remains Nivaan Raina; material ChatGPT development/engineering assistance is disclosed | Original ARES software and documentation are distributed under the MIT License; see `LICENSE`. This license does not override third-party rights, dataset terms, or unresolved asset provenance. |

| `mars_hero.png` | NASA/JPL-Caltech Viking Orbiter mosaic, sourced from [NASA Science — Mars Planet Globe](https://science.nasa.gov/resource/mars-planet-globe/). The source JPEG was resized and converted to PNG for ARES, replacing an image of unverified origin. | Credit NASA/JPL-Caltech. Follow [NASA Images and Media Guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/). NASA has not endorsed or certified ARES. The image is not part of the ARES MIT-licensed original software. |

| Owner's full MOLA GeoTIFF | File absent here; exact metadata was supplied by the owner in the master directive | Full-file identity, processing history, original URL and vertical reference remain unresolved; preserve the original |
| Supplied real 256 × 256 MOLA sample | Actual Rasterio/sample tests executed; all 65,536 pixels matched a nearest-neighbor virtual warp of a public USGS COG window | This does not prove the absent full file's identity or entire processing history; retain comparison evidence and distinguish the derivative from native PDS products |
| Public PDS/USGS scientific references | Native product-window comparison and a separate 4 samples/degree global reference were actually evaluated | Cite exact products/labels/methods and preserve uncertainty; do not attribute their results to the absent full owner raster |
| NASA Trek Viking MDIM21 basemap | External service URL and visible NASA Mars Trek attribution are present in `script.js`; imagery is distinct from MOLA elevation data | Verify service availability and applicable data/service attribution terms for the event; browser tests isolated external tile requests |
| Leaflet 1.9.4 | Existing dependency vendored; BSD 2-Clause license retained | Retain `THIRD_PARTY_NOTICES.md`, upstream license and `vendor/SHA256SUMS` |
| Three.js 0.160.1 and OrbitControls | Existing dependency vendored; MIT license retained | Retain `THIRD_PARTY_NOTICES.md`, upstream license and `vendor/SHA256SUMS` |
| Globe surface | DEM-derived elevation-colored canvas, or an identified fallback | Label rendering as a visualization, not a photograph or live orbital observation |

See [the detailed hero investigation](docs/ASSET_INVESTIGATION.md) for measured file evidence, actual NASA-source access outcomes, and an owner-approved replacement option. The image was not replaced. Metadata absence and appearance do not establish NASA or AI origin.

Scientific references and the supplied sample have now been used in actual validation; the full original raster is still unavailable. Refer to the scientific input/provenance documentation and comparison evidence rather than treating a filename as a citation.

The [competition assessment](docs/COMPETITION_READINESS.md) distinguishes failed live access from indexed official-domain material. The owner must review the actual current publication/submission terms and third-party permissions before an external submission. Original ARES software licensing is documented in LICENSE.