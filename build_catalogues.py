"""Build docs/03-catalogues.xlsx — the reference workbook."""

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

FONT = "Arial"
HDR_FILL = PatternFill("solid", fgColor="1F3864")
HDR_FONT = Font(name=FONT, size=10, bold=True, color="FFFFFF")
BODY = Font(name=FONT, size=10)
BOLD = Font(name=FONT, size=10, bold=True)
TITLE = Font(name=FONT, size=14, bold=True, color="1F3864")
NOTE = Font(name=FONT, size=9, italic=True, color="595959")
INPUT_FONT = Font(name=FONT, size=10, color="0000FF")
INPUT_FILL = PatternFill("solid", fgColor="FFFF00")
FORMULA_FONT = Font(name=FONT, size=10, color="000000")
THIN = Side(style="thin", color="D9D9D9")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
TOP = Alignment(vertical="top")

wb = Workbook()


def sheet(name):
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    return ws


def write_table(ws, start_row, headers, rows, widths, table_name):
    for j, h in enumerate(headers, start=1):
        c = ws.cell(row=start_row, column=j, value=h)
        c.font = HDR_FONT
        c.fill = HDR_FILL
        c.alignment = WRAP
        c.border = BOX
    for i, r in enumerate(rows, start=start_row + 1):
        for j, v in enumerate(r, start=1):
            c = ws.cell(row=i, column=j, value=v)
            c.font = BODY
            c.alignment = WRAP
            c.border = BOX
    for j, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ref = (f"A{start_row}:{get_column_letter(len(headers))}"
           f"{start_row + len(rows)}")
    t = Table(displayName=table_name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
    ws.add_table(t)
    ws.freeze_panes = ws.cell(row=start_row + 1, column=1)
    return start_row + len(rows) + 1


def title_block(ws, title, subtitle):
    ws["A1"] = title
    ws["A1"].font = TITLE
    ws["A2"] = subtitle
    ws["A2"].font = NOTE
    return 4


# ---------------------------------------------------------------- Read me ---
ws = wb.active
ws.title = "Read me"
ws.sheet_view.showGridLines = False
ws["A1"] = "MINERVA — reference catalogues"
ws["A1"].font = Font(name=FONT, size=18, bold=True, color="1F3864")
lines = [
    ("", ""),
    ("Prepared for", "Bernardo Munayer"),
    ("Date", "19 August 2026"),
    ("Companion to", "00-MINERVA.md · minerva-report.html · minerva-dashboard.html"),
    ("", ""),
    ("What this workbook is",
     "Every public data source and every open-source component behind the proposed "
     "public-sector mining oversight platform, with licence, access method, cadence and "
     "maturity, so that a procurement or technical review can check the claims without "
     "reading the report."),
    ("", ""),
    ("Sheets", ""),
    ("  Public data",
     "Free, reusable data an authority can obtain today. Columns include the question "
     "each source actually answers."),
    ("  Open source",
     "Components to build with, with licence and a risk note where one applies."),
    ("  Capability mirror",
     "Layer-by-layer comparison of what the operator sees against what a public body "
     "can see, including the layers that CANNOT be mirrored."),
    ("  Commercial landscape",
     "The vendor products listed on the SourceForge page, sorted by function, plus the "
     "consolidation record."),
    ("  Jurisdictions",
     "Cadastre, production/royalty disclosure, protected-area, dam-safety and due-"
     "process basis for twelve jurisdictions, so a deployment outside Brazil or the EU "
     "knows what to wire up."),
    ("  Cost model",
     "A live model of data volume against the Copernicus free-tier quota. Edit the "
     "yellow cells."),
    ("", ""),
    ("Verification status",
     "Licences and endpoints were checked on 19 August 2026 against primary sources. "
     "Re-verify before any procurement decision: licences change, and at least one "
     "component on the watch list changed during 2025-26."),
    ("", ""),
    ("Colour convention",
     "Yellow fill with blue text = a cell you may edit. Black text = calculated. "
     "This follows the standard financial-model convention."),
    ("", ""),
    ("Important",
     "Nothing in this workbook is a statement about any specific company or site. The "
     "prototype it accompanies runs on simulated imagery."),
]
r = 3
for k, v in lines:
    ws.cell(row=r, column=1, value=k).font = BOLD if k and not k.startswith("  ") else BODY
    c = ws.cell(row=r, column=2, value=v)
    c.font = BODY
    c.alignment = WRAP
    r += 1
ws.column_dimensions["A"].width = 24
ws.column_dimensions["B"].width = 96
for row in range(3, r):
    ws.row_dimensions[row].height = None

# ---------------------------------------------------------- Public data ---
ws = sheet("Public data")
start = title_block(ws, "Public data sources",
                    "Free and reusable. Verified 19 Aug 2026 — re-verify before procurement.")
headers = ["Source", "Category", "Publisher", "Coverage", "Resolution / detail",
           "Cadence / latency", "Licence", "Access", "Endpoint or DOI",
           "Question it answers", "Notes"]
rows = [
    ["Sentinel-2 L2A", "Earth observation — optical", "Copernicus / ESA", "Global",
     "13 bands: 4 at 10 m, 6 at 20 m, 3 at 60 m; 290 km swath",
     "5 days (2 sats), 2–3 days mid-latitude; archive from 2015",
     "Copernicus free, full and open", "STAC, OData, S3, Sentinel Hub, openEO",
     "catalogue.dataspace.copernicus.eu/stac",
     "How large is the disturbed surface, and where exactly is its edge?",
     "L2A offset of −1000 applies from processing baseline 04.00. Getting this wrong "
     "shifts every index."],
    ["Sentinel-1 GRD/SLC", "Earth observation — radar", "Copernicus / ESA", "Global",
     "C-band SAR, 5×20 m IW", "6–12 days; constellation 1A+1C+1D since Apr 2026",
     "Copernicus free, full and open", "STAC, OData, S3",
     "catalogue.dataspace.copernicus.eu/stac",
     "Is anything happening under cloud, or at night?",
     "The only reason tropical monitoring works at all. Sentinel-1B failed 2022; 1D "
     "data opened 17 Apr 2026."],
    ["Sentinel-5P", "Earth observation — atmosphere", "Copernicus / ESA", "Global",
     "~3.5×5.5 km; SO2, NO2, CO, CH4", "Daily", "Copernicus free, full and open",
     "STAC, OData", "catalogue.dataspace.copernicus.eu/stac",
     "Is a smelter or processing plant emitting?",
     "Far too coarse for a single pit. Useful at plant scale only."],
    ["Copernicus DEM GLO-30", "Elevation", "Copernicus / ESA", "Global (~149 M km²)",
     "30 m; absolute vertical <4 m (90% LE); relative <2 m on slopes ≤20%",
     "Static, versioned", "Free worldwide (ESA user licence)", "S3, OData, Copernicus Browser",
     "doi.org/10.5270/ESA-c5d3d65",
     "How much material has been moved?",
     "Makes volumetric estimation a public capability. EEA-10 (10 m) is restricted to "
     "defined user categories."],
    ["NASADEM / SRTM", "Elevation", "NASA / USGS", "Global to 60°N/56°S", "30 m",
     "Static (2000 epoch)", "Public domain", "HTTP, AWS Open Data",
     "lpdaac.usgs.gov",
     "What did the ground look like before the boom?",
     "The only global pre-2010 elevation baseline."],
    ["Landsat 8/9 Collection 2", "Earth observation — optical", "USGS / NASA", "Global",
     "30 m multispectral; 15 m pan", "8 days combined; archive from 1984",
     "Public domain", "STAC, AWS Open Data", "landsatlook.usgs.gov",
     "What was here before Sentinel-2 existed?",
     "Indispensable for establishing the pre-observation baseline."],
    ["European Ground Motion Service", "Ground deformation", "Copernicus Land / EEA",
     "Copernicus participating states", "Millimetre LOS displacement; PS points",
     "Annual update; only the two latest releases stay online",
     "Copernicus free and open", "EGMS Explorer download",
     "egms.land.copernicus.eu",
     "Is a tailings dam crest moving, and is it accelerating?",
     "Exists explicitly for authorities monitoring dams and for mining subsidence. "
     "For Europe this removes the hardest processing layer entirely."],
    ["RADD forest disturbance alerts", "Deforestation", "Wageningen University / GFW",
     "13 South American, 6 Central American, 25 African, 5 SE Asian, 1 Pacific country",
     "10 m, Sentinel-1 based", "Near-real-time", "CC BY 4.0", "GEE, GFW download",
     "gee-community-catalog.org/projects/radd/",
     "Has forest been cleared here since the last look?",
     "Cite Reiche et al. 2021, Environ. Res. Lett., doi:10.1088/1748-9326/abd0a8."],
    ["DETER", "Deforestation", "INPE", "Brazilian Amazon and Cerrado", "Polygon alerts",
     "Near-real-time", "Open", "TerraBrasilis API and download",
     "terrabrasilis.dpi.inpe.br",
     "Which clearings are new this fortnight?",
     "Designed for enforcement targeting; already used that way."],
    ["PRODES", "Deforestation", "INPE", "Brazilian biomes", "Annual clear-cut polygons",
     "Annual", "Open", "TerraBrasilis API and download",
     "terrabrasilis.dpi.inpe.br",
     "What is the official annual clearing figure?",
     "The reference series; slower but authoritative."],
    ["MapBiomas — mining module", "Land use", "MapBiomas", "Brazil",
     "30 m annual land cover, with garimpo/industrial split and substance attribution",
     "Annual, 1985–present", "CC BY-SA", "Download, GEE",
     "brasil.mapbiomas.org",
     "How much of the country is mined, by whom and since when?",
     "443,000 ha mined in 2022; 92% in the Amazon; 263,000 ha garimpo."],
    ["ANM SIGMINE", "Mining cadastre", "ANM (Brazil)", "Brazil",
     "Polygons of every active and inactive mining process",
     "Daily", "Open government data", "Bulk SHP/KML; ArcGIS REST",
     "dadosabertos.anm.gov.br/SIGMINE/PROCESSOS_MINERARIOS/",
     "Who is authorised to work exactly which polygon?",
     "The single most important non-imagery input. ArcGIS REST at geo.anm.gov.br."],
    ["ANM Cadastro Mineiro", "Mining cadastre", "ANM (Brazil)", "Brazil",
     "Requests, titles, holders, regimes", "Daily micro-datasets", "Open government data",
     "dados.gov.br", "dados.gov.br/dados/conjuntos-dados/sistema-de-cadastro-mineiro",
     "What is the legal status of this title today?",
     "Status matters as much as geometry: a requerimento authorises nothing."],
    ["ANM CFEM (arrecadação)", "Royalties", "ANM (Brazil)", "Brazil",
     "Royalty payments by process and period", "Monthly", "Open government data",
     "dados.gov.br", "dados.gov.br/dados/conjuntos-dados/sistema-arrecadacao",
     "What production has been declared, and what was paid on it?",
     "The declared-production proxy. TCU found R$16.4 bn uncollected over eight years."],
    ["ANM SIGBM", "Tailings dams", "ANM (Brazil)", "Brazil",
     "Dam characteristics, tailings type, emergency level", "Real-time",
     "Open government data; public viewer", "dados.gov.br; sigbm.anm.gov.br/Publico",
     "sigbm.anm.gov.br/Publico",
     "Which structures exist, and which are already in alert?",
     "917 dams registered Nov 2025; 470 under the PNSB; 93 in alert or emergency."],
    ["ANM TAH", "Fiscal", "ANM (Brazil)", "Brazil",
     "Annual per-hectare fee by process, year, holder, area", "Annual",
     "Open government data", "dados.gov.br",
     "dados.gov.br/dados/conjuntos-dados/taxa-anual-por-hectare-tah",
     "Is the holder paying to hold the area at all?",
     "Non-payment is a cheap early signal of a dormant or abandoned title."],
    ["Anuário Mineral Brasileiro", "Production", "ANM (Brazil)", "Brazil",
     "Production and destination — sales, transfers, consumption", "Annual, from 2010",
     "Open government data", "dados.gov.br",
     "dados.gov.br/dados/conjuntos-dados/anuario-mineral-brasileiro-amb",
     "What did this operation say it produced last year?",
     "Cross-check against CFEM and against the company's own annual report."],
    ["EU high-value datasets", "Cadastre and environment", "EU member states", "EU",
     "INSPIRE themes plus environmental priority data; scales to 1:5000",
     "As published; current plus historical versions required",
     "CC BY 4.0 or less restrictive (mandatory)", "API and bulk download (mandatory)",
     "eur-lex.europa.eu/eli/reg_impl/2023/138/oj/eng",
     "Where are the licences, protected areas and environmental records in this member state?",
     "Implementing Reg. (EU) 2023/138. The EU has already legislated the supply side of "
     "this architecture. Compliance was due mid-2024."],
    ["EITI country reports", "Payments and ownership", "EITI + implementing countries",
     "~50 countries", "Payments, beneficial ownership, contracts",
     "Annual; systematic disclosure encouraged", "Open (EITI open data policy)",
     "Download, country portals", "eiti.org",
     "Who owns this and what did they pay?",
     "2023 Standard strengthened beneficial-ownership and contract transparency."],
    ["EU Accounting Directive Ch. 10", "Payments", "EU-listed extractive companies", "EU",
     "Payments to governments by project", "Annual", "Public filing",
     "Company reports, national registers", "—",
     "Does what they told shareholders match what they told the tax authority?",
     "Cross-filing divergence needs no remote sensing and is often the strongest signal."],
    ["ESTMA reports", "Payments", "Canadian-listed extractive companies", "Global",
     "Payments to governments", "Annual", "Public filing", "Natural Resources Canada",
     "natural-resources.canada.ca", "Same question, different regime.",
     "Useful where a Canadian-listed parent operates elsewhere."],
    ["Global-scale mining polygons v2", "Reference", "Maus et al. / IIASA-WU", "145 countries",
     "44,929 polygons; 101,583 km²; from 2019 Sentinel-2 cloudless mosaic",
     "Static (2019)", "CC BY-SA 4.0", "PANGAEA download",
     "doi.org/10.1594/PANGAEA.942325",
     "Where are the world's mines, roughly?",
     "Accuracy 88.3%; user's 97.2%; producer's 78.9%; F1 0.87. A starting gazetteer, "
     "not a cadastre."],
    ["Open database of mine production", "Reference", "Jasansky et al.", "80 countries",
     "1,171 mines; 80 materials; 2000–2021; Brazil 89 facilities",
     "Static", "CC BY 4.0 (data); GPL-3 (code)", "Zenodo",
     "doi.org/10.5281/zenodo.7369478",
     "What has this mine historically produced?",
     "Hand-built from >1,900 company reports; every datum linked to its source. China "
     "under-covered; excludes artisanal mining."],
    ["Global Tailings Portal", "Tailings", "GRID-Arendal + Investor Mining and Tailings "
     "Safety Initiative", "Global", "~1,800 facilities; ~100 companies; 20 field categories",
     "Irregular", "Searchable; bulk on request", "Web portal",
     "tailing.grida.no",
     "What kind of structure is this, and how was it raised?",
     "Only 332 of 727 surveyed listed companies responded — itself a finding about the "
     "disclosure regime."],
    ["Global Coal Mine Tracker", "Reference", "Global Energy Monitor", "Global",
     "Operator, ownership, status, coal type, workforce, location",
     "Annual since 2023", "Open", "Download", "globalenergymonitor.org",
     "Who operates this coal mine and what is its status?",
     "Validated against government sources, company reports, media and field contacts."],
    ["JRC Global Surface Water", "Water", "EC Joint Research Centre", "Global",
     "30 m; occurrence, change, seasonality, 1984–present", "Annual", "Open",
     "GEE, download", "global-surface-water.appspot.com",
     "Was there water here before the impoundment was built?",
     "The baseline against which a new pond is 'new'."],
    ["WDPA / CNUC / FUNAI", "Protected areas", "UNEP-WCMC; MMA; FUNAI",
     "Global / Brazil", "Protected-area and Indigenous-land boundaries",
     "Monthly to irregular", "Varies — check per layer", "Download, WFS",
     "protectedplanet.net",
     "Is this area one where extraction is categorically prohibited?",
     "Boundary provenance matters: use the national register of record, not a global "
     "aggregate, for anything that will be acted on."],
    ["OpenCorporates", "Corporate", "OpenCorporates", "Global",
     "Company registrations and officers", "Continuous", "Mixed — check terms",
     "API", "opencorporates.com",
     "Who is behind the holder of record?",
     "Combine with EITI beneficial-ownership disclosures."],
    ["Open Ownership Register", "Corporate", "Open Ownership", "~30 jurisdictions",
     "Beneficial-ownership declarations in a common data standard", "Continuous",
     "Open (Beneficial Ownership Data Standard)", "Bulk download, API",
     "register.openownership.org",
     "Who ultimately benefits from the holder of record?",
     "Ingests country beneficial-ownership registers (including EITI-mandated ones) into "
     "one schema. The natural companion to the CFEM/EITI/Ch.10 cross-filing check."],
    ["Resource Contracts Portal", "Contracts", "NRGI / World Bank / Columbia CCSI",
     "~100 countries", "Full text of mining and oil contracts, annotated",
     "As published/submitted", "Open", "Web portal, bulk download",
     "resourcecontracts.org",
     "What did the state actually agree to on this title?",
     "The contract itself, not just the registry entry — useful where the cadastre "
     "records status but not terms."],
    ["Global Forest Watch platform", "Deforestation — access layer",
     "World Resources Institute", "Global",
     "Unified access to RADD, GLAD-L, GLAD-S2 and Hansen annual loss over one map/API",
     "Near-real-time to annual, depending on the layer", "CC BY 4.0",
     "Web map, API, bulk download", "globalforestwatch.org",
     "Which alert product is the right one for this region and this question?",
     "Useful as the ingestion point rather than wiring each underlying product "
     "separately; GLAD-L/S2 extend near-real-time coverage outside RADD's footprint."],
    ["ESA WorldCover", "Land cover baseline", "ESA / VITO", "Global",
     "10 m, 11 land-cover classes, two epochs (2020, 2021)", "Static per epoch",
     "CC BY 4.0", "STAC, download", "esa-worldcover.org",
     "What was here before it became a mine — cropland, forest, already-bare ground?",
     "The independent baseline that keeps the footprint detector honest about what "
     "counts as 'disturbed' in a given landscape."],
    ["OpenStreetMap", "Infrastructure baseline", "OSM Foundation / contributors", "Global",
     "Roads, haul-road candidates, settlements, watercourses", "Continuous, crowd-sourced",
     "ODbL 1.0", "API (Overpass), bulk extracts", "openstreetmap.org",
     "Is this a new haul road, and does it reach a settlement or a river?",
     "Coverage quality varies strongly by region; verify against imagery before relying "
     "on it evidentially."],
    ["USGS Mineral Resources Data System (MRDS)", "Reference", "USGS", "USA + global sites",
     "~330,000 historical mineral occurrences, deposits and prospects",
     "Static, periodically revised", "Public domain", "Download, ArcGIS REST",
     "mrdata.usgs.gov/mrds/",
     "Has this location been mined or prospected before?",
     "The deepest historical baseline available for the pre-satellite era."],
    ["INGEMMET GEOCATMIN", "Mining cadastre", "INGEMMET (Peru)", "Peru",
     "Mining concession polygons, status, geological and energy layers", "Regularly updated",
     "Open government data", "Web map, WMS, e-Catastro download",
     "geocatmin.ingemmet.gob.pe",
     "Who holds the concession over this Peruvian site, and what is its status?",
     "Peru's equivalent of SIGMINE; combine with MINEM production and formalisation "
     "(REINFO) registers for the declaration cross-check."],
    ["SERNAGEOMIN Catastro Minero Online", "Mining cadastre", "SERNAGEOMIN (Chile)", "Chile",
     "Mining concession (pertenencia) polygons and status", "Regularly updated",
     "Open government data", "Web viewer, download",
     "catastro.sernageomin.cl",
     "Who holds the concession over this Chilean site, and what is its status?",
     "Chile's national mining cadastre; pair with SERNAGEOMIN's tailings (relaves) "
     "registry for the dam-safety layer."],
    ["CAMI — Cadastre Minier (DRC)", "Mining cadastre",
     "Cadastre Minier, Ministry of Mines (DRC)", "Democratic Republic of Congo",
     "Mining and quarry title polygons, holder and status", "Regularly updated",
     "Government portal — confirm re-use terms before bulk use", "Web map portal",
     "drclicences.cami.cd", "Who is authorised to work this site in the DRC, and under "
     "what kind of title?",
     "One of the oldest web-based mining cadastres in Africa (running since the 2010s); "
     "verify current polygon vintage before relying on it for boundary work."],
    ["Ghana Minerals Commission — Mining Cadastre (MCAS)", "Mining cadastre",
     "Minerals Commission (Ghana)", "Ghana",
     "Mineral rights applications, licences and their spatial extent", "Regularly updated",
     "Government portal", "Web portal (Mining Cadastre Administration System)",
     "mincom.gov.gh/mining-cadestre/",
     "Who holds the licence over this Ghanaian site, and is it in good standing?",
     "A companion Ghana Mining Repository (revenuedev.org) publishes licence and "
     "payment data in a more analysis-ready form."],
    ["SAMRAD (South Africa)", "Mining cadastre", "Dept. of Mineral & Petroleum Resources",
     "South Africa", "Prospecting and mining right applications and status",
     "Nominally continuous", "Government portal",
     "Web portal (portal.samradonline.co.za)", "samradonline.co.za",
     "Who holds the right over this South African site?",
     "CAUTION: independent reporting through 2026 describes SAMRAD's records as "
     "unreliable and a cadastral-system replacement as delayed and repeatedly deferred. "
     "Treat title status from this source as a lead to confirm, not a fact to act on."],
    ["MinerbaOne (Indonesia)", "Mining cadastre / production reporting",
     "Kementerian ESDM (Indonesia)", "Indonesia",
     "Licence status, production and work-plan (RKAB) filings", "Continuous",
     "Government portal", "Web portal", "modi.esdm.go.id",
     "What has this Indonesian operation reported producing, and is its licence current?",
     "Formerly 'MODI' (Minerba One Data Indonesia); the ministry has been migrating "
     "filings to a successor system named MinerbaOne — confirm which endpoint is live "
     "before integrating."],
]
write_table(ws, start, headers, rows,
            [26, 20, 22, 22, 34, 24, 24, 24, 34, 40, 46], "PublicData")
for row in ws.iter_rows(min_row=start + 1, max_row=start + len(rows)):
    ws.row_dimensions[row[0].row].height = 58

# ---------------------------------------------------------- Open source ---
ws = sheet("Open source")
start = title_block(ws, "Open-source components",
                    "Licences verified 19 Aug 2026. Pin to OSI-approved licences and "
                    "keep a documented exit path for every dependency.")
headers = ["Component", "Layer", "Function", "Licence", "Governance", "Maturity",
           "Risk note"]
rows = [
    ["QGIS", "Desktop", "GIS, visualisation, manual verification", "GPL-2.0-or-later",
     "QGIS.org / OSGeo", "Production",
     "Recognised as a Digital Public Good by the DPG Alliance, Feb 2025 — a useful "
     "precedent for classifying this platform."],
    ["GDAL / OGR", "I/O", "Raster and vector formats, reprojection, warping",
     "MIT/X-style", "OSGeo", "Production", "The load-bearing dependency of the entire "
     "geospatial world. Safe."],
    ["PostgreSQL", "Store", "Relational database", "PostgreSQL Licence", "PostgreSQL "
     "Global Development Group", "Production", "Safe."],
    ["PostGIS", "Store", "Spatial types, indexes and operations", "GPL-2.0-or-later",
     "OSGeo", "Production", "Safe."],
    ["stac-fastapi + pgstac", "Store", "STAC API over PostgreSQL", "MIT",
     "Radiant Earth / community", "Production", "Same standard the upstream archives use."],
    ["pystac / pystac-client", "Acquisition", "STAC catalogue client", "Apache-2.0",
     "Radiant Earth", "Production", "—"],
    ["Open Data Cube", "Store", "Indexed EO data cube", "Apache-2.0", "ODC / CEOS",
     "Production", "Several national deployments (Digital Earth Australia, Africa)."],
    ["openEO", "Processing", "Federated EO processing API", "Apache-2.0", "openEO / ESA",
     "Production", "Available on CDSE within the free-tier credit allocation."],
    ["eodag", "Acquisition", "Multi-provider archive access", "Apache-2.0", "CS Group",
     "Production", "Useful when a deployment must span several archives."],
    ["rasterio / rioxarray", "Processing", "Raster read/write, warping, xarray bridge",
     "BSD-3 / Apache-2.0", "Mapbox → community", "Production", "—"],
    ["xarray / dask", "Processing", "Labelled arrays; out-of-core parallelism",
     "Apache-2.0 / BSD-3", "NumFOCUS", "Production", "—"],
    ["numpy / scipy", "Processing", "Numerics, morphology, statistics", "BSD-3",
     "NumFOCUS", "Production", "numpy is the only mandatory dependency of the core."],
    ["scikit-image", "Processing", "Segmentation, morphology, measurement", "BSD-3",
     "NumFOCUS", "Production", "—"],
    ["scikit-learn", "Analysis", "Classical ML for classification and clustering",
     "BSD-3", "NumFOCUS", "Production", "—"],
    ["TorchGeo", "Analysis", "Geospatial deep learning datasets and models", "MIT",
     "Microsoft", "Production", "The path for a learned second-opinion detector."],
    ["segment-geospatial / leafmap", "Analysis", "SAM-based segmentation; notebooks",
     "MIT", "Open Geospatial Solutions", "Production", "Used by Amazon Mining Watch for "
     "scar masks."],
    ["ESA SNAP", "SAR", "Sentinel-1 preprocessing, interferometry", "GPL-3.0", "ESA",
     "Production", "Heavy. Java. Works."],
    ["ISCE2", "SAR", "Interferogram generation", "Apache-2.0", "NASA JPL", "Production",
     "The other half of the non-European InSAR path."],
    ["MintPy", "SAR", "InSAR time-series inversion (SBAS)", "GPL-3.0", "Academic "
     "community", "Production", "Pairs with ISCE2 or SNAP."],
    ["LiCSBAS", "SAR", "InSAR time series over LiCSAR products", "GPL-3.0", "COMET",
     "Production", "Lower barrier to entry than MintPy where LiCSAR covers the area."],
    ["Orfeo ToolBox", "Processing", "Remote-sensing image processing", "Apache-2.0",
     "CNES", "Production", "—"],
    ["TiTiler", "Services", "Dynamic tiling from COGs", "MIT", "Development Seed",
     "Production", "—"],
    ["GeoServer", "Services", "OGC WMS/WFS/WCS", "GPL-2.0", "OSGeo", "Production", "—"],
    ["pygeoapi", "Services", "OGC API Features / Records / Processes", "MIT", "OSGeo",
     "Production", "Lighter and more modern than GeoServer for API-only needs."],
    ["GeoNode", "Portal", "Geospatial catalogue and portal", "GPL-3.0", "OSGeo",
     "Production", "Fastest route to a public portal."],
    ["CKAN", "Portal", "Open-data catalogue", "AGPL-3.0", "OKFN", "Production",
     "AGPL: procurement implications if modified and exposed as a service."],
    ["MapLibre GL JS", "Frontend", "Vector web maps", "BSD-3", "MapLibre / Linux "
     "Foundation", "Production", "The post-Mapbox fork; safe."],
    ["deck.gl", "Frontend", "Large-scale WebGL data overlays", "MIT", "OpenJS Foundation",
     "Production", "—"],
    ["Apache Airflow", "Orchestration", "Scheduled pipeline execution", "Apache-2.0",
     "ASF", "Production", "One DAG per site per cadence."],
    ["Prefect", "Orchestration", "Alternative orchestrator", "Apache-2.0", "Prefect "
     "Technologies", "Production", "Lighter for small deployments."],
    ["DuckDB", "Analytics", "In-process analytical SQL, GeoParquet reads", "MIT",
     "DuckDB Foundation", "Production", "Findings tables are small; no cluster needed."],
    ["GeoParquet", "Format", "Columnar geospatial storage", "Apache-2.0", "OGC",
     "Production", "—"],
    ["Cloud-Optimised GeoTIFF", "Format", "Range-request raster storage", "Open spec",
     "OGC", "Production", "What the upstream archives already serve."],
    ["Apache Superset", "Analytics", "BI dashboards", "Apache-2.0", "ASF", "Production",
     "—"],
    ["Keycloak", "Identity", "Authentication, roles, audit", "Apache-2.0", "CNCF / Red Hat",
     "Production", "Carries the role model the case state machine checks."],
    ["SeaweedFS", "Store", "S3-compatible object storage", "Apache-2.0", "Community",
     "Production", "RECOMMENDED replacement for MinIO."],
    ["Garage", "Store", "S3-compatible object storage", "AGPL-3.0", "Deuxfleurs",
     "Production", "Lightweight; AGPL implications if modified and exposed."],
    ["Ceph RGW", "Store", "S3-compatible object storage at scale", "LGPL-2.1/3.0",
     "Ceph Foundation", "Production", "For Tier-3 scale."],
    ["MinIO", "Store", "S3-compatible object storage", "AGPL-3.0 (community edition "
     "archived)", "MinIO Inc.", "DO NOT ADOPT",
     "Community edition entered maintenance mode and was archived over 2025-26 after "
     "features were stripped from the AGPL build. Any architecture that assumed MinIO "
     "now has a problem."],
    ["Grafana", "Monitoring", "Operational dashboards", "AGPL-3.0", "Grafana Labs",
     "Production", "Fine to run; AGPL implications if modified and exposed as a service."],
    ["Sen2Cor", "Processing", "Sentinel-2 L1C→L2A atmospheric correction",
     "ESA free-to-use, NOT OSI-approved", "ESA", "Production",
     "Prefer consuming L2A products directly rather than depending on local Sen2Cor."],
    ["GemPy", "Geoscience", "Implicit 3-D geological modelling", "EUPL / open",
     "Academic community", "Research to production",
     "The nearest open equivalent to Leapfrog. Not a mine-planning system, and the "
     "public mirror does not need one."],
    ["mining-detector (Earth Genome)", "Analysis",
     "CNN ensemble for artisanal mine detection from Sentinel-2", "MIT (code); "
     "CC BY 4.0 (data)", "Earth Genome / Earthrise Media", "Production",
     "99.4% specificity / 89.5% sensitivity on a Venezuela geographic holdout. The "
     "obvious second-opinion detector."],
    ["GeoPandas", "Processing", "Vector geospatial data frames over shapely/pyproj",
     "BSD-3", "GeoPandas community", "Production",
     "Ties shapely, pyproj and fiona together; an optional accelerator, not required "
     "by the core library."],
    ["QField", "Field", "Mobile QGIS for offline field data collection", "GPL-2.0-or-later",
     "OPENGIS.ch", "Production",
     "The natural way for an inspector to record a ground-truth visit and sync it back "
     "to the case register."],
    ["WhiteboxTools", "Processing", "Geomorphometry and hydrological DEM analysis",
     "MIT (core engine)", "Whitebox Geospatial / Dr. John Lindsay", "Production",
     "A lighter alternative to GRASS/SAGA for terrain-derivative work on the Copernicus "
     "DEM."],
    ["SAGA GIS", "Processing", "Terrain analysis and general geoprocessing", "GPL-2.0",
     "SAGA community", "Production", "—"],
    ["PDAL", "Processing", "Point-cloud (LiDAR, drone photogrammetry) processing",
     "BSD-3", "PDAL contributors / OSGeo", "Production",
     "Relevant where a deployment ingests drone or airborne LiDAR alongside satellite "
     "data — e.g. calibrating the DEM-differencing error model against a surveyed site."],
    ["Zarr", "Format", "Chunked, compressed, cloud-native N-dimensional arrays", "MIT",
     "Zarr community / NumFOCUS", "Production",
     "An alternative to COG for large multi-temporal cubes; pairs with xarray and dask."],
    ["eo-learn", "Analysis", "Earth-observation processing pipelines as scikit-learn-style "
     "transformers", "MIT", "Sinergise / community", "Production",
     "A patterned way to assemble a detector pipeline without hand-rolling glue code."],
    ["MLflow", "Analysis", "Experiment tracking and model versioning", "Apache-2.0",
     "Linux Foundation", "Production",
     "Gives the learned second-opinion detector the same version discipline the rule-"
     "based detectors get from ALGORITHM_VERSIONS — required once a model sits anywhere "
     "near the evidentiary path."],
    ["Great Expectations", "Data quality", "Declarative data validation for pipelines",
     "Apache-2.0", "Great Expectations community", "Production",
     "Catches a malformed registry export (wrong CRS, truncated file, schema drift) "
     "before it reaches a case, rather than after."],
    ["Martin", "Services", "Fast vector-tile (MVT) server in Rust", "MIT", "MapLibre "
     "organisation", "Production",
     "A lighter alternative to GeoServer/pygeoapi when only fast tile serving is needed."],
    ["H3", "Processing", "Hexagonal hierarchical spatial indexing", "Apache-2.0", "Uber /"
     " community", "Production",
     "Useful for aggregating findings to a coarse grid for the political-register "
     "oversight brief without exposing exact site geometry."],
    ["Folium / ipyleaflet", "Field", "Interactive maps inside notebooks", "MIT",
     "Python-Visualization / Jupyter community", "Production",
     "Lets an analyst eyeball a case's imagery and mask overlays before it is "
     "corroborated, without leaving the analysis notebook."],
    ["OpenSearch", "Analytics", "Log and full-text search, forked from Elasticsearch",
     "Apache-2.0", "OpenSearch Software Foundation", "Production",
     "A home for indexing ledger entries, notices and public cards for full-text search "
     "on the public portal."],
    ["Metabase (OSS edition)", "Analytics", "BI dashboards over the case register",
     "AGPL-3.0", "Metabase community", "Production",
     "Lighter to stand up than Superset for a Tier-1/Tier-2 deployment; AGPL "
     "implications apply if modified and exposed as a service, as with CKAN/Grafana."],
]
write_table(ws, start, headers, rows, [30, 16, 40, 30, 26, 18, 62], "OpenSource")
for row in ws.iter_rows(min_row=start + 1, max_row=start + len(rows)):
    ws.row_dimensions[row[0].row].height = 46

# ------------------------------------------------------ Capability mirror ---
ws = sheet("Capability mirror")
start = title_block(
    ws, "Capability mirror",
    "What the operator sees, what a public body can see from public data, and what "
    "cannot be mirrored at all.")
headers = ["#", "Operator capability", "Vendor examples", "Public mirror",
           "Public data behind it", "Fidelity", "Assessment"]
rows = [
    [1, "Tenure and permit management", "trueMINER, acQuire, Landfolio",
     "Cadastre engine — polygon register, overlap detection, title-status timeline",
     "SIGMINE (daily); EU member-state registries under Reg. 2023/138", "Full",
     "The registry IS the public copy. Nothing to reconstruct."],
    [2, "Survey of the working surface", "Total station, drone photogrammetry",
     "Footprint delineation at 10 m, every 5 days",
     "Sentinel-2 L2A; Landsat 8/9 for the pre-2015 baseline", "High",
     "Operator wins on precision; public wins on frequency and history. For 'did it "
     "move outside the boundary', frequency wins."],
    [3, "Volumetrics and progress", "Propeller, Strayos",
     "DEM differencing — cut/fill and implied tonnage with explicit uncertainty",
     "Copernicus DEM GLO-30; NASADEM; national photogrammetric DSMs", "Moderate",
     "Order-of-magnitude with wide intervals. An upper bound on extraction, never a "
     "production figure."],
    [4, "Geotechnical and dam monitoring", "Rocscience, instrumented crests",
     "InSAR displacement screening — mm-scale movement and acceleration",
     "EGMS (Europe, free); Sentinel-1 via ISCE2/SNAP + MintPy/LiCSBAS elsewhere",
     "High for movement, none for cause",
     "Detects that a crest is moving. Cannot say why, and must not predict failure."],
    [5, "Tailings and water management", "RPMGlobal, Envirosuite",
     "Pond extent, turbidity gradient, freeboard proxy",
     "Sentinel-2; JRC Global Surface Water; SIGBM; Global Tailings Portal", "Moderate",
     "Surface behaviour only. Turbidity is a trigger for sampling, not a contamination "
     "finding."],
    [6, "Environmental monitoring", "Envirosuite, EnviroDataVault",
     "Impact screening — vegetation loss, deforestation alerts, plume proxies",
     "RADD; DETER/PRODES; MapBiomas; Sentinel-5P", "Moderate to high for land cover",
     "Low for ambient concentrations without ground stations. Do not overclaim."],
    [7, "Metallurgical accounting", "INVENTEO (AMIRA P754)",
     "Declaration screening — intensity against peers; cross-filing consistency",
     "CFEM; Anuário Mineral; EITI; EU Ch. 10; ESTMA",
     "Low as measurement, high as triage",
     "Do NOT convert footprint to tonnes. You cannot compute their production; you can "
     "rank who is worth auditing."],
    [8, "Stakeholder and grievance management", "Borealis",
     "Public grievance intake with a published response obligation",
     "Built, not borrowed (ODK/Kobo pattern)", "Full",
     "Arguably better than the commercial equivalent: the record is not held by the "
     "party complained about."],
    [9, "EHS incident management", "Intelex, EHS Insight, SafetyIQ",
     "Public incident register cross-referenced with regulator and press records",
     "Agency bulletins, labour inspectorate data, press", "Partial",
     "Entirely dependent on the disclosure regime in force."],
    [10, "Mine planning, scheduling, reserve modelling",
     "Deswik, Vulcan, Datamine, Leapfrog", "NONE", "—", "Not mirrorable",
     "Requires the drillhole database. No open-source equivalent exists and the public "
     "mirror does not need one."],
    [11, "Fleet management and dispatch", "Modular, Wenco, Cat MineStar", "NONE", "—",
     "Not mirrorable, and should not be",
     "A regulator has no business dispatching trucks. Saying so is what makes the rest "
     "credible."],
    [12, "Process control / SCADA", "FrameworX, Rockwell, ABB", "NONE", "—",
     "Not mirrorable", "Inside the plant, behind the fence, on the operator's network."],
]
write_table(ws, start, headers, rows, [5, 34, 30, 44, 40, 28, 58], "CapabilityMirror")
for row in ws.iter_rows(min_row=start + 1, max_row=start + len(rows)):
    ws.row_dimensions[row[0].row].height = 62

# --------------------------------------------------- Commercial landscape ---
ws = sheet("Commercial landscape")
start = title_block(
    ws, "Commercial landscape",
    "The products listed on sourceforge.net/software/mining/europe/, sorted by "
    "function. Treated here as a published capability specification, not an endorsement.")
headers = ["Product", "Vendor", "Functional layer", "Self-described function",
           "Mirrorable from public data?"]
rows = [
    ["trueMINER", "trueMINER", "Tenure and permits",
     "Land management for tenure, exploration activities and permits", "Yes — fully"],
    ["MineCycle", "Bentley", "Mine design and survey",
     "Mine design, planning and survey with scheduling and bulk materials handling",
     "Extent only"],
    ["Promine", "Promine", "Mine design", "CAD-integrated resource calculation, mine "
     "planning and scheduling", "No"],
    ["Reactore / MineOne", "Reactore", "Planning and execution",
     "Operational planning and digitalisation of mining activity", "No"],
    ["ShiftManager", "RPMGlobal", "Short-interval control",
     "Real-time short-term planning and execution", "No"],
    ["Lightship", "Lightship", "Automation glue",
     "Connects field, facility and office work across enterprise systems", "No"],
    ["Blast Management System (BIMS)", "MineExcellence", "Drill and blast",
     "Planning, controlling and documenting drill and blast operations", "No"],
    ["Rocscience", "Rocscience", "Geotechnics",
     "2-D/3-D rock and soil stability analysis", "Movement only, via InSAR"],
    ["Propeller", "Propeller Aero", "Survey and volumetrics",
     "Drone mapping and 3-D analytics for earthworks progress",
     "Approximately, via DEM differencing"],
    ["Strayos", "Strayos", "3-D AI",
     "Visual AI on 3-D data for mine-to-mill digital twins", "No"],
    ["RockWorks", "RockWare", "Geological modelling",
     "2-D/3-D subsurface mapping and geological modelling", "No"],
    ["LogPlot8", "RockWare", "Geological logging",
     "Log plotting of geotechnical and mining data", "No"],
    ["Surfer", "Golden Software", "Surfaces",
     "Data visualisation and modelling for geology and hydrology",
     "Partially — open equivalents exist"],
    ["HSC Chemistry", "Metso", "Process chemistry",
     "Thermodynamic calculations for mineral processing", "No"],
    ["INVENTEO", "Caspeo", "Metallurgical accounting",
     "Metal accounting compliant with the AMIRA P754 code",
     "Only as relative triage, never as measurement"],
    ["Envirosuite", "Envirosuite", "Environmental monitoring",
     "Real-time environmental monitoring turning sensor data into decisions",
     "Partially — land cover yes, ambient concentrations no"],
    ["EnviroDataVault", "RPMGlobal", "Environmental data",
     "Environmental data capture and management across the mine lifecycle",
     "Partially"],
    ["Intelex", "Intelex Technologies", "EHSQ",
     "Integrated environment, health, safety and quality management",
     "Only the public-record part"],
    ["EHS Insight", "EHS Insight", "EHS", "Compliance and incident tracking",
     "Only the public-record part"],
    ["SafetyIQ", "SafetyIQ", "Workforce safety",
     "Mobile worker safety, fatigue management, training", "No"],
    ["PeopleTray", "PeopleTray", "Workforce",
     "Worker safety, incident reporting, compliance, rosters", "No"],
    ["Pervidi Mining", "Techs4Biz", "Inspections",
     "Mobile inspection and compliance with AI image recognition", "No"],
    ["Inspectivity", "Inspectivity", "Inspections",
     "Digital inspection management for asset-centric workflows", "No"],
    ["Dashpivot", "Sitemate", "Field records",
     "Consolidated field records, timesheets and incident reports", "No"],
    ["Borealis", "Borealis", "Stakeholder engagement",
     "Social investment, grievance management, land management",
     "Yes — and arguably better in public hands"],
    ["4site", "fsc", "Asset management",
     "Maintenance, purchasing, inventory and accounting", "No"],
    ["FrameworX", "Tatsoft", "SCADA / IIoT",
     "Industrial control combining operations, data and AI", "No"],
    ["MineTwin", "MineTwin", "Simulation",
     "Digital twins for decision support", "No"],
    ["EarthCache", "SkyWatch", "EO access",
     "API access to satellite Earth observation data",
     "Yes — this is what CDSE provides for free"],
    ["Chemical/EAM others (Surfer, BAM!, etc.)", "various", "Support", "—", "—"],
]
next_row = write_table(ws, start, headers, rows, [32, 24, 26, 52, 40], "Commercial")

ws.cell(row=next_row + 1, column=1,
        value="Broader market context — not from the SourceForge page itself").font = BOLD
ws.cell(row=next_row + 2, column=1,
        value="The consolidated platforms behind the mine-planning and fleet layers the "
              "report says are NOT mirrorable (rows 10-12 of the Capability mirror sheet). "
              "Listed for completeness of the market picture, not as a gap this "
              "architecture tries to close.").font = NOTE
ws.cell(row=next_row + 2, column=1).alignment = WRAP
ws.merge_cells(start_row=next_row + 2, start_column=1, end_row=next_row + 2, end_column=5)
start2 = next_row + 4
rows2 = [
    ["Deswik Suite", "Sandvik", "Mine design and scheduling",
     "Integrated mine planning, scheduling and geology", "No"],
    ["Datamine", "Constellation Software", "Mine design and resource modelling",
     "Geology, resource estimation, mine planning and scheduling", "No"],
    ["Vulcan", "Trimble", "Mine design and resource modelling",
     "3-D geological modelling, resource estimation and mine planning", "No"],
    ["Leapfrog / Seequent Evo", "Bentley Systems", "Geological modelling",
     "Implicit 3-D geological and resource modelling", "No"],
    ["Micromine", "Weir Group", "Mine design and resource modelling",
     "Geology, mine design, scheduling and equipment monitoring", "No"],
    ["Maptek Vulcan/BlastLogic/PointStudio", "Maptek", "Mine design and survey",
     "Geological modelling, blast design, laser-scan survey processing",
     "Survey extent only, via satellite in place of laser scan"],
    ["Hexagon Mining (HxGN MinePlan)", "Hexagon AB", "Mine planning and autonomy",
     "Mine planning, fleet management, autonomous-haulage integration", "No"],
    ["Cat MineStar", "Caterpillar", "Fleet management and autonomy",
     "Fleet dispatch, terrain, detect and health monitoring for Cat equipment", "No"],
    ["Modular Mining (DISPATCH)", "Komatsu", "Fleet management",
     "Real-time fleet dispatch and production tracking", "No"],
    ["Wenco Mining Systems", "Hitachi Construction Machinery", "Fleet management",
     "Fleet management and autonomous-haulage system", "No"],
]
r = start2
for row in rows2:
    for j, v in enumerate(row, start=1):
        c = ws.cell(row=r, column=j, value=v)
        c.font = BODY
        c.alignment = WRAP
        c.border = BOX
    ws.row_dimensions[r].height = 34
    r += 1
next_row2 = r

ws.cell(row=next_row2 + 1, column=1, value="Market consolidation record").font = BOLD
cons = [
    ["Global Mining Tech 50 (IMARC / Mines and Money)",
     "Top 50 vendors sold ~US$6.8 bn of mining/metals technology in 2025; +73.5% over "
     "five years."],
    ["Caterpillar → RPMGlobal", "~US$728–735 m; completed February 2026."],
    ["Weir → Micromine", "~US$840 m; completed April 2025."],
    ["Sandvik → Deswik", "Owned."],
    ["Bentley → Seequent", "Leapfrog, Evo."],
    ["Constellation Software", "30+ mining software firms acquired since 2011; flagship "
     "Datamine."],
    ["Epiroc", "13 mining-technology firms acquired since 2021."],
    ["Implication for a regulator",
     "Planning, execution and reporting increasingly sit inside one commercial "
     "relationship, and the interfaces between them are not public."],
]
r = next_row2 + 2
for a, b in cons:
    ws.cell(row=r, column=1, value=a).font = BODY
    c = ws.cell(row=r, column=2, value=b)
    c.font = BODY
    c.alignment = WRAP
    r += 1
for row in ws.iter_rows(min_row=start + 1, max_row=start + len(rows)):
    ws.row_dimensions[row[0].row].height = 34

# -------------------------------------------------------------- Jurisdictions ---
ws = sheet("Jurisdictions")
start = title_block(
    ws, "Jurisdictions",
    "The registries and legal hooks a deployment needs per country: cadastre, "
    "production/royalty disclosure, protected-area and dam-safety registers, and the "
    "due-process basis. Verified 19 Aug 2026 from each register's own site — re-verify "
    "before procurement, since several of these systems are mid-reform.")
headers = ["Jurisdiction", "Title / cadastre registry", "Production or royalty disclosure",
           "Protected-area / environmental register", "Dam-safety regime",
           "Due-process legal basis", "Notes"]
rows = [
    ["Brazil", "ANM SIGMINE + Cadastro Mineiro (daily, SHP/KML)",
     "CFEM (royalties) + Anuário Mineral Brasileiro (production)",
     "CNUC (conservation units); FUNAI (Indigenous Lands)",
     "SIGBM under Lei 12.334/2010 + Lei 14.066/2020 (PNSB)",
     "CF/88 art. 5 LIV/LV; Lei 9.784/1999; Lei 9.605/1998; Lei 12.527/2011 (LAI)",
     "The strongest combination in this table: polygon, royalty, dam and access-to-"
     "information regimes are all open and machine-readable today."],
    ["European Union (member states)", "National cadastres under Reg. (EU) 2023/138 "
     "high-value datasets", "EU Accounting Directive Ch. 10 (payments to governments)",
     "Natura 2000 / national protected-area registers under Directives 92/43/EEC, "
     "2009/147/EC", "Directive 2006/21/EC (extractive waste); national dam-safety law",
     "EU Charter arts. 41/47; Directive 2003/4/EC (environmental information); Aarhus "
     "Convention",
     "The Union has legislated the supply side directly: HVD compliance was due "
     "~mid-2024, ahead of most jurisdictions in this table."],
    ["Peru", "INGEMMET GEOCATMIN / e-Catastro Minero",
     "MINEM production statistics; REINFO for artisanal/small-scale formalisation",
     "SERNANP (protected natural areas)", "ANA / ANM (Peru) dam oversight — supervision "
     "less centralised than Brazil's SIGBM",
     "Ley del Procedimiento Administrativo General (Ley 27444); constitutional due "
     "process",
     "REINFO's formalisation-in-progress status is itself a signal worth screening: "
     "activity outside any REINFO or concession polygon is unambiguous."],
    ["Chile", "SERNAGEOMIN Catastro Minero Online (pertenencias)",
     "SERNAGEOMIN production statistics; Servicio de Impuestos Internos royalty filings",
     "SNASPE / Ministerio del Medio Ambiente protected areas",
     "SERNAGEOMIN relaves (tailings) registry, tightened after Ley 21.430 and post-2019 "
     "reforms",
     "Ley 19.880 (bases de procedimientos administrativos)",
     "One of the more mature Latin American cadastres; pair with the relaves registry "
     "for the dam-safety layer."],
    ["Democratic Republic of Congo", "CAMI Cadastre Minier web portal",
     "Ministry of Mines statistics; EITI-DRC reports", "ICCN (protected areas)",
     "No centralised public dam registry identified — treat as a gap to flag, not to "
     "assume covered",
     "Loi minière (as revised); constitutional due-process guarantees",
     "Verify current polygon vintage before boundary work; CAMI has run since the "
     "2010s but update cadence is not published to the standard SIGMINE sets."],
    ["Ghana", "Minerals Commission Mining Cadastre (MCAS) + Ghana Mining Repository",
     "Minerals Commission / GRA royalty statistics; EITI-Ghana reports",
     "Forestry Commission reserves; EPA environmental permits",
     "Ghana has no SIGBM-scale public tailings register identified — a gap",
     "Constitution art. 23 (administrative justice); Minerals and Mining Act 2006 "
     "(Act 703)",
     "The Ghana Mining Repository publishes licence and payment data in a more "
     "analysis-ready form than the cadastre portal itself."],
    ["South Africa", "SAMRAD (rights) — CAUTION: independent reporting through 2026 "
     "describes it as unreliable, with a replacement system delayed",
     "DMPR statistics; Mining Charter reporting; EITI is not implemented in South Africa",
     "SANParks / provincial conservation agencies",
     "Department publishes a dam-safety framework; no public per-structure register at "
     "SIGBM's granularity identified",
     "Constitution s. 33 (just administrative action); Promotion of Administrative "
     "Justice Act 3 of 2000",
     "Treat any SAMRAD title status as a lead to confirm through a parallel channel, "
     "not a fact to act on, until the cadastre replacement lands."],
    ["Indonesia", "MinerbaOne / MODI (Kementerian ESDM) — mid-migration between systems",
     "RKAB work-plan and production filings via the same portal",
     "KLHK forestry/environmental permit and forest-cover layers",
     "No centralised public tailings-dam register identified at SIGBM's granularity",
     "UU No. 30/2014 (administrasi pemerintahan); constitutional due process",
     "Confirm which endpoint (legacy MODI vs MinerbaOne) is live before integrating; "
     "the ministry has been actively migrating filings during 2026."],
    ["Australia (Commonwealth + states)", "State-run cadastres — e.g. Geoscience "
     "Australia national context plus state systems (WA Tengraph, NSW MinView, "
     "Qld MyMinesOnline)", "State royalty statistics; ASX continuous-disclosure filings "
     "for listed operators", "CAPAD (protected areas database, DCCEEW)",
     "State-based dam-safety regulation (e.g. Qld's dam-safety regime); no single "
     "national register",
     "Administrative Decisions (Judicial Review) Act 1977; state equivalents",
     "Mining regulation is state-run — a deployment needs one connector per state "
     "cadastre rather than one national feed, unlike Brazil or the EU HVD regime."],
    ["Canada (Federal + provinces)", "Provincial mineral-claim registries (e.g. Ontario "
     "Mining Lands Administration System, BC Mineral Titles Online)",
     "ESTMA (payments to governments); provincial royalty statistics",
     "CPCAD (Canadian protected and conserved areas database)",
     "Provincial dam-safety regulation; federal oversight for tailings under CEPA/Fisheries "
     "Act for water impacts",
     "Canadian Charter s. 7; provincial administrative-procedure statutes",
     "ESTMA is one of the cleanest cross-filing checks available anywhere in this "
     "table — federal, standardised, and already machine-readable."],
    ["United States", "BLM LR2000 (federal claims) + state-level programs",
     "USGS Mineral Commodity Summaries; SEC filings for listed operators",
     "PAD-US (Protected Areas Database of the US)",
     "State dam-safety programs; federal oversight limited outside listed structures",
     "Administrative Procedure Act (5 U.S.C. §551 et seq.); Fifth/Fourteenth Amendment "
     "due process",
     "No federal mining cadastre equivalent to SIGMINE; claims are federal (BLM) but "
     "permitting and much reporting is state-level, so coverage is uneven by state."],
]
write_table(ws, start, headers, rows, [20, 34, 34, 30, 34, 34, 46], "Jurisdictions")
for row in ws.iter_rows(min_row=start + 1, max_row=start + len(rows)):
    ws.row_dimensions[row[0].row].height = 74

# ------------------------------------------------------------- Cost model ---
ws = sheet("Cost model")
ws.sheet_view.showGridLines = False
ws["A1"] = "Data volume against the Copernicus free-tier quota"
ws["A1"].font = TITLE
ws["A2"] = ("Edit the yellow cells. Everything else is calculated. "
            "Quota figures are as published at documentation.dataspace.copernicus.eu/Quotas.html "
            "and were checked on 19 Aug 2026.")
ws["A2"].font = NOTE
ws["A2"].alignment = WRAP

def label(row, text, note=""):
    c = ws.cell(row=row, column=1, value=text)
    c.font = BODY
    if note:
        n = ws.cell(row=row, column=4, value=note)
        n.font = NOTE
        n.alignment = WRAP

def inp(row, value, fmt="#,##0"):
    c = ws.cell(row=row, column=2, value=value)
    c.font = INPUT_FONT
    c.fill = INPUT_FILL
    c.border = BOX
    c.number_format = fmt
    return c

def calc(row, formula, fmt="#,##0.0"):
    c = ws.cell(row=row, column=2, value=formula)
    c.font = FORMULA_FONT
    c.border = BOX
    c.number_format = fmt
    return c

ws["A4"] = "INPUTS"
ws["A4"].font = BOLD
label(5, "Sites monitored", "Tier 1 ≈ 20; Tier 2 ≈ 500; Tier 3 = the full cadastre")
inp(5, 500)
label(6, "Mean site area (ha)", "Licence polygon plus a 1 km assessment apron")
inp(6, 1200)
label(7, "Sentinel-2 bands retained", "The library needs six: B02 B03 B04 B08 B11 B12")
inp(7, 6)
label(8, "Bytes per pixel per band", "uint16")
inp(8, 2)
label(9, "Acquisitions composited per month", "5-day revisit ⇒ about six per month")
inp(9, 6)
label(10, "Months of history to backfill", "2015 to date is roughly 130 months")
inp(10, 130)
label(11, "Compression ratio achieved", "COG with DEFLATE on 10 m reflectance")
inp(11, 2.5, "0.0")

ws["A13"] = "PUBLISHED FREE-TIER QUOTAS"
ws["A13"].font = BOLD
label(14, "S3 / OData / STAC transfer, per rolling 30 days (TB)")
inp(14, 12, "0.0")
label(15, "Direct COG requests per month")
inp(15, 50000)
label(16, "Sentinel Hub requests per month")
inp(16, 10000)
label(17, "Sentinel Hub processing units per month")
inp(17, 10000)

ws["A19"] = "CALCULATED"
ws["A19"].font = BOLD
label(20, "Pixels per site (10 m)")
calc(20, "=B6*10000/100", "#,##0")
label(21, "Bytes per site per acquisition")
calc(21, "=B20*B7*B8", "#,##0")
label(22, "GB per month, all sites, uncompressed")
calc(22, "=B21*B9*B5/1024/1024/1024", "#,##0.00")
label(23, "GB per month, all sites, compressed")
calc(23, "=IF(B11=0,B22,B22/B11)", "#,##0.00")
label(24, "TB per month, compressed")
calc(24, "=B23/1024", "#,##0.000")
label(25, "Share of the 12 TB / 30-day transfer quota")
c = calc(25, "=IFERROR(B24/B14,0)", "0.0%")
label(26, "One-off backfill volume (TB, compressed)")
calc(26, "=B24*B10", "#,##0.0")
label(27, "Months to backfill inside quota")
calc(27, "=IFERROR(B26/B14,0)", "#,##0.0")
label(28, "Local storage for the backfill (TB)")
calc(28, "=B26", "#,##0.0")
label(29, "Distinct S2 tiles touched (whole-granule alternative)",
      "If a deployment pulls whole granules instead of clipping to the AOI with COG "
      "range requests. Still inside quota, but ~600x the traffic.")
inp(29, 150)
label(30, "Whole-granule traffic (TB/month)",
      "Assumes ~1 GB per L2A granule.")
calc(30, "=B29*B9*1/1024", "#,##0.00")

ws["A32"] = "COST"
ws["A32"].font = BOLD
label(33, "Imagery licence cost")
c = ws.cell(row=33, column=2, value=0)
c.font = FORMULA_FONT
c.number_format = '"€"#,##0'
c.border = BOX
ws.cell(row=33, column=4,
        value="Copernicus data is free, full and open. This cell is zero by policy, "
              "not by estimate.").font = NOTE
label(34, "Software licence cost")
c = ws.cell(row=34, column=2, value=0)
c.font = FORMULA_FONT
c.number_format = '"€"#,##0'
c.border = BOX
ws.cell(row=34, column=4,
        value="Every component in the 'Open source' sheet is OSI-licensed. Excludes "
              "support contracts, which a public body may still want.").font = NOTE
label(35, "Assumed storage cost per TB-month")
inp(35, 18, '"€"#,##0')
label(36, "Annual storage cost")
calc(36, "=B28*B35*12", '"€"#,##0')
label(37, "Assumed compute cost per site-month")
inp(37, 0.4, '"€"#,##0.00')
label(38, "Annual compute cost")
calc(38, "=B5*B37*12", '"€"#,##0')
label(39, "Annual infrastructure subtotal")
calc(39, "=B36+B38", '"€"#,##0')

ws["A41"] = "STAFF — the real cost"
ws["A41"].font = BOLD
label(42, "Analysts (triage)")
inp(42, 2, "0.0")
label(43, "Technical officers (corroboration)")
inp(43, 1, "0.0")
label(44, "Fully loaded cost per FTE per year")
inp(44, 60000, '"€"#,##0')
label(45, "Annual staff cost")
calc(45, "=(B42+B43)*B44", '"€"#,##0')
label(46, "TOTAL annual cost")
c = calc(46, "=B39+B45", '"€"#,##0')
c.font = Font(name=FONT, size=11, bold=True)
label(47, "Cost per site monitored per year")
calc(47, "=IFERROR(B46/B5,0)", '"€"#,##0')
label(48, "Sites per member of technical staff")
calc(48, "=IFERROR(B5/(B42+B43),0)", "#,##0")

ws.cell(row=50, column=1,
        value="Read the last two rows, not the total.").font = BOLD
ws.cell(row=51, column=1,
        value="The argument this model supports is not that oversight becomes cheap. It "
              "is that the marginal cost of adding one more site to a monitoring "
              "programme is nearly zero, which is the opposite of the cost structure of "
              "physical inspection. The staff line dominates, and it should: this is a "
              "capacity programme, not a technology purchase."
        ).font = BODY
ws.cell(row=51, column=1).alignment = WRAP
ws.merge_cells("A51:D53")

ws.column_dimensions["A"].width = 48
ws.column_dimensions["B"].width = 18
ws.column_dimensions["C"].width = 3
ws.column_dimensions["D"].width = 62

wb.save("docs/03-catalogues.xlsx")
print("written")
