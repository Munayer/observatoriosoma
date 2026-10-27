# Observatório SOMA

An open mirror of the mining operator's software stack, built for the public sector out of
public data.

Prototype, version 0.1.0. Runs on simulated imagery out of the box; the production provider
is written against live Copernicus endpoints.

---

## Documentation

Everything written about this project lives in one file: **`docs/00-SOMA.md`** — summary,
full report, technical architecture, demonstration transcript, GIS prototype notes, and the
sourced evidence base behind every factual claim, each numbered 1–7 with plain decimal
sub-numbers (2.1, 2.9.3 — no roman numerals) and closed out with an ISO 690 reference list
that every inline `[N]` marker in the text links straight back to. The document is bilingual,
English and Brazilian Portuguese, full parity, same numbering in both.

Three companion HTML files, each self-contained (no build step, no server):

- **`report.html`** — the document above as a minimal reading view, with an EN/PT
  language toggle and a section rail.
- **`map.html`** — a GIS prototype: the four demonstration sites on a map, each with
  its cross-agency reference chain (ANM, IBAMA, ICMBio, FUNAI, INCRA, ANA) and an
  evidence-thread panel, exportable as CSV or GeoJSON. Kept as its own file because it needs
  to fetch map tiles over the network. See §6 of the report for how and why.
- **`dashboard.html`** — the operational view, the four-site case-queue demonstration.

`docs/03-catalogues.xlsx` is the reference workbook: every public data source, open-source
component, jurisdiction (cadastre, royalty regime, dam-safety rule, due-process basis) and
the vendor landscape this architecture responds to, plus a live cost model.

### Minas Gerais: strategic minerals (real ANM data)

- **`mg.html`** — the consolidated report on active ANM processes for lithium, manganese,
  rare earths, niobium, nickel, copper and cobalt in Minas Gerais, with a phase chart and a
  live count from ANM's SIGMINE API set against the extract.
- **`mg-mapa.html`** — the GIS: processes per municipality (IBGE mesh) from the extract,
  and the live process polygons queried from SIGMINE
  (`geo.anm.gov.br/arcgis/rest/services/SIGMINE/dados_anm/MapServer/0`), with a
  per-mineral check of the API against the extract.

Both are generated from the Observatory's workbook and report:

```bash
python build_mg.py anm_mg_municipios_2026-10-17.xlsx Minerais_estrategicos_MG_relatorio_consolidado_2026-10-17.docx
```

This writes `mg.html` and `data/mg/` (summary, per-municipality counts, the IBGE mesh and a
CSV of the processes). Holder names are published for companies and public bodies only,
never for natural persons; each process links to its record in ANM's Cadastro Mineiro. The workbook itself stays out of the repository.

---

## Run it

No installation, no network, no configuration:

```bash
cd observatoriosoma
PYTHONPATH=src python3 -m soma.cli demo --out data/out
PYTHONPATH=src python3 -m soma.cli ledger verify --root data/out/cases
python3 tests/run_tests.py
```

The four-site demonstration and the dashboard:

```bash
PYTHONPATH=src python3 -c "
from soma.portfolio import run_portfolio
from soma.dashboard import build
run_portfolio('data/out')
build('data/out', 'dashboard.html')"
```

Then open `dashboard.html` in any browser.

### Requirements

| Tier | Packages |
|---|---|
| **Core (mandatory)** | Python ≥ 3.10, `numpy` |
| **Recommended** | `scipy`, `scikit-image`, `matplotlib`, `Pillow` |
| **Production (live imagery)** | `pystac-client`, `rasterio`, GDAL |
| **Optional accelerators** | `shapely`, `pyproj`, `dask` |

The core has **no mandatory geospatial dependencies**. GDAL, rasterio, shapely and pyproj
are optional accelerators, never requirements. A municipal environment agency with one
laptop and no procurement budget can run the detection library — that was a design goal, not
an accident.

---

## What it does

Eight questions, and it refuses to answer others:

1. Is there extraction where no title exists at all?
2. Is extraction outside the polygon of the title that authorises it?
3. Is extraction inside an area where it is categorically prohibited?
4. Is a title recorded as dormant, suspended or merely applied-for showing activity?
5. Is the rate of expansion changing, and when did it change?
6. Is a tailings structure moving, and is it accelerating?
7. Is the impounded water surface approaching the extent of its impoundment?
8. Is what has been declared consistent with what is visible, and with the operator's own
   other filings?

---

## The design contract

> Every number this library puts on a screen must be re-derivable, by a third party, from
> public inputs, using only the manifest that accompanies it.

