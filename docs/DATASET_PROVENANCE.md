# ARES dataset provenance

Research and numerical comparisons performed on **12 November 2026**. Project
creator and lead: **Nivaan Raina**. Research, implementation, and reporting were
AI-assisted. This report distinguishes the supplied sample, owner-reported
full-raster metadata, authoritative product documentation, and numerical
comparisons. Agreement with another MOLA-derived product is a consistency
check, not independent observational ground truth.

## Findings and confidence

| Evidence layer | Established result | Limit |
| --- | --- | --- |
| Supplied local sample | A real 256 × 256 GeoTIFF was available; its 65,536 elevations are finite, ranging from −1,558 to −960 | This equatorial window does not establish full-planet coverage, polar behavior, or original processing history |
| Owner's full GeoTIFF | The owner supplied detailed Rasterio metadata for a 46,081 × 23,041 geographic raster | The complete owner file was not available for independent inspection or hashing |
| Native NASA PDS MEGDR | Authoritative labels establish units, latitude/longitude convention, pixel-area registration, and the documented native topography reference | These labels do not automatically establish every property of a later USGS/owner derivative |
| Public USGS COG | Metadata identifies a closely named 46,081 × 23,041 projected MOLA raster; its georeferenced window reproduces every supplied sample value under the stated comparison | Exact sample agreement does not prove whole-file identity, the original download URL, or a unique conversion history |

## Supplied files

The full raster is named
`mola128_mola64_merge_90Nto90S_SimpleC_clon0.tif`. The owner reports Int16,
one band, nodata −32768, scale 1, offset 0, `AREA_OR_POINT=Area`,
`ESRI:104905` / `GCS_Mars_2000`, and dimensions 46,081 × 23,041.
Its reported affine coefficients are:

```text
a = 0.00781224569558698   b = 0   c = -180
d = 0                     e = -0.00781224569558698   f = 90
```

Reported outer bounds are west −180, south −90.0019530720196,
east 179.99609389834364, north 90 degrees. These values are retained as
reported, including their small departure from nominal global bounds; they
must not be silently replaced with an ideal 46,080 × 23,040 grid.

The supplied `mola_sample_256.tif` is a window near 0° latitude, 0° longitude,
reported extracted without intentional resampling. Its SHA-256 is:

```text
c99f92579062c39934295690bd0a0644d3e73a60a1c7fbf14c93d714d6198981
```

Its measured bounds are west −1.005826622711112, south −0.9970378621971483,
east 0.994108275359155, north 1.0028970358731186 degrees. It has the reported
geographic CRS and nodata value, with no nodata pixels in this particular
sample. Missing-data behavior therefore also requires synthetic masked tests.
Band-unit metadata is absent. Neither that absence nor the horizontal WKT
establishes a vertical reference.

## Authoritative native product

The reference family is **Mars Global Surveyor MOLA MEGDR**,
`MGS-M-MOLA-5-MEGDR-L3-V1.0`, credited by the NASA PDS profile to Smith,
Zuber, Neumann, Guinness, and Slavney (2003). The Geosciences Node now points
to its maintained PDS4 topography-derived bundle; the original PDS3 archive
remains linked. The inspected PDS3 topography labels have product version 2.0
and creation date 21 March 2003. The inspected PDS4 label is version 1.1,
whose September 2026 history corrects map-scale/transform metadata; a label
revision is not evidence that the owner used that revision.

Sources accessed successfully:

