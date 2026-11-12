# Deployment readiness and hosting preparation

ARES has been run and tested locally with an isolated Python environment, actual Flask/Rasterio, and the supplied real terrain sample. A private loopback Gunicorn process was used for real-backend browser checks. **No public deployment was performed or authorized.** Tests with the regional sample and a separate public global reference do not establish production performance with the absent original multi-gigabyte DEM.

## Runtime and data requirements

Use Python 3.12. The sprint environment recorded Python 3.12.14, Flask 3.1.3, NumPy 2.5.4, Rasterio 1.5.2, GDAL 3.12.2, PROJ 9.8.1, and Gunicorn 25.3.0; see [dependency evidence](docs/evidence/dependencies.json). Install in a new virtual environment using the repository manifests and tested lock instructions in the README. Do not modify system Python.

A static host alone cannot run ARES: the frontend makes relative `/api/...` requests to a Python Flask backend that reads a local compatible raster. A static-only upload can show assets but cannot supply terrain, routing, readiness, or relief APIs.

The full application requires a supported global Mars elevation raster, persistent storage, and read permission for the service account. The owner reports an approximately 2.12 GB original file; that file was not supplied here. Size storage for the actual raster, application and operational logs, and measure real peak memory and concurrent I/O. Do not copy an entire raster into memory merely because its on-disk size fits.

## Practical hosting options

| Option | Suitable conditions | Main limit to verify |
| --- | --- | --- |
| Linux VM or container with a mounted persistent volume | Python/GDAL-compatible runtime, read-only DEM mount, TLS proxy, controllable memory/timeouts | Full-raster disk/I/O and concurrent route latency |
| Managed Python/container service with persistent storage | Provider supports the required wheel/runtime, volume size, startup and request budgets | Volume availability, cold starts, worker memory and request timeout |
| Static frontend plus separate Python API | Only if both URLs/proxy paths are configured and the API has terrain storage | Same-origin reverse proxy is simplest; cross-origin deployment requires deliberate narrow CORS policy |
| Static-only or short-lived function runtime | Interface preview only unless a separately validated API is provided | Cannot assume Flask/GDAL and multi-gigabyte persistent terrain fit a function's limits |

No provider was selected, infrastructure purchased, or application published.

## Local and production-process commands

For local development, use `python terrain_api.py` and `http://127.0.0.1:5001`; the Flask development server binds loopback and disables debug mode.

A starting Linux WSGI configuration, after authorized raster provisioning and installation of `requirements-production.txt`, is:

```bash
export ARES_DEM_PATH='/srv/ares-data/your-validated-dem.tif'
export ARES_MAX_CONCURRENT_ANALYSES=4
gunicorn --bind 127.0.0.1:8000 --workers 1 --threads 4 --timeout 120 terrain_api:app
```

This is a configuration to measure, not a deployment or capacity guarantee. Place a supported TLS reverse proxy in front of it when hosting is approved. Forward the same origin's `/`, frontend/vendor assets, `/api/`, `/healthz`, and `/readyz` to the reviewed application routes. Do not add a proxy alias that exposes the source directory or DEM. Keep Flask debug disabled.

The current frontend and backend share one origin, so they require **no CORS package or wildcard CORS header**. If a separate origin is intentionally introduced, configure a narrow allowed origin and verify actual browser requests; do not enable unrestricted CORS preemptively. Trust forwarded proxy headers only for the actual controlled proxy topology.

## Configuration, status and resource behavior

| Setting/check | Current meaning |
| --- | --- |
| `ARES_DEM_PATH` | Configured raster; default is `data/mola128_mola64_merge_90Nto90S_SimpleC_clon0.tif` relative to the application |
| `ARES_MAX_CONCURRENT_ANALYSES` | Integer 1–64, default 4; per-process concurrency limit on expensive analysis routes |
| `GET /healthz` | Process liveness, independent of dataset availability |
| `GET /readyz` | 200 for metadata-compatible global coverage; 503 for absent/incompatible raster or regional-only coverage |
| Regional-only readiness | A valid sample can report regional capability while global/full-app readiness remains 503 |
| Busy response | 503 plus `Retry-After: 1`; the frontend exposes bounded retries and a user retry control |

Metadata-compatible coverage is not proof of authenticity, valid data in every pixel, a verified vertical datum, or rover safety. Unknown terrain remains unavailable rather than being substituted with an automatically safe value. A configured regional sample can support the tested nearby regional mission while global requests remain unavailable.

Global models and metadata caches are process-local. Restart/reload workers when replacing the configured dataset; do not assume an in-place raster swap refreshes every cache. More workers duplicate caches and increase simultaneous raster access. Four workers with four analysis slots allow up to sixteen expensive operations. Start with one worker and measure before increasing concurrency.

## Security and operational release checklist

- Run under a least-privilege service account; mount the original DEM read-only and retain its checksum. Keep credentials, `.env`, private logs, backups, and source out of public routes.
- Retain the explicit asset allowlist and safe vendor serving. Verify Python files, dotfiles, data paths, traversal paths, and future config files remain unavailable through both Flask and the proxy.
- Configure TLS, reverse-proxy connection/request-rate limits, bounded request times, log retention and monitoring. The semaphore is a work bound, not a distributed rate limiter.
- Check live `/healthz` and `/readyz`, known elevation/slope/region requests, regional and global route cases, invalid inputs, NoData, busy responses and dataset errors on the intended host.
- Re-run browser tests against the real host: map/globe synchronization, actual API status, profile gaps, retry, keyboard operation, mobile layout, and WebGL fallback. The executed browser runs isolated NASA Trek tiles; external basemap availability still needs a separate check.
- Benchmark cold and warm global loads, representative routes and expected concurrency with the actual full DEM. Local sample benchmarks do not predict full-source memory/I/O or public latency.
- Confirm the original DEM's vertical reference and provenance, image permissions, owner distribution decision, and applicable submission terms. Hosting an unknown-origin image is not cleared by testing its bytes.
- Preserve exact test commands/results and record any skipped or failed check. Obtain the owner's publication/deployment approval only after the concrete release is reviewable.
