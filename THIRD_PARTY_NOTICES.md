# Third-party frontend components

ARES was created and is directed by **Nivaan Raina**. The notices below apply
to bundled third-party components only; they do not select or change the
license of original ARES material.

The existing frontend dependency versions are included locally so the core
interface does not require a CDN connection after the application is loaded.
The upstream files and license texts are preserved without modification.

| Component | Version | Upstream distribution | License | Local files |
| --- | --- | --- | --- | --- |
| Leaflet | 1.9.4 | https://cdn.jsdelivr.net/npm/leaflet@1.9.4/ | BSD 2-Clause | `vendor/leaflet-1.9.4/` |
| Three.js, including OrbitControls | 0.160.1 | https://cdn.jsdelivr.net/npm/three@0.160.1/ | MIT | `vendor/three-0.160.1/` |

Leaflet copyright: 2010–2023 Volodymyr Agafonkin; 2010–2011 CloudMade.
See `vendor/leaflet-1.9.4/LICENSE` for the complete conditions and disclaimer.

Three.js copyright: 2010–2023 three.js authors.
See `vendor/three-0.160.1/LICENSE` for the complete conditions and disclaimer.

Leaflet JavaScript, CSS, and marker/layer images came from the package's
`dist/` directory. Three.js files came from `build/three.module.js` and
`examples/jsm/controls/OrbitControls.js`. Both license files came from their
package roots. SHA-256 digests of the supplied local files, including license
texts, are recorded in `vendor/SHA256SUMS`; run `sha256sum -c SHA256SUMS` from
the `vendor/` directory to check them. These digests detect local changes;
they are not an independent signature of upstream authorship.

This inventory covers the bundled frontend libraries. Dataset provenance,
the hero image, AI assistance, and original-project distribution decisions
are recorded separately in the project documentation and asset register.