- [PDS Geosciences MEGDR overview](https://pds-geosciences.wustl.edu/missions/mgs/megdr.html)
- [NASA PDS dataset profile and citation](https://pds.nasa.gov/ds-view/pds/viewProfile.jsp?dsid=MGS-M-MOLA-5-MEGDR-L3-V1.0)
- [Maintained PDS4 bundle](https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/)
- [MEGDR software interface specification](https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/document/egdrsis.htm)
- [Pixel registration and map-projection definition](https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/catalog/dsmap.cat)
- [Example native topography PDS3 label](https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/megt44n000hb.lbl)
- [Corresponding PDS4 label](https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/megt44n000hb.xml)

The native labels establish:

- Planetocentric latitude, east-positive longitude, with native tiles expressed
  in the 0°–360° longitude domain.
- Signed, most-significant-byte-first 16-bit topography values in meters.
- Median topography within bins; unobserved bins can contain interpolated
  elevations, rather than direct laser measurements.
- Topography defined as planetary radius minus areoid radius. The inspected
  native label names Goddard Mars potential model **GMM3 (mgm1025), degree and
  order 50**, for the areoid. IAU2000 identifies the coordinate reference and
  must not be substituted for this vertical model.
- Pixel-area registration: the first pixel center is half a bin east and
  south of the western and northern outer edges. Integral PDS line/sample
  numbers denote centers; the first line/sample is 1.

At 128 pixels per degree, the inspected equatorial tiles contain 11,520
columns × 5,632 rows over 90° × 44°. The native 128-pixel/degree tiled coverage
extends to ±88°, not both poles. A nominal assembled 360° × 180° grid at that
spacing would contain 46,080 × 23,040 area pixels; this arithmetic is not a
claim that such a single native 128-pixel/degree polar-complete file exists.

## Closest identified public derivative

The following public USGS-hosted Cloud Optimized GeoTIFF was successfully
accessed with bounded HTTPS byte ranges:

[USGS MOLA 128/64 merged global COG](https://asc-pds-services.s3.us-west-2.amazonaws.com/wms_basemaps3/Mars/MOLA/mola128_mola64_merge_90Nto90S_SimpleC_clon0_cog.tif)

Observed metadata: total object size 1,929,690,228 bytes; dimensions 46,081 ×
23,041; LZW compression; nodata −32768; spherical Mars equidistant cylindrical
projection recognized as `ESRI:103885`; sphere radius 3,396,190 m. The pixel
spacing is approximately 463.0836 m, with upper-left corner
(−10,669,677.095995119, 5,334,954.318897561) m. This is **projected metadata**,
unlike the owner's reported geographic `ESRI:104905` metadata.

The [USGS 463 m catalog record](https://astrogeology.usgs.gov/search/map/mars_mgs_mola_dem_463m)
was discoverable through indexed official-page content, but direct retrieval
returned HTTP 403 in this environment. That catalog describes a related
planetocentric, east-positive derivative and polar gap filling, and lists
[this download](https://planetarymaps.usgs.gov/mosaic/Mars_MGS_MOLA_DEM_mosaic_global_463m.tif).
The latter URL was not used as the comparison source and is not asserted to
be identical to the accessed COG.

The indexed catalog describes a GMM-2B-based areoid, whereas the inspected
native PDS label names GMM3 (mgm1025). The COG header supplies no independently
verified vertical-datum declaration. These records must not be conflated:
the exact vertical model inherited by the owner's GeoTIFF remains unresolved.

The matching 46,081 × 23,041 dimensions show that the extra row and column
already exist in the closest public projected derivative. They do not, by
themselves, establish gridline registration, duplicated meridians, or a specific
resampling algorithm. The name suggests merged 128/64-resolution ancestry;
it is not sufficient evidence for an exact merge or polar-processing history.

A current Rasterio default-transform experiment from the COG CRS to the owner's
geographic CRS suggested **46,082 × 23,041** and different affine coefficients.
It did not reproduce the reported owner grid. Thus a simple claim that the
owner file is an unchanged default conversion is unsupported. Its changed CRS
and spacing are consistent with a conversion/reprojection, but the commands,
options, software version, clipping, and registration decisions remain unknown.

## Executed reference comparisons

| Comparison | Pixels | Exact matches | Mean absolute difference | RMSE | Maximum absolute difference |
| --- | ---: | ---: | ---: | ---: | ---: |
| Native PDS containing-bin values versus sample | 65,536 | 10,113 | 3.302597 m | 5.166903 m | 84 m |
| USGS COG warped by nearest neighbor to the sample grid | 65,536 | 65,536 | 0 m | 0 m | 0 m |

Native reference values came from four tiles surrounding the equator/prime
meridian: `megt44n000hb`, `megt44n270hb`, `megt00n000hb`, and `megt00n270hb`.
Their downloadable `.img` and accompanying `.lbl` URLs, requested byte ranges,
and range hashes appear in [native comparison evidence](evidence/native_pds_comparison.json).
Each sample pixel center was mapped to its native PDS area bin; no offset
was fitted. For sample array index (128,128), sample elevation was −1517 m
and native PDS elevation −1515 m. This difference does not establish an error:
the sources and registration/derivation differ.

The closer COG comparison used a nearest-neighbor virtual warp to the supplied
sample's exact CRS, affine transform, width, and height. Verified HTTPS ranges
were brokered locally for GDAL after its own TLS client could not use the
session trust configuration; TLS verification was not disabled. The comparison
transferred **737,280 bytes**, not the 1.93 GB object. See
[USGS comparison evidence](evidence/usgs_sample_comparison.json).

The exact window agreement strongly supports membership in this USGS derivative
family at the tested location. It does not prove a unique processing history,
whole-file checksum equality, a vertical datum, or latitude handling away from
the equatorial window. No source was treated as independent rover-scale ground
truth, and zero sample difference is not a zero scientific uncertainty claim.

A separate native 4-pixel/degree global topography reference was downloaded
for actual global-routing checks: 1,440 × 720 pixels, 2,073,600 bytes,
SHA-256 `25f16fb7aaf857898dcf98bc4f841341a24f8b9f7e98453ca083bc45d897ca2c`.
Its [download](https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg004/megt90n000cb.img)
and [label](https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg004/megt90n000cb.lbl)
are authoritative; its pixel-preserving temporary GeoTIFF conversion did not
resample values. It is a coarser reference, not the owner's full DEM. Results
are recorded in [global reference evidence](evidence/global_reference_results.json).

## Reproduction and bounded downloads

Run from the project root with the declared dependencies installed. Choose
new research output paths; keep original datasets separate and unchanged.

```bash
python -B scripts/compare_usgs_window.py /path/to/mola_sample_256.tif --output /separate/research/usgs-comparison.json
python -B scripts/compare_pds_reference.py /path/to/mola_sample_256.tif --output /separate/research/native-ranges
python -B scripts/prepare_global_reference.py --output /separate/research/global-reference
```

The recorded native comparison used 11,705,344 bytes across four bounded
ranges. The COG comparison used 737,280 bytes; a separate metadata-header
inspection read 1,048,576 bytes. The small global reference used 2,073,600
bytes. Metadata pages and labels add small transfers; these operation-level
counts are not a total network-byte accounting. No complete multi-gigabyte
DEM was downloaded, and the supplied sample and original owner dataset were
not overwritten. Reference binaries remain outside the source package.

## Remaining provenance work

1. Obtain the owner's original download URL, file hash, download date, and
   any source label or sidecar metadata.
2. Obtain the actual conversion commands/options and software versions,
   including resampling and extent/registration choices. Preserve both the
   downloaded original and derived file.
3. Resolve the derivative's vertical-model declaration against its own
   authoritative metadata; do not infer it from the horizontal WKT or from
   another version's catalog text.
4. Compare additional windows at midlatitudes, both polar merges, the seam,
   and source boundaries against the identified reference. The current
   equatorial sample cannot establish those behaviors for the owner's file.
5. Record full-file metadata and hashes locally, then provide a reproducible
   derivative recipe and citations without redistributing the original DEM.

The current work establishes a useful, independently fetched reference match
for the supplied window while keeping these whole-dataset questions explicit.
