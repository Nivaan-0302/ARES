# Dependencies and reproducibility report

Necessary runtime and browser-test dependencies were installed in a **new isolated virtual environment**. System-wide Python was not modified. The previous iteration's “dependencies unavailable” limitation no longer applies to the sprint's recorded checks.

Tested: Python **3.12.14**, Rasterio-bundled GDAL **3.12.2**, PROJ **9.8.1**. Node **v24.22.1** and an existing Chromium **Chromium 156.0.8078.79 built on Debian GNU/Linux 13 (trixie)** were used. Browser binary provisioning was already available; no system package installation was needed.

| Installed Python package | Version |
| --- | --- |
| affine | 3.0.1 |
| attrs | 26.1.0 |
| blinker | 1.9.0 |
| certifi | 2026.10.23 |
| click | 8.5.1 |
| Flask | 3.1.3 |
| greenlet | 3.5.6 |
| gunicorn | 25.3.0 |
| itsdangerous | 2.2.0 |
| Jinja2 | 3.1.6 |
| MarkupSafe | 3.0.4 |
| numpy | 2.5.4 |
| packaging | 26.3 |
| playwright | 1.62.0 |
| pyee | 13.0.1 |
| pyparsing | 3.3.3 |
| rasterio | 1.5.2 |
| typing_extensions | 4.16.0 |
| Werkzeug | 3.1.9 |

`requirements.txt` holds minimal runtime compatibility ranges; it is not evidence that every permitted version was tested. `requirements-production.txt` adds Gunicorn. `requirements-tested.txt` records exact tested runtime/production pins. `requirements-browser.txt` includes those pins plus the optional exact Playwright environment. Browser binaries remain separate. `python -m pip check` passed.

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-tested.txt
# Optional browser verification:
python -m pip install -r requirements-browser.txt
```

Flask, NumPy and Rasterio are backend dependencies; Gunicorn is an optional Linux WSGI server. Playwright/Chromium and Node are test tooling, not runtime terrain services. Leaflet and Three.js are vendored with original upstream notices. No Flask-CORS, SciPy, pyproj, requests or pytest package is required by the application. The optional profiling script's RSS measurement uses Linux's standard-library resource module.

This is the tested Linux/Python 3.12 environment, not a claim of universal OS or package-version compatibility. Hosting resource requirements for the owner's full2.12 GB derivative still need measurement. Keep dependency updates reviewable and rerun the numerical, API and browser regressions after changes.
