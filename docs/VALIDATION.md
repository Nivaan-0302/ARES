# Reproducing validation

Use Python 3.12 and the isolated environment from the README. The final recorded results are in [scientific validation](SCIENTIFIC_VALIDATION.md) and [machine-readable outcomes](evidence/final_verification.json).

## Backend and numerical tests

Keep the real sample external to source control. Prepare the optional small global reference in a fresh temporary directory:

```bash
python scripts/prepare_global_reference.py --output /tmp/ares-reference-new
export ARES_SAMPLE_PATH='/absolute/path/to/mola_sample_256.tif'
export ARES_GLOBAL_REFERENCE_PATH='/tmp/ares-reference-new/pds_megdr_4ppd_reference.tif'
export GDAL_PAM_ENABLED=NO
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s . -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -p 'test_*.py' -v
```

The original full DEM is not required for these supplied-sample and reference tests. Two older smoke tests require the actual full dataset and skip when its default/configured path is absent. They must not be pointed at an unrelated sample and described as full-data validation. Other sample/reference tests skip explicitly when their environment paths are absent. The reference preparation script downloads the documented2,073,600-byte public PDS product, verifies its hash, converts byte order/format without resampling, and refuses existing output files.

The root discovery command also executes three existing top-level A* assertions, separately from the42 named unittest cases. The tests folder runs30 named cases when the real sample and reference paths are supplied. Final outcome:70 passed and2 full-original-DEM skips across72 named cases. No final failed suite was hidden. Some warning logs deliberately exercise missing-data and private-error branches; those branches are expected assertions, not passing scientific observations.

## Frontend tests

```bash
node --test tests/frontend_regressions.cjs
python -m pip install -r requirements-browser.txt
# Use a provisioned Chromium, or install Playwright's supported browser separately:
python -m playwright install chromium
python tests/frontend_browser_smoke.py
```

A system `chromium` is detected automatically; `ARES_CHROMIUM_EXECUTABLE` can select another supported binary. Eight Node cases and two explicitly synthetic API/browser scenarios passed. Synthetic responses exist only in the isolated test fixture, never as production terrain substitutes.

For the real-backend check, start ARES with `ARES_DEM_PATH` pointing to the actual256 × 256 sample and run:

```bash
python tests/frontend_real_backend.py --url http://127.0.0.1:5001
```

Normal WebGL and deliberately disabled WebGL scenarios both used actual Flask/Rasterio terrain API responses. Route plotting,25 profile samples,64 × 64 hazards, shared controls, reset/error states, keyboard tabs, and390px layout were exercised. External Trek image requests were isolated; those scenarios do not verify NASA basemap service availability. The partial sample intentionally cannot produce a full-planet relief texture or real global route.

## Optional authoritative comparisons

```bash
python scripts/compare_pds_reference.py /path/to/mola_sample_256.tif --output /tmp/ares-native-reference
python scripts/compare_usgs_window.py /path/to/mola_sample_256.tif --output /tmp/ares-new-usgs-comparison.json
```

These commands make bounded public HTTPS range requests. The USGS comparator refuses existing report files and caps per-request/total bytes; it preserves TLS verification through a loopback range broker if bundled GDAL TLS cannot use the session trust configuration. No full large COG is downloaded. Native PDS bins and a transformed USGS derivative are different comparisons, not independent ground truth.

## Evidence and scope

Current exact software versions are in `requirements-tested.txt`, `requirements-browser.txt` and [dependencies](DEPENDENCIES.md). Syntax parsing, `pip check`, real-data calculations, browser tests, performance measurements and physical scientific accuracy are separate evidence categories. Keep the input hash, source labels, model assumptions, commands, outputs and skips together. See [performance](PERFORMANCE.md), [provenance](DATASET_PROVENANCE.md), and [remaining limitations](SPRINT_REPORT.md#h-remaining-limitations).
