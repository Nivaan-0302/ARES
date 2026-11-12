# Measured performance and reliability

The confirmed bottleneck was repeated CRS/geometry/unit validation on every neighborhood/row read. Metadata is now cached only for an **open read-only Rasterio handle**, using weak keys and a lock. New opens are revalidated, writers are not cached, callers receive independent metadata dictionaries, and reader handles are not retained. Dataset-wide arrays are not loaded just to accelerate point lookup.

The following local Flask test-client comparison used the same installed environment and real 256 × 256 sample:10 measured repetitions after2 warmups for each endpoint. It compares the previous corrected copy with this sprint, not the pristine original project. It excludes network/browser latency.

| Endpoint | Prior median ms | Sprint median ms | Ratio |
| --- | ---: | ---: | ---: |
| `/api/elevation` | 10.353 | 8.059 | 1.28× |
| `/api/terrain-region` | 50.926 | 18.865 | 2.70× |
| `/api/mission-route` | 157.952 | 39.628 | 3.99× |

Raw measurements and process-RSS observations are in [endpoint_performance.json](evidence/endpoint_performance.json). Workloads, caching and timing noise matter; these ratios are not hosted concurrency guarantees or proof of improvements for every raster.

On the separately prepared2 MB PDS 4 ppd reference, global model creation took93.1ms and a warm cached access0.097ms in one recorded run. Three recorded real-reference routes completed successfully: dateline118.316km, high-latitude102.600km, opposite-hemisphere10683.422km. See [global reference results](evidence/global_reference_results.json). Their timings do not establish full128ppd original-file performance.

Existing safe controls remain: one bounded global model keyed by file identity per process, a cold-load lock, shared/cancelable frontend region requests, one final mission profile, bounded concurrent heavy API work, GPU cleanup and hidden-view render suspension. Client cancellation prevents stale display; it does not forcibly terminate already executing server calculations.

Still unmeasured: cold I/O and peak memory for the full local2.12 GB derivative, production-host contention, sustained load, proxy/client network costs and resource sizing across multiple workers. The full raster need not be held entirely in RAM, but its storage and access pattern must be tested. More worker processes duplicate caches and independent analysis limits. Start with one process and measure representative traverses before scaling.

Reproduce local timings with `python scripts/profile_endpoints.py --repeats 10` after setting `ARES_DEM_PATH` to an authorized raster. No destructive benchmark, original-data modification or public load test was performed.