Nothing here returns a bare number. Detectors return `Observation` objects; cross-checks
return findings; both carry an `EvidenceManifest` recording inputs, algorithm versions,
parameters and hashes. Manifests are appended to a hash-chained ledger, so deleting or
editing a past finding is detectable.

### What it refuses to do

- Predict tailings dam failure. It reports that a crest is moving and recommends an
  engineering visit.
- Convert a footprint into tonnes and assess royalties. It ranks sites for audit and says
  why.
- Report turbidity as contamination. It triggers a sampling campaign.
- Count area inside the boundary tolerance against a title holder.
- Advance a case without a named human.
- Publish anything about a party that has not been notified.
- Issue an administrative notice or a judicial dossier from simulated evidence.

Each of those refusals has a test behind it.

---

## Due process, enforced in code

```
observed → screened → corroborated → notified → contested → reviewed
                          ↓              ↓          ↓          ↓
                      dismissed ←────────┴──────────┴──── substantiated → referred → closed
```

- Every transition names a person and a role; automated advancement raises `DueProcessError`.
- A notice requires a **corroborated** case — a single-sensor detection is not a sufficient
  basis for a coercive act.
- A case cannot be reviewed while the response window is open.
- Nothing is public before notification; a notified-but-unresolved case is visible to the
  notified party and to nobody else.
- A dismissal publishes a summary. Being cleared is a public fact.

In the bundled four-site demonstration, the only case publicly visible is the one that was
**cleared**. That is the correct behaviour.

---

## Layout

```
src/soma/
  geom.py            ellipsoidal geometry (authalic-latitude polygon area), no GIS stack
  scene.py           the unit of observation; content hashing; fixed-stretch rendering
  indices.py         NDVI, NDWI, MNDWI, NDMI, NBR, BSI, NDTI — with citations
  providers/
    base.py          SceneProvider interface
    stac_sentinel2.py  CDSE / Element 84 Earth Search — production
    synthetic.py     deterministic simulator with known ground truth
  detectors/
    base.py          Observation; three-state reliability (ok | degraded | unusable)
    footprint.py     disturbed-surface delineation by published spectral rule
    water.py         pond extent, turbidity gradient, freeboard proxy
    change.py        Theil–Sen trend, guarded breakpoint search, observation gaps
    deformation.py   InSAR velocity screen (EGMS or self-processed Sentinel-1)
    volume.py        DEM differencing with a two-term error model
  crosscheck/
    cadastre.py      inside / outside / indeterminate, with a ±25 m holder-favourable tolerance
    declaration.py   peer intensity, cross-filing consistency, audit priority
  evidence.py        manifest, canonical JSON, hash-chained ledger, replay recipe
  cases.py           case state machine with due process enforced
  dossier.py         five translations; Brazilian and EU legal frames; synthetic guard
  render.py          evidence images (scale bar, north arrow, legend) and charts
  pipeline.py        end-to-end run for one site
  portfolio.py       the four-site demonstration
  dashboard.py       self-contained HTML build
  cli.py             soma demo | ledger | case
tests/               49 tests; pytest, or tests/run_tests.py with no pytest installed
```

---

## Going live

Replace the provider:

```python
from soma.providers import StacSentinel2Provider
provider = StacSentinel2Provider(catalogue="cdse", token=my_token)
```

Everything downstream is unchanged. Then, in order:

1. Measure precision and recall on real imagery over sites with known outcomes, and publish
   the confusion matrix. This step validates or kills the project and belongs first.
2. Calibrate thresholds to local ground truth. The humid-tropical defaults are defaults.
3. Wire the registry connectors (SIGMINE, CFEM, SIGBM, or the national equivalents).
4. Stand up InSAR — EGMS in Europe, ISCE2/SNAP + MintPy elsewhere.
5. Work one real case end to end with a real official, through notification and response.

---

## Licence

Intended for release under an OSI-approved licence (Apache-2.0 or EUPL-1.2) and submission
to the Digital Public Goods registry, following QGIS's recognition as a DPG in February 2025.

Copernicus Sentinel data is free, full and open. Everything this depends on is
OSI-licensed — with one exclusion recorded in `docs/03-catalogues.xlsx`: **MinIO's community
edition was archived over 2025–26** and must not be adopted.

---

## Status, stated plainly

This is a prototype that has never seen a real satellite image. It has been exercised
end-to-end against a simulator with known ground truth, where it recovered areas to within a
few per cent, recovered a simulated growth-rate change of 0.7 → 4.5 ha/month as 0.70 → 4.65,
and correctly declined to report a rate change on a steady site. That is evidence the method
is sound and no evidence at all about its false-positive rate on real scenes.

The first thing anyone should do with it is point it at the Copernicus archive and find out.
