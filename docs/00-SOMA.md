# Observatório SOMA

**A landscape review, an asymmetry analysis, and a working prototype of an open public-sector platform**

Prepared for Bernardo Munayer · 19 August 2026 · single-document edition

## 1 Summary

You asked three things: whether I have any contact with the mining software vendors listed
on SourceForge; whether the public sector's need for mining surveillance can be met with
public data and open source; and whether a piece of software could be developed that
*communicates* those needs properly, rather than merely detecting things.

**No.** I have no relationship, integration, partnership or privileged access to any vendor
named in this document — Deswik, Micromine, Datamine, Maptek, Hexagon, Seequent, RPMGlobal,
Envirosuite, Borealis or any other. Everything about them here comes from their own public
marketing and from trade press, which turns out to be useful rather than a limitation: a
published capability list is a specification, and this report treats it as one (§2.2).

**Yes, and further than most people assume — but not uniformly.** Some of what an operator
sees can be mirrored from public data almost exactly; some approximately and honestly, with
stated error bars; some cannot be mirrored at all. Section 2.4 sets out which is which, layer
by layer, and is the analytical core of the whole document.

**Yes, and that is the harder half of the problem.** A regulator does not lack satellite
images — everything used here is already free and downloadable today. What the public sector
lacks is an apparatus that turns what the images show into communications its own
institutions can act on: an inspection order, a notice with a legal basis and a deadline, an
evidence dossier a court will accept, a budget line a legislature will fund, a page a
community can read. Section 2.8 argues that this translation *is* the product; section 2.9
describes how it was built; and roughly as much code went into the translation layer
(`dossier.py`) as into the detectors themselves.

The clearest evidence for the gap is Brazilian and it is measured, not estimated: the
Federal Court of Audit (TCU) found R$16.4 billion in mining royalties uncollected over eight
years, a six-person team contesting twelve thousand collection files, inspections down 92%
in five years, and an agency workforce down 41.9% since 1996 — against 443,000 hectares of
mapped mining disturbance, 92% of it in the Amazon (§2.3). No plausible increase in
headcount closes that gap. A satellite that revisits every point on Earth every few days, for
free, might.

**Observatório SOMA** is the
prototype built in response. One sentence
governs its design: *every number the system puts on a screen must be re-derivable, by a
third party, from public inputs, using only the manifest that accompanies it.* Everything
else — the guarded detectors, the cadastral tolerance applied in the title holder's favour,
the due-process state machine, the hash-chained evidence ledger, the five-register
translation layer, the refusal to act on simulated evidence — follows from that one
sentence.

Exercised blind against a deterministic simulator with known ground truth, the prototype
recovered disturbed area to within a few per cent, correctly detected and quantified a
routine-to-accelerated growth-rate change (0.70 → 4.65 ha/month against a simulated 0.71 →
4.5), correctly declined to raise a false alarm on a steady, compliant site, and correctly
kept three of its four demonstration cases out of public view because due process had not
yet run its course — publishing only the one that was examined and cleared (§2.10; §4 has
the full transcript). It has never seen a real satellite image; that is the single most
important limitation and §2.13 makes proving it on real imagery the first next step, not the
last.

**What is in this document.** This is the single-file edition of everything delivered, with
a strict decimal numbering — Indo-Arabic numerals throughout, no Roman numerals — and a
language selector: the buttons marked **EN** / **PT** (ISO 639-1 codes) switch this entire
document, section for section, between English and Brazilian Portuguese.

- **§2 — Report.** The full argument: the operator's stack as a specification, the measured
  capability gap, the asymmetry table, the public data and open-source estates, the
  Luhmannian translation argument, the Observatório SOMA proposal, prototype results and honest limits,
  deployment tiers and cost, objections taken seriously, and next steps.
- **§3 — Technical Architecture.** The specification a procurement process needs: layer by
  layer, with the design contract, dependencies, licensing and a repository map.
- **§4 — Demonstration Transcript.** Verified, re-run command output: the test suite, the
  four-site portfolio, ground-truth recovery, the evidence ledger and what happens when it is
  tampered with, due-process enforcement, and the synthetic-evidence guard.
- **§5 — Evidence Base.** The sourced research notes behind every factual claim in the
  document, organised by topic, each line carrying its source.
- **§6 — GIS Prototype.** Where and how the geospatial data and multi-agency registries (ANM,
  IBAMA, ICMBio, FUNAI, INCRA, ANA) would fit into an interactive view, with export of
  coordinates and process identifiers.
- **§7 — References.** The full bibliography in ISO 690 numeric format, linked from citation
  markers like **[1]** throughout the text above.

Alongside this document: `map.html` (the GIS prototype, with an OSM map and export),
`dashboard.html` (the working operational dashboard — open either in any browser, no
network needed), `soma/` (6,100 lines of runnable Python plus 720 lines of tests, zipped),
and `03-catalogues.xlsx` (every public data source, open-source component and jurisdiction
this architecture depends on, with licence, access method and maturity).

The prototype runs on **simulated** imagery, deliberately, for reasons §2.10.2 explains — but
nothing in this package is a claim about any real company or site, and the software refuses
by design to issue a legal act from simulated evidence.

## 2 Report

### 2.1 The question, restated

"Mining surveillance" is an unfortunate phrase in a document that will be read by lawyers,
so let me replace it with a sharper one.

A mining operation is an information asymmetry with a hole in the ground attached. The
operator knows, continuously and to a few centimetres, where its pit face is, how much
material it moved last shift, how much water is behind its tailings dam, how far the crest
has crept this month, and what it will declare to the state at the end of the quarter. The
state knows what the operator tells it, when the operator tells it, in the form the operator
chooses. The affected community knows what it can see from the road.

Every serious mining governance failure of the last decade sits inside that gap. Brumadinho
was a dam whose stability declaration had been signed. Under-collection of royalties is a
gap between declared and actual production. Illegal extraction inside Indigenous land is
extraction the state did not observe. The gap is not a policy failure; it is an
*observational* failure with policy consequences.

So the question is not "how do we watch mining companies". It is:

> **Can a public authority obtain, from data it is already entitled to, an independent
> picture of a mining operation good enough to act on — and can that picture be produced in
> a form that its own institutions, and the operator's right to defend itself, can both
> survive?**

This report argues yes, sets out exactly how far "good enough" reaches, and delivers a
working prototype of the answer.

---

### 2.2 What the operator's stack does

#### 2.2.1 The list you sent is a specification

The SourceForge listing for mining software in Europe shows thirty products [27]. Sorted by what
they actually do rather than by vendor, they cover twelve functional layers:

| Layer | Representative products on that page |
|---|---|
| Tenure, permits and land management | trueMINER; (and, off-page, acQuire, Landfolio) |
| Geological modelling and subsurface visualisation | RockWorks, LogPlot8, Surfer |
| Mine design, planning and scheduling | MineCycle (Bentley), Promine, Reactore/MineOne |
| Short-interval control and execution | ShiftManager (RPMGlobal), Lightship |
| Drill and blast | Blast Management System (MineExcellence) |
| Geotechnical and slope stability | Rocscience |
| Survey, volumetrics and progress | Propeller (drone), Strayos (3-D AI) |
| Process chemistry and metallurgical accounting | HSC Chemistry (Metso), INVENTEO (Caspeo, AMIRA P754) |
| Environmental data and monitoring | Envirosuite, EnviroDataVault (RPMGlobal) |
| EHS, inspections and workforce | Intelex, EHS Insight, SafetyIQ, PeopleTray, Pervidi, Inspectivity, Dashpivot |
| Stakeholder engagement and grievance | Borealis |
| Enterprise asset management and control | 4site, FrameworX, MineTwin, EarthCache |

Two things are worth noticing. First, that is a complete apparatus of *self-observation*: an
operator running the full stack knows more about its own site than any regulator could
learn by visiting. Second, several of these layers exist precisely because the operator must
report to the state — the environmental data management, the stakeholder grievance module,
the metallurgical accounting to a recognised code. **The instruments the state relies on to
supervise the industry are largely owned, operated and maintained by the industry.** That is
not an accusation of bad faith; it is a structural description, and it is the thing this
project is about.

#### 2.2.2 The market around it

The Global Mining Tech 50 puts 2025 mining- and metals-technology revenue for the top fifty
vendors at roughly **US$6.8 billion**, up **73.5%** over five years [19]. The consolidation is
vertical and recent:

- Caterpillar acquired **RPMGlobal** for about **US$728–735 million**, completing in February 2026 [1].
- Weir acquired **Micromine** for about **US$840 million**, completing in April 2025 [20].
- Sandvik owns **Deswik**; Bentley owns **Seequent** (Leapfrog, Evo).
- **Constellation Software** has bought more than thirty mining software firms since 2011;
  its flagship is **Datamine**.
- **Epiroc** has acquired thirteen mining-technology firms since 2021.

Equipment makers are buying the software that plans the work their machines do. The
practical consequence for a regulator is that the planning layer, the execution layer and
the reporting layer increasingly sit inside one commercial relationship, and the interfaces
between them are not public.

#### 2.2.3 What this costs a public body to match by procurement

Nothing in this report requires an estimate of licence fees, because the argument does not
depend on them. It is enough to observe that a national mining regulator in a middle-income
country will not procure a Deswik-and-Envirosuite stack across every site it supervises, and
that even if it did, it would be buying the operator's own tooling, applied to data the
operator supplies. The mirror has to be built out of something else.

---

### 2.3 What the public sector actually has

The Brazilian numbers are the clearest published evidence anywhere of the capability gap,
because the Federal Court of Audit measured it.

From the TCU's 2024 ruling on the Agência Nacional de Mineração [28]:

- Approximately **R$ 16.4 billion** in mining revenue was not collected over eight years:
  R$ 12.4 bn unrecovered over 2014–2021, R$ 4 bn lost to time-barred credits over 2017–2021,
  and **R$ 20 bn at risk of prescription**.
- The team responsible for contesting CFEM royalty collection is **six staff and one chief**,
  against roughly **12,000** collection files.
- The agency's workforce fell **41.9%** from its 1996 level, to 695 employees over 2010–2023.
- Inspections fell **92%**: from **2,184 audits in 2014 to 173 in 2019**.
- TCU ordered ANM to produce, within sixty days, a plan for a collection-and-enforcement
  system.

Set against that: ANM's tailings register (SIGBM) held **917 dams** [30] as of November 2025, of
which **470** fall under the national dam-safety regime, with **93 structures** in declared
alert or emergency (1 at level 3, 8 at level 2, 62 at level 1, 22 in alert). And MapBiomas
put Brazil's mined surface at **443,000 hectares** [16] in 2022 — 263,000 ha of it artisanal
garimpo — of which **92%** lies in the Amazon biome, with more than 25,000 ha inside
Indigenous Lands and 78,000 ha inside conservation units. Mining inside protected
territories grew **190%** over 2018–2022; inside Indigenous Lands, **265%**.

The arithmetic is the whole argument. One hundred and seventy inspections a year, against
tens of thousands of titles, hundreds of dams and 443,000 hectares of disturbed ground, is
not an enforcement regime. It is a sampling error. No plausible increase in headcount closes
that gap; a satellite that revisits every point on Earth every few days, for free, might.

This is not a Brazilian peculiarity, though Brazil has measured it more honestly than most.
Any jurisdiction where the number of supervised sites vastly exceeds the number of people
supervising them has the same structure, and that is nearly all of them.

---

### 2.4 The asymmetry, layer by layer

This is the analytical core of the report: what an operator sees, what a public body can see
from public data, and — stated plainly — what it cannot.

| # | Operator capability | Vendor examples | Public mirror | Public data behind it | Fidelity |
|---|---|---|---|---|---|
| 1 | Tenure and permit management | trueMINER, acQuire | **Cadastre engine** — polygon register, overlap detection against protected areas, title-status timeline | SIGMINE (daily, SHP+KML); EU member-state registries under the high-value-dataset regime | **Full.** The registry *is* the public copy. |
| 2 | Survey of the working surface | Total station, drone photogrammetry | **Footprint delineation** — disturbed-surface mapping at 10 m, every 5 days | Sentinel-2 L2A; Landsat 8/9 for the pre-2015 baseline | **High** for extent; the operator wins on precision, the public wins on frequency and history |
| 3 | Volumetrics and progress | Propeller, Strayos | **DEM differencing** — cut/fill and implied tonnage with explicit uncertainty | Copernicus DEM GLO-30 (free, <4 m absolute vertical); NASADEM/SRTM for a 2000 baseline; national photogrammetric DSMs | **Moderate.** Order-of-magnitude, wide intervals. Useful as an upper bound, never as a production figure. |
| 4 | Geotechnical and dam monitoring | Rocscience, instrumented crests | **InSAR displacement screening** — mm-scale line-of-sight movement and acceleration | EGMS (Europe, annual, free); self-processed Sentinel-1 via ISCE2/SNAP + MintPy/LiCSBAS elsewhere | **High for movement, none for cause.** Detects that a crest is moving; cannot say why or predict failure. |
| 5 | Tailings and water management | RPMGlobal, Envirosuite | **Pond extent, turbidity gradient, freeboard proxy** | Sentinel-2; JRC Global Surface Water; SIGBM and the Global Tailings Portal for the register | **Moderate.** Surface behaviour only. |
| 6 | Environmental monitoring | Envirosuite, EnviroDataVault | **Impact screening** — vegetation loss, deforestation alerts, dust and plume proxies | RADD (Sentinel-1, 10 m, near-real-time, CC BY); DETER/PRODES; Sentinel-5P for SO₂/NO₂ | **Moderate to high** for land cover; **low** for ambient concentrations without ground stations. |
| 7 | Metallurgical accounting | INVENTEO (AMIRA P754) | **Declaration screening** — declared production per active hectare, benchmarked against peers; cross-filing consistency | CFEM; Anuário Mineral Brasileiro; EITI reports; EU Accounting Directive Ch. 10; ESTMA | **Low as measurement, high as triage.** You cannot compute their tonnage. You can rank who is worth auditing. |
| 8 | Stakeholder and grievance management | Borealis | **Public grievance intake** with a published response obligation | Built, not borrowed (ODK/Kobo-style) | **Full**, and arguably better: the record is not held by the party complained about. |
| 9 | EHS incident management | Intelex, EHS Insight | **Public incident register**, cross-referenced with regulator and press records | Agency bulletins, labour inspectorate data, press | **Partial.** Depends entirely on the disclosure regime. |
| 10 | Mine planning, scheduling, reserve modelling | Deswik, Vulcan, Datamine, Leapfrog | **None** | — | **Not mirrorable.** Needs the drillhole database. |
| 11 | Fleet management and dispatch | Modular, Wenco, Cat MineStar | **None** | — | **Not mirrorable, and should not be.** |
| 12 | Process control / SCADA | FrameworX | **None** | — | **Not mirrorable.** |

Three observations about this table.

**The public sector wins on time, not on precision.** The operator's survey is
centimetric and monthly; the public mirror is metric and every five days, with a
continuous archive back to 2015 (Sentinel-2) or 1984 (Landsat). For the questions a
regulator actually asks — *did the footprint move outside the boundary; when did the rate
change; is the crest accelerating* — frequency and history beat precision.

**Rows 10 to 12 are not a gap to be closed.** A regulator does not need to model the
orebody or dispatch the trucks, and building toward that would be both futile and a
legitimate intrusion. Being explicit about this is what makes the rest credible. A proposal
that claims to mirror everything gets dismissed; one that says "these four things exactly,
and not these three" gets read.

**Row 7 is the one people get wrong.** The temptation is to convert observed footprint into
tonnes and compare that with declared production. Do not. The conversion needs stripping
ratio, ore grade, moisture, waste handling and stockpile movement, none of which are public,
and a demand built on that chain will not survive contest. What survives is relative
reasoning: intensity against peers, consistency between the operator's own filings, and the
clean case of visible activity with nothing declared at all.

---

### 2.5 The public data estate

Everything in this section is free, licensed for reuse, and available today.

#### 2.5.1 Earth observation

**Sentinel-1 (C-band radar).** Sentinel-1D completed commissioning and its data opened to
users on 17 April 2026, bringing the constellation to 1A + 1C + 1D (1B failed in 2022) [5, 11].
Radar sees through cloud and at night — the single fact that makes tropical mining
monitoring possible at all, since optical sensors lose the entire wet season.

**Sentinel-2 (optical).** Thirteen bands — four at 10 m, six at 20 m, three at 60 m — on a
290 km swath. Revisit is 10 days with one satellite, 5 with two, and 2–3 days at
mid-latitudes; a three-satellite configuration has been running since March 2025 with the
2A extension campaign now prolonged to the end of 2026. L2A surface reflectance is the
analysis-ready product; the archive runs from 2015.

**Copernicus DEM.** GLO-30 (30 m) and GLO-90 global, free worldwide, with absolute vertical
accuracy better than 4 m at 90% linear error and relative accuracy under 2 m on slopes up to
20%. EEA-10 (10 m) covers 39 European countries under restricted access. This is what makes
volumetric estimation a public capability at all.

**European Ground Motion Service.** Sentinel-1 interferometry across Europe at millimetre
accuracy, updated annually, in Basic / Calibrated / Ortho levels, downloadable from the EGMS
Explorer [10]. It exists explicitly for authorities monitoring dams and infrastructure and for
mining-induced subsidence. For a European deployment, the hardest technical layer in this
whole architecture arrives as a table.

**Landsat 8/9.** The pre-Sentinel baseline, back to 1984 across the archive — indispensable
for establishing what a site looked like before anyone was watching.

#### 2.5.2 The cost of all this

Copernicus Data Space Ecosystem free-tier quotas, as published, for an ordinary registered
user [3]:

- **12 TB per rolling 30 days** over S3 / OData / STAC, at 2,000 requests per minute and up
  to 20 MB/s per connection across four concurrent connections. Exceeding the quota degrades
  throughput to 1 MB/s rather than cutting access off.
- **50,000 direct COG requests per month**; **10,000 Sentinel Hub API requests** and
  **10,000 processing units** per month; **10,000 openEO credits** per month.

Twelve terabytes a month is not a constraint for a national mining monitoring programme —
it is roughly the whole Sentinel-2 archive over a large mining province, repeatedly. **The
data cost of monitoring every mine in a country is zero.** The cost is compute, storage and
— overwhelmingly — the people who read the outputs and decide what to do.

#### 2.5.3 Registries and cadastre

**Brazil.** ANM publishes, through dados.gov.br and its own open-data endpoints: SIGMINE
(polygons of every active and inactive mining process, shapefile and KML, daily); the
Cadastro Mineiro (requests, titles, holders, regimes, daily micro-datasets); CFEM collection
data; SIGBM (tailings dams with technical characteristics and tailings type, real-time);
TAH (annual per-hectare fee by process, year, holder and area); the Anuário Mineral
Brasileiro (production and destination since 2010); SICOP; the active-debt register; DIPEM;
and SOPLE. Bulk files sit at `dadosabertos.anm.gov.br`, with an ArcGIS REST service at
`geo.anm.gov.br`.

That combination is unusually strong. Title polygons plus royalty payments plus dam register
plus production yearbook, all public and all machine-readable, is exactly the input set this
architecture needs.

**European Union.** Commission Implementing Regulation (EU) 2023/138 designates six
categories of high-value dataset, two of which — **Geospatial** and **Earth observation and
environment** — cover the relevant material. Member states must publish them free of
charge, in machine-readable format, **with an API and bulk download**, under **CC BY 4.0 or
less restrictive**, with metadata per Regulation (EC) 1205/2008, at scales to 1:5000, and
must maintain both current and historical versions. Compliance was due around mid-2024.

This matters more than it first appears. The EU has already legislated the supply side of
this architecture. A member state that has implemented the high-value-dataset regime has,
without intending to, provisioned the cadastral and environmental inputs a public mining
monitor needs.

#### 2.5.4 Money

- **CFEM** (Brazil) — royalty payments per process: the declared-production proxy.
- **EU Accounting Directive, Chapter 10** — payments to governments by extractive companies.
- **ESTMA** (Canada) and equivalent regimes elsewhere.
- **EITI Standard 2023** — systematic disclosure, an explicit open-data policy, and
  strengthened beneficial-ownership and contract-transparency requirements [12].

The most productive check available needs no satellite at all: compare what one company
reported for the same site and period to three different regimes. Divergences between an
operator's own filings are the strongest and cheapest signal in this whole architecture.

#### 2.5.5 Environment

- **RADD forest disturbance alerts** — Wageningen University, Sentinel-1 based, **10 m**,
  near-real-time, covering 13 South American, 6 Central American, 25 African, 5 insular
  South-East Asian and 1 Pacific country, under **CC BY 4.0** [23].
- **DETER and PRODES** (INPE) — near-real-time and annual deforestation for Brazil, with
  open download and an API through TerraBrasilis.
- **MapBiomas** — annual land-cover and land-use series including a dedicated mining and
  garimpo module, with substance attribution.
- **Sentinel-5P** — SO₂ and NO₂ columns, useful for smelting and processing, too coarse for
  a single pit.

#### 2.5.6 Reference datasets

- **Global-scale mining polygons v2** (Maus et al. 2022): **44,929 polygons**, **101,583
  km²**, **145 countries**, digitised from 2019 Sentinel-2 cloudless mosaics within 10 km
  buffers of 34,820 known mine locations. Overall accuracy 88.3%, user's accuracy 97.2%,
  producer's accuracy 78.9%, F1 0.87. CC BY-SA 4.0 on PANGAEA [18].
- **Open database on global coal and metal mine production** (Jasansky et al. 2023):
  **1,171 mines**, **80 materials**, 2000–2021, 80 countries (Brazil: 89 facilities), hand-built
  from more than 1,900 public company reports with every datum linked to its source document.
  CC BY 4.0 on Zenodo; R code GPL-3. Known limits: China under-covered; copper coverage
  60–70%, gold 30–40%; excludes artisanal mining and in-situ leaching [15].
- **Global Tailings Portal** (GRID-Arendal with the Investor Mining and Tailings Safety
  Initiative): about **1,800 facilities** from about **100 companies**, twenty field
  categories including raising method, height, volume, hazard classification and downstream
  impact. Only **332 of 727** surveyed listed companies responded — which is itself a
  finding about the disclosure regime [14].
- **Global Coal Mine Tracker** (Global Energy Monitor): database plus wiki, validated
  against government sources, company reports, media, local NGOs and field contacts;
  annual update cycle since 2023 [13].

---

### 2.6 The open-source estate

#### 2.6.1 What exists, and is good

The geospatial open-source stack is mature, foundation-governed and in production use by
national agencies. QGIS was recognised as a **Digital Public Good** by the Digital Public
Goods Alliance in February 2025 [22] — a useful precedent for the classification of the platform
proposed here.

| Function | Component | Licence |
|---|---|---|
| Desktop GIS | QGIS | GPL-2.0-or-later |
| Raster/vector I/O and reprojection | GDAL/OGR | MIT/X-style |
| Spatial database | PostgreSQL + PostGIS | PostgreSQL Licence + GPL-2.0-or-later |
| Imagery catalogue | STAC spec, pystac, pystac-client, stac-fastapi, pgstac | Apache-2.0 / MIT |
| Data cubes and processing | Open Data Cube; openEO | Apache-2.0 |
| Archive access | eodag; CDSE OData/STAC/S3 clients | Apache-2.0 |
| Array processing | numpy, xarray, dask, rasterio, rioxarray | BSD-3 / Apache-2.0 |
| Image analysis and ML | scikit-image, scikit-learn, TorchGeo, segment-geospatial | BSD-3 / MIT |
| SAR and InSAR | ESA SNAP; ISCE2; MintPy; LiCSBAS; Orfeo ToolBox | GPL-3.0 / Apache-2.0 |
| Tiles and services | TiTiler, GeoServer, pygeoapi | MIT / GPL-2.0 |
| Portal and catalogue | GeoNode, CKAN | GPL-3.0 / AGPL-3.0 |
| Web mapping | MapLibre GL JS, deck.gl, leafmap | BSD-3 / MIT |
| Orchestration | Apache Airflow, Prefect | Apache-2.0 |
| Analytics | DuckDB, GeoParquet, Apache Superset | MIT / Apache-2.0 |
| Identity | Keycloak | Apache-2.0 |

#### 2.6.2 What does not exist in open source

There is no credible open-source equivalent of Deswik, Vulcan, Surpac, Datamine or Leapfrog.
GemPy is an excellent open-source implicit geological modeller and pygslib covers
geostatistics, but neither is a mine-planning system, and the gap in scheduling, reserve
reporting and metallurgical accounting is total.

**This does not matter for the public mirror**, because those are rows 10–12 of the
asymmetry table: capabilities a regulator does not need. It matters enormously if anyone
proposes an open-source alternative for *operators*, which is a different and much harder
project. Keeping the two apart is important; conflating them is the fastest way to lose an
audience of engineers.

#### 2.6.3 A licensing caution

**MinIO's community edition entered maintenance mode and was archived over 2025–2026**,
after features were stripped from the AGPL build. Any architecture that assumed MinIO as its
S3 layer now has a problem. Use SeaweedFS (Apache-2.0), Garage (AGPL-3.0), Ceph RGW, or the
sovereign cloud's own object store.

The general lesson is procurement policy rather than technology choice: pin to OSI-approved
licences, keep an exit path documented for every dependency, and re-verify licences at each
procurement cycle. Source-available relicensing has continued to catch infrastructure
projects, and a public body that discovers this after deployment has a much worse problem
than one that planned for it.

---

### 2.7 What already exists in the public interest — and why it is not enough

Real, working, credible systems already do parts of this.

**Amazon Mining Watch** (Earth Genome / Earthrise Media, with the Pulitzer Center) covers
all nine Amazonian countries [7, 6]. Its detector is an ensemble of six convolutional networks over
48×48×13 Sentinel-2 patches — roughly 480 m on a side — mostly around 800k parameters, with
one smaller model, averaged; it runs on multi-month median composites across the 8.2 million
km² basin. On a Venezuela geographic holdout it reports **99.4% specificity and 89.5%
sensitivity**; combined evaluation gives 99.8% / 92.4%. Scar masks are derived with SAM2.
Code is **MIT**, data products **CC BY 4.0**, bulk outputs on Source Cooperative.

**MAAP** publishes near-real-time gold-mining deforestation analyses for the Andean Amazon.
**SkyTruth** builds free, open tools including a mountaintop-mining tracker. **MapBiomas**
produces the annual Brazilian series. **Global Energy Monitor** and the **Global Tailings
Portal** maintain the facility registers. **Code for Africa** has begun an Africa Mining
Watch.

This is excellent work and the architecture proposed here should consume its outputs rather
than duplicate them — Amazon Mining Watch's detector is better than the rule-based one in
the prototype, and section 9 says so explicitly.

But none of them produces an **administrable act**. They produce maps, datasets and
journalism. What they do not produce — because it is not their job — is a record that an
official can put their name to, that names a legal basis, that opens a response window for
the party affected, that records what that party said, and that a court can accept. The
distance between "an AI model scored this pixel 0.87" and "the holder of title 830.123/2018
is notified that 36.6 hectares of disturbance were observed outside its polygon between
these dates, on this evidence, and has thirty days to respond" is the entire distance
between civic technology and public administration.

That distance is the gap this project addresses.

---

### 2.8 The real design problem: translation between systems

You work with Luhmann, so let me put the argument in those terms, because it is not
decoration — it determined the architecture.

A satellite detection is a communication in the register of remote sensing. It is
*meaningless* to the legal system, which processes communications through the binary
lawful/unlawful; to the administrative system, which processes them as competence,
procedure and act; to the political system, which processes them as budget and mandate; and
to the public sphere, which processes them as harm and responsibility. A quantity that
cannot cross those boundaries stays inside the technical system and changes nothing. That is
the observed fate of a great deal of very good environmental monitoring: the science is
sound, the pixels are correct, and nothing happens, because the finding never became a
communication any other system could operate on.

The environment "irritates" the legal system; it does not speak to it. What speaks to it is
a properly formed communication. So the product requirement is not *detection*. It is
**structural coupling**: an apparatus that takes an environmental irritation and produces,
from it, communications that each receiving system can process by its own code.

Concretely, the same sealed finding has to be rendered five ways — not five summaries of
it, five *translations*, each carrying the whole finding into a form the receiving system
can operate on, and each explicit about what it is not claiming:

| Register | Artefact | What it must carry | What it must refuse |
|---|---|---|---|
| Technical | **Technical annex** | Every input, algorithm version, parameter, hash; a reproduction recipe | Conclusions of law |
| Administrative | **Notice of observed facts** | Fact, applicable norm, response deadline, how to contest, where to get the raw data | Any finding of infraction — that is reserved to the official who signs |
| Legal | **Evidence dossier** | Chain of custody, the primary/derived distinction, stated limitations, procedural history | Intent, authorship, or the existence of an offence |
| Political | **Oversight brief** | Sites observed per member of staff, cases raised, cases cleared, what the counterfactual coverage was | Hectares as a headline |
| Public | **Site card** | What, where, how much, in plain language; whether the operator has answered | Any implication that a detection is a conviction |

This is why "a software that communicates these needs properly" is the right way to have
framed the request, and why the prototype puts as much code into `dossier.py` as into the
detectors.

One consequence deserves emphasis, because it is where most monitoring platforms fail
politically. **The operator is a receiving system too.** The notice is addressed to it; it
must be able to answer; its answer must enter the same record with the same protections;
and if the answer resolves the matter, the case must close *visibly*. A platform that only
accuses produces a stream of unfalsifiable allegations, and within one budget cycle nobody
in government will defend it.

---

### 2.9 Observatório SOMA: the proposal

#### 2.9.1 The epistemic contract

One sentence governs the whole design:

> **Every number the system puts on a screen must be re-derivable, by a third party, from
> public inputs, using only the manifest that accompanies it.**

That is testable, and it is tested. It is also what separates a regulator's instrument from
a black box: an operator who cannot reproduce a finding cannot meaningfully contest it, and
a finding that cannot be meaningfully contested will not survive judicial review.

Consequences that fall straight out of it: no proprietary imagery in the evidentiary path;
no unversioned algorithms; no undocumented parameters; no model whose training data cannot
be disclosed sitting on the critical path to a coercive act.

#### 2.9.2 The eight questions

The system exists to answer eight questions, and refuses to answer others:

1. Is there extraction where no title exists at all?
2. Is extraction outside the polygon of the title that authorises it?
3. Is extraction inside an area where it is categorically prohibited?
4. Is a title recorded as dormant, suspended or merely applied-for showing activity?
5. Is the rate of expansion changing, and when did it change?
6. Is a tailings structure moving, and is it accelerating?
7. Is the impounded water surface approaching the extent of its impoundment?
8. Is what has been declared consistent with what is visible, and with the operator's own
   other filings?

#### 2.9.3 Detectors, and why a rule beats a network here

The footprint detector in the prototype is a published spectral rule — NDVI below 0.30 [25],
MNDWI below 0.10 [31], BSI above 0.00 [24], SWIR-1 reflectance above 0.12, morphologically cleaned,
with a 0.5 ha minimum mapping unit — and not a convolutional network. A network would be
more accurate. Three reasons the rule is the default and the network is the upgrade:

1. **It can be written into a decision.** That threshold sentence can go into an
   administrative act and be contested on its merits. "The ensemble scored 0.87" cannot.
2. **It has no training-set provenance problem.** A learned model imports the biases of
   wherever its labels came from, and when it is used to justify coercive action against a
   named party, that provenance becomes discoverable.
3. **It degrades legibly.** When it fails, you can see which term failed.

The right architecture is both: the rule as the accountable baseline, a model (Amazon Mining
Watch's is the obvious candidate — MIT-licensed, already validated) as a recall booster
whose *extra* detections are triaged by a human before they enter a case. Never the model
alone on the path to an act.

#### 2.9.4 Due process as a state machine

Cases move through: `observed → screened → corroborated → notified → contested → reviewed →
substantiated | dismissed | referred → closed`.

The transitions are enforced in code, not in policy:

- **No transition without a named human and their role.** Automated advancement raises an
  exception. Software does not advance a case.
- **No notice from an uncorroborated case.** A single-sensor detection is not a sufficient
  basis for a coercive act, so the state machine will not permit one.
- **No review while the response window is open.** The case cannot proceed until the
  notified party has had the chance to answer or the window has expired.
- **Nothing is published before notification**, and a case that is notified but unresolved
  is visible to the notified party and to nobody else. Publishing an unresolved allegation
  imposes the reputational penalty before the procedure that is supposed to decide it.
- **A dismissal publishes a summary.** Being cleared is a public fact.

This is ordinary administrative due process — CF/88 art. 5, LIV and LV; Lei 9.784/1999;
Article 41 of the EU Charter — expressed as a state machine so that the software cannot skip
it. In the prototype's four-site portfolio, the only case that is publicly visible is the
one that was *cleared*. That is the correct behaviour and it surprises people, which is
precisely why it is worth demonstrating.

#### 2.9.5 Evidence and the ledger

Every finding carries an `EvidenceManifest`: inputs (identified, sourced, timestamped,
hashed), algorithms (named and versioned), every parameter, outputs (hashed), stated
assumptions and stated limitations. The manifest is canonicalised and hashed itself, and
appended to a hash-chained JSONL ledger in which each entry carries the hash of its
predecessor. Deleting or editing any past finding invalidates every later one, detectably.

This is a hash chain, not a blockchain: no consensus, no tokens, no distributed anything.
Public administration does not need distributed trust; it needs a record it can be held to.
Where stronger guarantees are wanted, the ledger head can be RFC 3161 timestamped or
published periodically in an official gazette — which is how notarial practice has solved
this for a century.

The relevant scholarship is thin but pointed: Muhammad's analysis [21] of Earth-observation
admissibility identifies exactly the vulnerability this addresses — that the path from
primary data to analysed information "requires a degree of manipulation", and that
authenticity is contested precisely there. His proposed remedies, data imaging and digital
audit, are what the manifest and the ledger implement.

#### 2.9.6 What the system refuses to do

Stated as design constraints, because a system's refusals are more informative than its
features:

- It does not predict tailings dam failure. It reports that a crest is moving faster than it
  was and recommends an engineering visit.
- It does not compute a tonnage from a footprint and does not assess royalties owed. It
  ranks sites for audit and says why.
- It does not report turbidity as contamination. It triggers a sampling campaign.
- It does not count area inside the boundary tolerance against a holder.
- It does not issue an administrative notice or a judicial dossier from simulated evidence —
  enforced by a guard with a test behind it.
- It does not treat absence of observation as absence of activity. Observation gaps are
  reported as findings in their own right.

---

### 2.10 The prototype, and what it showed

#### 2.10.1 What was built

About 6,100 lines of Python, with 720 more of tests: geometry on the ellipsoid without a geospatial stack; a scene
model with per-pixel validity; a real STAC provider written against the Copernicus Data
Space Ecosystem and Element 84 Earth Search; a deterministic simulator; five detectors
(footprint, water, change, deformation, volume); cadastral and declaration cross-checks; the
evidence manifest and ledger; the case state machine; the five-register dossier generator;
chart and evidence-image rendering; a CLI; and **49 tests, all passing**.

The core has **no mandatory geospatial dependencies**. numpy is required; scipy and
scikit-image are used where present. GDAL, rasterio, shapely and pyproj are optional
accelerators. A municipal environment agency with one laptop and no procurement budget can
run the detection library. That was a design goal, not an accident.

#### 2.10.2 Why the demonstration runs on simulated imagery

The sandbox this was built in has no outbound network access to STAC endpoints, so the
pipeline could not be pointed at live Copernicus data. Rather than ship pseudocode, the
provider interface was split: a real `StacSentinel2Provider` written against the live APIs,
and a `SyntheticProvider` that generates physically plausible Sentinel-2 L2A reflectance
for a simulated site — including a growing pit, a tailings impoundment, haul roads, a river,
seasonal cloud with wet-season loss, and a paired DEM.

That turned out to be worth keeping regardless, for three reasons an adopting agency will
recognise: detectors can be regression-tested against known ground truth, so a threshold
change that costs 3 ha of recall shows up in CI; an agency can watch the system find
something it already knows the answer to before trusting it on something it does not; and
the whole pipeline is demonstrable with no network at all, in a prosecutor's office or a
hearing room.

#### 2.10.3 Results

The simulator was configured with a known truth: routine expansion at about **0.7 ha per
month**, stepping up to about **4.5 ha per month** in July 2025, with the working face
crossing the licence boundary in September 2025 into an adjacent conservation unit.

Running blind on the resulting imagery, the pipeline reported:

| Quantity | Detected | Simulated truth |
|---|---|---|
| Disturbed surface, July 2026 | 129.7 ha | 126.2 ha |
| Growth rate before the change | 0.70 ha/month | ~0.71 ha/month |
| Growth rate after the change | 4.65 ha/month | ~4.5 ha/month |
| Date of the rate change | May 2025 | July 2025 |
| Outside the licensed polygon | 36.6 ha | (by construction, post-Sept 2025) |
| Inside the conservation unit | 30.6 ha | (by construction) |
| Impounded water, peak | 22.3 ha | 22.3 ha |

Areas track truth to within a few per cent on fully observed dates. The rate change was
found and quantified correctly; its *date* was recovered two months early, which is an
honest characterisation of what a breakpoint fit on monthly composites can do and is
reported as such rather than smoothed over.

Equally important is what the system did **not** report. Of four sites in the demo
portfolio, one was entirely compliant. It was raised by the routine screen, examined, and
**cleared** — and it is the only one of the four whose case is publicly visible, because the
other three are either pre-notification or notified-and-unresolved. A steady site did not
get a spurious "rate change" alert; that required adding a guard requiring the two segment
slopes to be statistically separated, without which quiet sites reported regime changes
every time a short cloud-thinned series wobbled. That guard has a regression test, because
a system that cries wolf about rate changes stops being read within a month.

#### 2.10.4 Honest limits of the prototype

- Simulated imagery is not real imagery. Real scenes have terrain shadow, haze, sensor
  artefacts, agricultural bare soil that looks spectrally like a mine, and burn scars. The
  false-positive rate on real data is unknown and must be measured before deployment.
- Thresholds are humid-tropical defaults. They must be calibrated against local ground truth
  for any other setting.
- The InSAR module consumes displacement time series; it does not process interferograms.
  For Europe, EGMS supplies them. Elsewhere, the ISCE2/SNAP + MintPy chain must be stood up,
  and that is real work.
- The volumetric module was exercised on a synthetic DEM pair with a known excavation. On
  real DEMs the systematic co-registration error dominates, which the error model reflects
  but which no error model can remove — that requires co-registration on stable ground.

---

### 2.11 Deploying it

#### 2.11.1 Three tiers

**Tier 1 — a municipality or a prosecutor's office.** One analyst, a laptop, QGIS, the
detection library, imagery pulled from the Copernicus free tier for a handful of sites.
Runs offline. Produces annexes and notices for cases someone is already working. Standing up
takes weeks, not years, and costs the analyst's time.

**Tier 2 — a state environmental agency.** A modest server, PostGIS, Airflow, a STAC
catalogue, twenty to a few hundred sites on a monthly cadence, a public portal under the
access-to-information regime. One or two technical staff plus the inspectors who already
exist.

**Tier 3 — a national regulator.** Full cadastral coverage, systematic screening of every
active title, the tailings register wired to a deformation service, integration with the
royalty system, published open data, an API. This is where the TCU's finding gets answered:
not by hiring back the 41.9% of ANM's workforce that was lost, but by making sure that the
173 inspections a year that do happen are aimed at the right 173 sites.

#### 2.11.2 Cost

Data: **zero**, within quotas that are not binding at this scale. Software: **zero** in
licence terms, with all components OSI-licensed. Compute and storage: modest — this is
embarrassingly parallel work on 10 m imagery over small areas, and a mid-sized server
handles a national programme.

The real cost is people, and it is not small: analysts to triage, technical officers to
corroborate, officials to sign, lawyers to draft, and the institutional will to act on
what comes out. Any proposal that presents this as a technology purchase rather than a
capacity programme is misrepresenting it.

#### 2.11.3 Sovereignty and the digital public good route

The platform should be developed as a **digital public good**: OSI-approved licence, open
standards (STAC, OGC API, GeoParquet, COG), no vendor lock-in, deployable on national
infrastructure or air-gapped. QGIS's recognition by the Digital Public Goods Alliance in
February 2025 is the precedent and the DPG Standard is the checklist.

The reason is not ideological. A mining regulator's monitoring system that runs on a foreign
commercial platform is a monitoring system whose continuity depends on a commercial
relationship the regulator does not control, in a sector where the regulated parties are
large enough to have views about that. Sovereignty here is a risk control.

---

### 2.12 Objections, taken seriously

**"This is surveillance."** It is observation of industrial activity on public land under
public licence, from data anyone may download, of sites whose coordinates are already
published in the cadastre. It is not observation of persons. The design deliberately
excludes anything at the resolution where individuals become identifiable and works with
10 m public imagery rather than sub-metre commercial imagery. The word in your original
message is the right word for the function and the wrong word for the politics; "oversight"
or "verification" will get further.

**"Satellite evidence will not hold up."** Sometimes it will not, and the honest response is
to build for that rather than deny it. The manifest, the version pinning, the parameter
record, the hash chain and the reproduction recipe exist because the vulnerability is real
and identified in the literature. Note also that the system's outputs are mostly *not*
offered as proof of an offence: they are offered as the basis for a notice that opens a
procedure. That is a much lower and much more defensible bar.

**"The agency cannot act on more alerts than it already ignores."** This is the strongest
objection and the reason severity ranking and the dismissal path are in the design. The
system's value at Tier 3 is not more alerts; it is *the same number of inspections aimed
better*. An oversight brief that reports sites-per-inspector and cases-cleared, rather than
hectares detected, is written for exactly this argument.

**"Operators will game it."** Some will. Working under cloud, revegetating quickly,
staging material to look like a stockpile. Radar defeats the first; the archive defeats
the second; DEM differencing constrains the third. More to the point, gaming a public
detector is expensive and detectable, and the operators most likely to try are the ones
whose behaviour you most want to make expensive.

**"It will be used politically."** Yes — any oversight instrument can be. The mitigations
are structural, not rhetorical: publication rules that prevent an unresolved allegation
being aired; a dismissal path that is public; an evidence chain that makes selective
deletion detectable; and outputs anyone can reproduce, so a politically motivated finding
can be checked by the other side.

**"False positives will destroy its credibility."** Correct, and this is the operational
risk that matters most. Hence the minimum mapping unit, the boundary tolerance applied in
the holder's favour, the corroboration requirement before any notice, the separated-slopes
guard on rate changes, and the treatment of dismissal as a quality metric rather than a
failure. A screening system with a zero dismissal rate is not screening; it is confirming
what was already believed.

**"This duplicates MapBiomas / Amazon Mining Watch / the agency's own system."** It consumes
them rather than duplicating them. What none of them provides is the administrative and
evidentiary layer, and that is the deliverable.

---

### 2.13 What I would do next

**Months 0–3 — prove it on real imagery.** Point the STAC provider at the Copernicus Data
Space Ecosystem. Take twenty Brazilian sites with known outcomes — ideally ones with existing
ANM or MPF proceedings, so ground truth exists — and measure precision and recall on real
data. Publish the confusion matrix. This is the step that either validates or kills the
project and it should come first.

**Months 3–6 — calibrate and harden.** Local thresholds. Add the Amazon Mining Watch model
as a second opinion. Wire SIGMINE, CFEM and SIGBM ingestion to the live endpoints. Build
the ISCE2/MintPy chain for one tailings structure and compare it against whatever
instrumented record exists.

**Months 6–9 — put it in front of an institution.** Not a pilot deployment: a single real
case, worked end to end with a real official, through notification and response, to a real
outcome. Everything you learn that matters, you learn there.

**Months 9–12 — publish.** Code under an OSI licence, submitted to the DPG registry.
Methodology paper. An open-data endpoint for the findings that are lawfully publishable.
Then approach a second jurisdiction, because the second deployment is what proves it is a
platform rather than a project.

**A note on where to start institutionally.** Do not start with the mining regulator. Start
with the audit court or the public prosecutor — a body whose mandate is oversight rather
than sector development, which has an existing information-request power, and which has
already publicly identified the capability gap. The TCU has done exactly that in writing.
An instrument that answers a finding the institution has already made about itself has a
much easier path than one that arrives as an outside critique.

---

## 3 Technical Architecture

**Mineral Extraction Verification & Regulatory Accountability.** An open mirror of the mining operator's software stack, for the public sector. Version 0.1.0 · companion specification to §2.

### 3.1 Design contract

Everything below follows from one commitment:

> Every number the system puts on a screen must be re-derivable, by a third party, from
> public inputs, using only the manifest that accompanies it.

Six consequences, each of which is a hard constraint rather than a preference:

| Constraint | Because |
|---|---|
| No proprietary imagery on the evidentiary path | A finding the affected party cannot reproduce cannot be meaningfully contested |
| Every algorithm versioned; behaviour change requires a version bump | Otherwise past findings are silently invalidated — the geospatial equivalent of losing the chain of custody |
| Every parameter recorded in the manifest, not in a config file somewhere | A threshold that is not in the record is a threshold nobody can challenge |
| No model whose training data cannot be disclosed on the path to a coercive act | Training-set provenance becomes discoverable the moment the output justifies action against a named party |
| No transition without a named human | Software does not decide; officials do |
| Observation gaps are findings, not nulls | "We could not see" and "nothing happened" are different claims and must never be collapsed |

---

### 3.2 Layers

```
┌──────────────────────────────────────────────────────────────────────────┐
│  8  AUDIT           append-only hash-chained ledger · replay recipes     │
├──────────────────────────────────────────────────────────────────────────┤
│  7  PUBLICATION     OGC API Features/Tiles/Records · open-data export    │
│                     public portal · notification channels                │
├──────────────────────────────────────────────────────────────────────────┤
│  6  TRANSLATION     technical annex · administrative notice ·            │
│                     judicial dossier · oversight brief · public card     │
├──────────────────────────────────────────────────────────────────────────┤
│  5  CASE            state machine with due process enforced in code      │
├──────────────────────────────────────────────────────────────────────────┤
│  4  RECONCILIATION  cadastre · restricted areas · declarations · filings │
├──────────────────────────────────────────────────────────────────────────┤
│  3  OBSERVATION     footprint · water · change · deformation · volume    │
├──────────────────────────────────────────────────────────────────────────┤
│  2  STORE           PostGIS · object store (COG) · STAC · GeoParquet     │
├──────────────────────────────────────────────────────────────────────────┤
│  1  ACQUISITION     STAC providers · registry connectors · InSAR feeds   │
├──────────────────────────────────────────────────────────────────────────┤
│  0  PLATFORM        sovereign infrastructure · OSI-licensed throughout   │
└──────────────────────────────────────────────────────────────────────────┘
```

Layers 1, 3, 4, 5, 6 and 8 are implemented in the prototype. Layers 2 and 7 are specified
here and are conventional; nothing about them is novel and nothing about them is hard.

---

### 3.3 Layer 1 — acquisition

#### 3.3.1 Imagery providers

A provider turns *(site geometry, date range)* into a list of `Scene` objects. The interface
is deliberately narrow so that a national deployment can add its own archive — CBERS-4A in
Brazil, a regional receiving station in Africa — without touching a detector.

```python
class SceneProvider(ABC):
    def search(self, site_id, aoi, start, end, grid=None, max_cloud=0.6) -> List[Scene]: ...
```

Two implementations ship:

**`StacSentinel2Provider`** — production. Written against:

| Catalogue | Root | Collection | Auth |
|---|---|---|---|
| Copernicus Data Space Ecosystem | `https://catalogue.dataspace.copernicus.eu/stac` | `SENTINEL-2` | yes |
| Element 84 Earth Search | `https://earth-search.aws.element84.com/v1` | `sentinel-2-l2a` | no |

Handles both asset-key conventions (`blue`/`B02`, `swir16`/`B11`, `scl`/`SCL`), applies the
**L2A offset of −1000 for processing baseline ≥ 04.00** — getting this wrong shifts every
index and is the most common Sentinel-2 pipeline error — and screens with the Scene
Classification Layer, rejecting classes 0, 1, 3, 8, 9 and 10.

Composites are per-pixel **medians** over valid pixels within a calendar month. Median
rather than mean: a single undetected cloud edge biases a mean and does not move a median,
and the point of a monthly composite is to survive the tropics.

**`SyntheticProvider`** — deterministic simulation for testing, acceptance and air-gapped
demonstration. Generates plausible L2A reflectance for a landscape with a growing pit, a
tailings impoundment, waste dumps, haul roads, a river, seasonal cloud with occasional
total wet-season loss, and a paired DEM. Every artefact it produces is stamped
`provider="synthetic"` and the dossier layer refuses to issue a legal act from it.

#### 3.3.2 Registry connectors

| Source | Endpoint | Cadence |
|---|---|---|
| ANM SIGMINE (title polygons) | `dadosabertos.anm.gov.br/SIGMINE/PROCESSOS_MINERARIOS/`; ArcGIS REST at `geo.anm.gov.br` | daily |
| ANM Cadastro Mineiro, CFEM, SIGBM, TAH, AMB, SICOP, Dívida Ativa, DIPEM, SOPLE | dados.gov.br | daily to real-time |
| Protected areas | CNUC, FUNAI, WDPA | as published |
| EU member-state cadastres | national HVD endpoints under Reg. (EU) 2023/138 — API and bulk, CC BY 4.0 | per member state |
| EGMS ground motion | `egms.land.copernicus.eu` | annual |
| RADD alerts | Global Forest Watch / Wageningen | near-real-time |
| DETER / PRODES | TerraBrasilis | near-real-time / annual |

Every connector records what it fetched, when, from where, under what licence, and with what
checksum. That record is an input to the manifest and is not optional.

#### 3.3.3 InSAR

Two paths, chosen by geography:

- **Europe** — consume EGMS Level 2b/3 point products directly. Velocity and displacement
  time series arrive as a table; no processing.
- **Elsewhere** — ISCE2 or ESA SNAP for interferograms, MintPy or LiCSBAS for time-series
  inversion. Heavier, wholly open, wholly reproducible.

The observation module consumes `DeformationSeries` objects in either case, so the
downstream code does not know or care which path produced them.

---

### 3.4 Layer 2 — store

Conventional and deliberately boring:

| Concern | Choice | Note |
|---|---|---|
| Vector, cases, ledger | PostgreSQL 16 + PostGIS 3 | The ledger is also mirrored to plain JSONL, so it survives the database |
| Imagery | Cloud-Optimised GeoTIFF in an S3-compatible store | **Not MinIO** — community edition archived 2025–26. Use SeaweedFS, Garage, Ceph RGW, or the sovereign cloud's own |
| Imagery catalogue | STAC via `stac-fastapi` + `pgstac` | The same standard the upstream archives use |
| Analytics | GeoParquet + DuckDB | Findings tables are small; this needs no cluster |
| Orchestration | Apache Airflow (or Prefect) | One DAG per site per cadence |
| Identity | Keycloak | Roles below |

**Roles.** `analyst` (may screen), `technical_officer` (may corroborate), `inspecting_official`
(may notify, may record a response), `legal` (may refer), `coordinator` (may close),
`public` (sees only what publication rules permit). The case state machine checks the role
on every transition; there is no path that bypasses it.

**Retention.** Manifests and ledger entries are permanent. Imagery need not be: the manifest
names the granule identifiers, and the granules are re-obtainable from the public archive
for as long as the archive exists — which for Copernicus is a policy commitment, not a
vendor's goodwill.

---

### 3.5 Layer 3 — observation

Every detector returns an `Observation`, never a bare number:

```python
@dataclass
class Observation:
    site_id: str; acquired: date
    detector: str; algorithm_version: str
    quantity: str; value: float; units: str
    valid_fraction: float          # share of the assessment area actually observable
    reliability: str               # ok | degraded | unusable
    params: dict; detail: dict; mask: Optional[np.ndarray]
```

**`reliability` has three states, not two.** A regulator must distinguish "we measured it"
from "we half-measured it" from "we could not see". Collapsing the last two into a null is
how monitoring programmes end up under-reporting activity in exactly the wet season when
illegal operators prefer to work.

**Visibility is judged over an assessment area, not over the scene.** Cloud over an empty
corner says nothing about how well the workings were seen; cloud over the workings says
everything. The default assessment area is the licence polygon buffered by 1 km — wide
enough to contain a plausible excursion, narrow enough that weather in the far corner does
not discard a good measurement.

#### 3.5.1 Footprint (`footprint.spectral_rule` v1.0.0)

```
disturbed = NDVI < 0.30
          & MNDWI < 0.10
          & BSI   > 0.00
          & B11   > 0.12
          & NBR   < 0.62
          & valid
→ morphological opening (r=1) then closing (r=2)
→ drop components below the 0.5 ha minimum mapping unit
```

Indices are the published ones (Rouse 1974; Xu 2006; Rikimaru et al. 2002; Key & Benson
2006) and the citations travel in the manifest. Thresholds are humid-tropical defaults,
are parameters, and must be calibrated locally before anything is issued.

*Upgrade path.* Add a learned detector as a **second opinion**, not a replacement — the
Earth Genome / Amazon Mining Watch ensemble is MIT-licensed and already validated (99.4%
specificity / 89.5% sensitivity on a geographic holdout). Its *extra* detections are triaged
by a human before they may enter a case. The rule remains the accountable baseline for
anything that reaches an act.

#### 3.5.2 Water (`water.pond_extent` v1.0.0)

MNDWI > 0.10 and NDVI < 0.20, opened, with a 0.5 ha minimum. Process water is separated from
natural water by turbidity (NDTI) and green brightness. Restricted to the licence polygon:
the question is how much water the operator is impounding, and a river crossing the scene is
not that. A `freeboard_proxy` expresses pond area as a fraction of the impoundment's mapped
extent; above 0.90 the water surface is approaching the structure's footprint.

`turbidity_gradient` compares NDTI between an upstream and a downstream reach of the same
river, using the river as its own control to cancel most atmospheric and illumination error.
Output is a **screening proxy for suspended sediment and a trigger for sampling** — never a
water-quality determination, and the dossier says so in those words.

#### 3.5.3 Change (`change.robust_trend` v1.0.0)

Fits only fully observed dates. Cloud-limited dates are lower bounds and are reported
separately, never joined to the line — joining them draws a fall in the footprint that never
happened.

- **Theil–Sen** median-of-pairwise-slopes, with a 68% interval from the 16th/84th
  percentiles. Breakdown point 29%; ordinary least squares has a breakdown point of zero,
  which is the wrong property for cloud-screened composites.
- **Single-breakpoint search** with four guards, each of which exists because without it
  the fit reports a regime change that is not there:
  1. ≥ 5 observations each side;
  2. ≥ 5 months span each side;
  3. ≥ 25% improvement in residual sum of squares over the single-line fit;
  4. **the two segment slopes' 68% intervals must not overlap.** Guard 4 does most of the
     work. Without it, a quiet compliant site reports a rate change every time its first few
     months wobble — and a regulator told about a rate change that is not there stops
     believing the ones that are.
- **`current_rate_per_month`** is the post-breakpoint slope where one exists, otherwise the
  whole-period slope. When a series has a regime change, the whole-period slope is a blend
  of two rates and describes neither.
- **`observation_gaps`** lists every interval longer than 75 days with no usable
  observation. Reported alongside every trend.

#### 3.5.4 Deformation (`deformation.velocity_screen` v1.0.0)

Consumes persistent-scatterer series. Screens on the **recent** velocity (default: last 365
days) rather than the whole-history velocity, and reports both. A crest that crept at
2 mm/yr for four years and 30 mm/yr for six months has a whole-history velocity of about
6 mm/yr, which is reassuring and wrong.

Flags: `velocity_exceeds_threshold` (10th percentile of recent velocities beyond −10 mm/yr),
`accelerating` (median quadratic term beyond −6 mm/yr²), and
`recent_velocity_at_least_double_historic`.

Fewer than five coherent points over the structure returns `unusable` with a stated reason
and a recommendation — vegetated or freshly reworked crests decorrelate, and the honest
output is "this technique cannot see this structure; use corner reflectors or another
method", not a number.

**The module does not predict failure.** It reports that a crest is moving faster than it
was and that an engineering inspection is warranted.

#### 3.5.5 Volume (`volume.dem_difference` v1.0.0)

Cut and fill between two elevation surfaces, with a two-term error model:

```
sigma_random     = sigma_z · cell_area · L · sqrt(n)      # L = correlation length, default 10 cells
sigma_systematic = bias_sigma · changed_area             # default bias_sigma = 0.5 m
sigma_total      = hypot(sigma_random, sigma_systematic)
```

The systematic term normally dominates and is reduced only by co-registering the two
surfaces on stable ground outside the workings; a deployment must record that this was done.
The naive independent-error assumption understates the interval by roughly an order of
magnitude.

Output is an **interval**, never a point value, and is labelled *material moved, not
material sold* — waste rock, overburden and stockpile rehandling are all included. Use as an
upper bound on extraction; never as a production figure.

---

### 3.6 Layer 4 — reconciliation

#### 3.6.1 Cadastre (`crosscheck.cadastre` v1.0.0)

Splits the disturbed footprint into three classes against each title:

- **confidently inside** — within the polygon eroded by the boundary tolerance;
- **confidently outside** — outside the polygon dilated by the tolerance;
- **indeterminate** — in the annulus between them.

`BOUNDARY_TOLERANCE_M = 25.0` by default: Sentinel-2 geolocation is specified better than
11 m at 95%, and cadastral vector error in most registries is of the same order or worse.
**The tolerance is applied in the holder's favour and indeterminate area is never counted as
a violation.** This single decision is the difference between a system a mining lawyer
dismantles in an afternoon and one that holds.

Also emits registry notes: activity inside a dormant, suspended, expired or merely
applied-for title; activity where no title of any status covers the footprint; activity
inside an exploration-phase title, which does not authorise extraction.

#### 3.6.2 Declarations (`crosscheck.declaration` v1.0.0)

**Do not convert footprint to tonnes and compare with declared production.** The conversion
needs stripping ratio, ore grade, moisture, waste handling and stockpile movement, none of
which are public. A demand built on that chain will not survive contest.

What the module does instead:

| Check | Signal |
|---|---|
| **Activity without declaration** | ≥ 5 ha of active disturbed surface in a period with nothing declared. Needs no conversion factor at all. |
| **Intensity against peers** | Declared tonnes per active hectare per month, placed in the decile distribution of comparable operations (same commodity, method, region). Bottom decile is a flag. |
| **Growth against declaration** | Top-decile footprint growth combined with bottom-decile declared intensity. |
| **Cross-filing consistency** | The same quantity as reported to CFEM, to shareholders, and under EU Accounting Directive Ch. 10 / ESTMA. Needs no remote sensing whatsoever and is frequently the most productive check available. |

Output is an **audit priority score with reasons**, stamped:

> SCREENING RESULT — audit prioritisation only. Not an assessment of tax or royalty owed,
> and not evidence of under-declaration.

Every flag ships with its innocent explanations named — waste stripping ahead of ore,
stockpile build, pre-production development — because the audit exists to test them.

#### 3.6.3 Severity

Ranked by what is at stake, not by hectares:

| Level | Trigger |
|---|---|
| **critical** | deformation flags on a tailings structure; > 5 ha inside a restricted area; > 5 ha on a title that authorises nothing (requested/expired) |
| **high** | > 5 ha outside the titled polygon; > 5 ha on a suspended title; audit priority ≥ 0.5; any restricted-area overlap |
| **medium** | > 1 ha outside the polygon, or any declaration flag |
| **low** | everything else |

Ten hectares inside a conservation unit outranks fifty hectares of lawful expansion, and an
accelerating crest outranks both — nothing else on the list can kill anyone.

---

### 3.7 Layer 5 — case, and due process in code

```
observed → screened → corroborated → notified → contested → reviewed
                          ↓              ↓          ↓          ↓
                      dismissed ←────────┴──────────┴──── substantiated → referred → closed
```

Enforced invariants, each with a test:

| Invariant | Enforcement |
|---|---|
| Every transition names a human and a role | `DueProcessError` on empty actor |
| A notice requires a corroborated case | `administrative_notice()` refuses otherwise |
| A case cannot be reviewed while the response window is open | `DueProcessError` unless a response was recorded or the window expired |
| Nothing is public before notification | `public_view()` returns `None` |
| A notified-but-unresolved case is visible to the notified party only | `PublicationState.PARTY_ONLY` |
| A dismissal is published as a summary | `PublicationState.PUBLIC_SUMMARY` |
| A response is evidence of the same rank as the state's | stored, hashed, ledgered |

Publication states: `internal → notified_party_only → public_summary | public_full`.

The reason a notified-but-unresolved case stays out of public view is not squeamishness.
Publishing an unresolved allegation imposes the reputational penalty before the procedure
that is supposed to decide it — and a platform that does that will, correctly, be enjoined.

---

### 3.8 Layer 6 — translation

The same sealed finding, rendered five ways. Not five summaries: five translations, each
explicit about what it does not claim.

| Method | Register | Carries | Refuses |
|---|---|---|---|
| `technical_annex()` | technical | every input, algorithm, parameter, hash; reproduction recipe | conclusions of law |
| `administrative_notice()` | administrative | fact, norm, deadline, how to contest, where to get the raw data | any finding of infraction |
| `judicial_dossier()` | legal | custody, primary vs derived distinction, limitations, procedural history | intent, authorship, existence of an offence |
| `oversight_brief()` | political | sites per member of staff, cases raised, cases cleared | hectares as a headline |
| `public_card()` | public sphere | what, where, how much, in plain words; whether the operator answered | any implication that a detection is a conviction |

Jurisdictions are configured as `LegalFrame` objects carrying the applicable norms; `BRAZIL`
and `EUROPEAN_UNION` ship, and the notice renders in Portuguese or English accordingly.

**The synthetic-evidence guard.** `administrative_notice()` and `judicial_dossier()` raise
`SyntheticEvidenceError` if the evidence chain contains simulated inputs. The technical
annex is permitted, with a SIMULATION banner.

---

### 3.9 Layer 8 — audit

**`EvidenceManifest`** — `manifest_id`, `site_id`, the regulatory question, creation
timestamp, software versions, inputs (kind, identifier, source, retrieval time, licence,
checksum), algorithms (name, version, parameters, reference), outputs (name, value, units,
digest), assumptions, limitations, jurisdiction, evidential status, `prev_hash`,
`manifest_hash`. Canonical JSON — sorted keys, no incidental whitespace — so one
serialisation gives one hash.

**`Ledger`** — append-only JSONL, each entry carrying the hash of its predecessor.
`verify_chain()` re-computes every hash and every link and returns a report rather than
raising: a broken chain is a fact to be reported to whoever is responsible for the register,
not an exception to be swallowed.

**`replay_recipe()`** emits the commands and inputs that reproduce a finding.

For stronger guarantees than an internal chain provides, timestamp the ledger head with
RFC 3161, or publish it periodically in an official gazette. This is a hash chain, not a
blockchain: public administration does not need distributed trust, it needs a record it can
be held to.

---

### 3.10 Dependencies and licensing

**Core (mandatory):** Python ≥ 3.10, numpy. That is all.
**Recommended:** scipy, scikit-image, matplotlib, Pillow.
**Production:** pystac-client, rasterio, GDAL, PostgreSQL + PostGIS, Airflow, Keycloak.
**Optional accelerators:** shapely, pyproj, dask, TorchGeo.

The core has no mandatory geospatial dependencies. A municipal agency with one laptop and no
procurement budget can run the detection library — a design goal, not an accident.

Licence policy: OSI-approved only; a documented exit path for every dependency; licences
re-verified at each procurement cycle. **MinIO is excluded** (community edition archived
2025–26). AGPL components (Grafana, Metabase OSS, CKAN, Garage) are fine to run but have
procurement implications if the institution modifies them and exposes them as a service.

Target classification: **Digital Public Good**, against the DPG Standard, following QGIS's
recognition in February 2025.

---

### 3.11 Deployment tiers

| | Tier 1 — municipality / prosecutor | Tier 2 — state agency | Tier 3 — national regulator |
|---|---|---|---|
| Sites | 1–20 | 20–500 | full cadastre |
| Cadence | on demand | monthly | monthly, with radar alerting between |
| Infrastructure | one laptop, offline | one server | small cluster |
| Storage | GB | low TB | tens of TB |
| Imagery cost | 0 | 0 | 0 (inside CDSE free-tier quotas) |
| Staff | 1 analyst | 1–2 technical + existing inspectors | small unit + existing inspectorate |
| Outputs | annexes for cases already open | portal + notices | open data, API, royalty integration |

---

### 3.12 What is not built, and what it would take

| Gap | Effort | Note |
|---|---|---|
| Live STAC ingestion exercised against real imagery | 2–4 weeks | The provider is written; the sandbox had no egress. **Do this first.** |
| Precision/recall on real scenes with known outcomes | 4–8 weeks | The step that validates or kills the project |
| InSAR processing chain outside Europe | 6–10 weeks | ISCE2/SNAP + MintPy; Europe gets EGMS free |
| Learned detector as second opinion | 3–5 weeks | Amazon Mining Watch weights are MIT |
| Portal, OGC API, open-data export | 6–8 weeks | Conventional; GeoNode or pygeoapi |
| Grievance intake | 4 weeks | ODK/Kobo pattern |
| Multi-tenant identity and audit | 4 weeks | Keycloak |
| Localisation beyond pt/en | ongoing | The `LegalFrame` abstraction is the seam |

---

### 3.13 Repository map

```
src/soma/
  geom.py                  ellipsoidal geometry, no geospatial stack
  scene.py                 the unit of observation; content hashing
  indices.py               spectral indices with citations
  providers/
    base.py                SceneProvider interface
    stac_sentinel2.py      CDSE / Earth Search — production
    synthetic.py           deterministic simulator
  detectors/
    base.py                Observation; three-state reliability
    footprint.py           disturbed-surface delineation
    water.py               pond extent, turbidity gradient, freeboard proxy
    change.py              Theil–Sen trend, guarded breakpoint, gaps
    deformation.py         InSAR velocity screen
    volume.py              DEM differencing with a two-term error model
  crosscheck/
    cadastre.py            inside / outside / indeterminate; registry notes
    declaration.py         intensity, cross-filing, audit priority
  evidence.py              manifest, canonical JSON, hash-chained ledger
  cases.py                 state machine with due process enforced
  dossier.py               the five translations; legal frames; guards
  render.py                evidence images and charts
  pipeline.py              end-to-end run for one site
  portfolio.py             the four-site demonstration
  dashboard.py             self-contained HTML build
  cli.py                   soma demo | ledger | case
tests/                     49 tests; run with pytest or tests/run_tests.py
```

## 4 Demonstration Transcript

Everything below was produced by running the delivered code on 19 August 2026 from a clean working directory. Nothing here is transcribed by hand: this section is generated by re-running each command and capturing its output.

### 4.1 The test suite

Runs with pytest, or with the bundled runner when pytest is not installed — which is
the situation in a locked-down government environment.

```
$ python3 tests/run_tests.py
  ok    test_geom.test_hemisphere_area
  ok    test_geom.test_point_in_concave_ring
  ok    test_geom.test_point_in_ring
  ok    test_geom.test_square_area_at_equator

49 passed, 0 failed
```

### 4.2 The four-site portfolio

```
$ PYTHONPATH=src python3 -c "from soma.portfolio import run_portfolio; run_portfolio()"

SITE         SEVERITY  STATE        DISTURBED   OUTSIDE    INDET   RATE NOW
BR-PA-0001   critical  contested       129.7h     36.6h     3.6h     4.65/mo
BR-MT-0002   critical  notified         76.9h     22.5h     5.7h     1.33/mo
BR-MG-0003   high      screened         67.8h      3.3h     2.3h     0.36/mo
BR-GO-0004   low       closed           58.5h      0.2h     0.2h     0.25/mo
```

#### What each site is

- **BR-PA-0001** — expansion accelerates from 0.70 to 4.65 ha/month, then crosses the
  licence boundary into a conservation unit. Declaration does not keep pace. The holder
  has answered on part of it, so the case sits at `contested`.
- **BR-MT-0002** — sustained extraction on nothing more than a pending application. A
  requerimento de pesquisa authorises no works at all.
- **BR-MG-0003** — title recorded as suspended, working surface still growing, nothing
  declared. Its tailings structure is creeping steadily but *not* accelerating, so the
  screen deliberately does not escalate it to critical.
- **BR-GO-0004** — entirely compliant. Raised by the routine screen, examined,
  **cleared**, and closed. It is the only one of the four whose case is publicly visible.

### 4.3 Recovery of the simulated ground truth

The simulator was configured with routine growth at about 0.7 ha/month stepping up to
about 4.5 ha/month in July 2025, with the working face crossing the licence boundary in
September 2025. Running blind on the resulting imagery:

```
quantity                                detected   simulated truth
------------------------------------------------------------------
disturbed surface, Jul 2026 (ha)           129.7             126.2
growth before the change (ha/mo)            0.70              0.71
growth after the change (ha/mo)             4.65              4.50
date of the rate change               2025-05-01        2025-07-01
impounded water, peak (ha)                  22.3              22.3
observations used / cloud-limited          25/18         43 months
```

Areas track truth to within a few per cent on fully observed dates. The rate change was
found and quantified correctly; its date was recovered two months early, which is an
honest characterisation of what a breakpoint fit on monthly composites can do, and is
reported as such rather than smoothed over.

### 4.4 The evidence ledger, and what happens when it is altered

```
$ PYTHONPATH=src python3 -m soma.cli ledger verify --root data/out/cases
{
  "entries": 4,
  "intact": true,
  "head": "9b709edf5694b13eed0b07222ace0ad7952b80c46fd2bee99f1671ce4ba5aed1",
  "problems": []
}
```

Now change one number in a past entry — 22.5 hectares outside the title becomes zero —
and re-verify:

```
{
  "entries": 4,
  "intact": false,
  "head": "9b709edf5694b13eed0b07222ace0ad7952b80c46fd2bee99f1671ce4ba5aed1",
  "problems": [
    "entry 1 (MNV-b4f8c05596c1d20b) hash mismatch: stored c76b54398c93f1c180487963867792c1a023e8e4a4ec2e73a606242ce564423e, recomputed 96538b9d9422e5f735b1d798e67ca7617f99665dd918dc1aecf2bc7b1520d740"
  ]
}
```

The finding cannot be quietly rewritten. That property is what lets an operator prove
the state's record has not been altered, and the state prove the same to a court.

### 4.5 Due process, enforced rather than promised

```
unnamed actor         -> every transition must name a responsible person and their role; automated adva
skipping notification -> cannot move a case from corroborated to substantiated. Permitted: ['notified',
review during window  -> the response window is open until 2026-09-18T05:10:40+00:00. A case cannot be 
publicly visible now  -> None
```

And the guard against issuing a legal act from simulated evidence:

```
administrative_notice -> refused: refusing to produce an administrative notice: the evidence chain c
judicial_dossier      -> refused: refusing to produce a judicial dossier: the evidence chain contain
technical_annex       -> permitted, with a SIMULATION banner
```

### 4.6 What is publishable, and when

```
CASE-2026-2A4FF177     publishable=True   58.5 hectares of mining disturbance mapped, all of it inside t
CASE-2026-5E1E5198     publishable=False  The holder has been notified and the response window is runnin
CASE-2026-9A84C406     publishable=False  The affected party has not yet been notified. Publishing befor
CASE-2026-B4F8C055     publishable=False  The holder has been notified and the response window is runnin
```

Only the cleared case is public. The other three are either pre-notification or notified
and unresolved, and publishing an unresolved allegation would impose the reputational
penalty before the procedure that is supposed to decide it.

## 5 Evidence Base

Working research notes. Every line carries a source. Verified during the research pass of 2026-08-19; re-verify before procurement, since licences and endpoints change.

### 5.1 The commercial stack (what operators already have)

- Global Mining Tech 50 (IMARC / Mines and Money, 2026): the top 50 mining-tech vendors sold
  ~US$6.8 bn of mining/metals technology in 2025; +73.5% over five years.
  <https://minesandmoney.com/news/industry/global-mining-tech-50-the-top-50-global-mining-metals-tech-players>
- Consolidation is accelerating and is *vertical* (equipment makers buying the software that
  plans the work their machines do):
  - Caterpillar acquired **RPMGlobal** (~US$728–735 m), completed February 2026.
    <https://www.caterpillar.com/en/news/corporate-press-releases/h/rpm-global-acquisition.html>
    <https://im-mining.com/2026/02/18/caterpillar-competes-rpmglobal-acquisition-expanding-data-driven-mining-technology-and-software-solutions-2/>
  - Weir acquired **Micromine** (~US$840 m; completed April 2025 — verified
    independently at <https://www.mining-technology.com/news/weir-micromine-acquisition/>;
    the IMARC write-up's ~US$800 m was the announced figure, not the completed one).
  - Sandvik owns **Deswik**. Bentley owns **Seequent** (Leapfrog, Evo).
  - **Constellation Software** has acquired 30+ mining software firms since 2011; flagship **Datamine**.
  - Epiroc has acquired 13 mining-tech firms since 2021.
  (all per the Global Mining Tech 50 write-up above)
- SourceForge "Mining software / Europe" listing (the user's link) — 30 products visible, which map
  onto these functional layers: EHSQ (Intelex, EHS Insight, SafetyIQ, PeopleTray, Pervidi),
  SCADA/IIoT (FrameworX), stakeholder & grievance management (Borealis), process chemistry
  (HSC Chemistry / Metso), surfaces & geostatistics (Surfer, RockWorks, LogPlot8), environmental
  data management (EnviroDataVault/RPMGlobal, Envirosuite), inspection (Inspectivity, Dashpivot),
  EO access (EarthCache/SkyWatch), mine design (MineCycle/Bentley, Promine), AI on 3-D data
  (Strayos), metallurgical accounting (INVENTEO/Caspeo, AMIRA P754), tenure & permits (trueMINER),
  digital twins (MineTwin), drill & blast (MineExcellence BIMS), geotechnics (Rocscience),
  drone volumetrics (Propeller), short-interval control (ShiftManager/RPMGlobal),
  EAM (4site), automation glue (Lightship).
  <https://sourceforge.net/software/mining/europe/>
  → NOTE: this is a *self-declared capability list*. Treated in this project as the specification
    the public sector has to match, not as an endorsement.

### 5.2 The public-sector capability gap (Brazil, measured)

Brazilian Court of Audit (TCU), 2024 ruling on ANM (Agência Nacional de Mineração):
- ~R$ 16.4 bn of mining revenue not collected over eight years; R$ 12.4 bn unrecovered 2014–2021;
  R$ 4 bn lost to time-barred credits 2017–2021; R$ 20 bn at risk of prescription.
- The CFEM enforcement team is **six staff plus one chief** for ~**12,000** CFEM collection files.
- ANM workforce fell **41.9%** from 1996; 695 employees over 2010–2023.
- Inspections collapsed **92%**: from 2,184 audits in 2014 to 173 in 2019.
- TCU ordered ANM to present, within 60 days, a plan for a collection-and-enforcement system.
  <https://agenciabrasil.ebc.com.br/geral/noticia/2024-10/tcu-cobra-anm-por-sonegacao-de-rs-16-bi-de-mineradoras-em-impostos>

ANM tailings-dam bulletin, October 2025 (published Nov 2025):
- **917** tailings dams registered in SIGBM; **470** fall under the PNSB (dam-safety policy) regime.
- Emergency level 3: **1**; level 2: **8**; level 1: **62**; alert status: **22** → **93** structures
  in declared alert or emergency.
- 1,241 dam inspections carried out in 2025 to that point.
  <https://www.gov.br/anm/pt-br/assuntos/barragens/boletim-de-barragens-de-mineracao/boletim-mensal-outubro-2025>

MapBiomas (Coleção 8 mining module, published 2023, reference year 2022):
- Total mined area in Brazil **443,000 ha**; garimpo **263,000 ha** (59%), industrial **180,000 ha** (41%).
- +35,000 ha added in 2022 alone.
- **92%** of mined area is in the Amazon biome.
- **>25,000 ha** inside Indigenous Lands; **>78,000 ha** inside Conservation Units — together 39%.
- Mining inside protected territories +190% over 2018–2022; on Indigenous Lands +265%.
- Five river basins hold 66% of national mining; Tapajós 20% (54,800 ha), Teles Pires 18% (48,100 ha).
  <https://brasil.mapbiomas.org/en/2023/09/22/amazonia-concentra-mais-de-90-do-garimpo-no-brasil/>
- Related MapBiomas finding: 77% of garimpo in the Amazon lies within 500 m of water [17].
  <https://brasil.mapbiomas.org/en/2024/04/19/77-do-garimpo-na-amazonia-esta-a-menos-de-500-metros-da-agua/>

### 5.3 Public data that already exists (the raw material)

#### Brazil — ANM open data (dados.gov.br, daily/real-time)
| Dataset | What it gives you |
|---|---|
| SIGMINE | polygons of every active/inactive mining process, SHP + KML, updated daily |
| Cadastro Mineiro | requests, titles, holders, regimes; daily micro-datasets |
| CFEM (Sistema de Arrecadação) | royalty payments — the declared-production proxy |
| SIGBM | tailings dams: technical characteristics, tailings type, real-time updates |
| TAH | annual per-hectare fee: process, year, holder, hectares, amount |
| AMB (Anuário Mineral Brasileiro) | production and destination (sales, transfers, consumption) since 2010 |
| SICOP | administrative process control |
| Dívida Ativa | unpaid credits registered for enforcement |
| DIPEM | declared exploration investment by municipality and substance |
| SOPLE | public offering / auction of available areas |
<https://www.gov.br/anm/pt-br/acesso-a-informacao/dados-abertos/bases-de-dados>
Bulk endpoints: <https://dadosabertos.anm.gov.br/SIGMINE/PROCESSOS_MINERARIOS/>
ArcGIS REST service: <https://geo.anm.gov.br/arcgis/rest/services/SIGMINE/dados_anm/MapServer>
Public tailings viewer: <https://sigbm.anm.gov.br/Publico>

#### Brazil — INPE
- DETER (near-real-time deforestation alerts) and PRODES (annual clear-cut), published through
  TerraBrasilis with open download and API. <https://terrabrasilis.dpi.inpe.br/en/data-access/>

#### Europe — Copernicus Data Space Ecosystem (CDSE)
Free-tier quotas for a "Copernicus General User" (this is the whole cost argument):
- Sentinel Hub APIs: 10,000 requests/month, 10,000 processing units/month, 300 PU/min cap, 300 req/min.
- openEO: 10,000 credits/month, 12 requests/min, 2 concurrent jobs.
- S3 / OData / STAC: **12 TB per rolling 30 days**, 2,000 req/min, 4 concurrent connections,
  20 MB/s per connection; over-quota degrades to 1 MB/s rather than cutting off.
- Direct HTTP COG access: 50,000 requests/month.
- Access tokens valid 10 minutes, refreshable within 60.
  <https://documentation.dataspace.copernicus.eu/Quotas.html>
APIs offered: OData, STAC, OpenSearch, Catalog Subscriptions, Sentinel Hub, openEO, S3,
Traceability API, On-Demand Production (CARD-BS, CARD-COH6/12).
  <https://documentation.dataspace.copernicus.eu/APIs.html>

#### Europe — European Ground Motion Service (EGMS)
- Sentinel-1 InSAR ground motion, **millimetre accuracy**, Europe-wide, **updated annually**,
  Basic / Calibrated / Ortho product levels, downloadable from the EGMS Explorer
  (only the two latest releases stay online). Explicitly aimed at authorities monitoring
  dams, bridges, railways and buildings, and at mining-induced subsidence.
  <https://land.copernicus.eu/en/products/european-ground-motion-service>
  <https://egms.land.copernicus.eu/>

#### Global datasets
- **Global-scale mining polygons v2** (Maus et al. 2022, *Scientific Data*), PANGAEA, CC BY.
  <https://doi.pangaea.de/10.1594/PANGAEA.942325> · <https://www.nature.com/articles/s41597-022-01547-4>
- **Open database on global coal and metal mine production** (Jasansky et al. 2023,
  *Scientific Data*): 1,171 mines, 80 materials (6 coal types, 21 ores, 12 concentrates, 19 metals),
  2000–2021, 80 countries (USA 233, Australia 213, Russia 100, South Africa 100, China 95,
  **Brazil 89**). Built by hand from >1,900 public company reports, every datum linked to its
  source document. GeoPackage + CSV on Zenodo under CC BY 4.0; R code on GitHub under GPL-3.
  Known gaps: China under-covered; copper coverage ~60–70%, gold ~30–40%; excludes artisanal
  mining and in-situ leaching. <https://www.nature.com/articles/s41597-023-01965-y>
  <https://doi.org/10.5281/zenodo.7369478>
- **Global Tailings Portal** (GRID-Arendal with the Investor Mining and Tailings Safety Initiative,
  co-chaired by the Church of England Pensions Board and the Swedish AP funds' Council on Ethics,
  UNEP-supported). ~1,800 tailings facilities from ~100 companies; 20 field categories including
  raising method, height, volume, hazard classification, stability history, downstream impact.
  Only 332 of 727 surveyed listed companies responded. Searchable online; bulk download by request.
  <https://tailing.grida.no/about>
- **Global Coal Mine Tracker** (Global Energy Monitor): database + wiki, validated against
  government sources, company reports, media, local NGOs and field contacts; methane estimated from
  production, gas content and emission coefficients; workforce estimated by ML where undisclosed;
  annual update cycle since 2023.
  <https://globalenergymonitor.org/projects/global-coal-mine-tracker/methodology/>

### 5.4 Public-interest monitoring that already works

- **Amazon Mining Watch** (Earth Genome / Earthrise Media, with Pulitzer Center and partners) —
  covers all nine Amazonian countries, aimed at journalists, activists, researchers, policymakers.
  <https://amazonminingwatch.org/en>
  Code: **MIT**; data products **CC BY 4.0**; bulk products on Source Cooperative.
  Model: ensemble of six CNNs over 48×48×13 Sentinel-2 L1C patches (~480 m per side), most ~800k
  parameters plus one ~100k model, scores averaged; multi-month median composites over the
  8.2 M km² basin. Venezuela geographic holdout: **99.4% specificity / 89.5% sensitivity**;
  combined evaluation **99.8% / 92.4%**. Scar masks derived with SAM2.
  <https://github.com/earthrise-media/mining-detector>
  <https://source.coop/earthgenome/amazon-mining-watch>
- **MAAP** (Monitoring of the Andean Amazon Project) — near-real-time gold-mining deforestation
  reporting. <https://www.maapprogram.org/amazon-gold-mining-2025/>
- **SkyTruth** — free, open-source tools; named projects Cerulean (oil), Mining (mountaintop
  removal), Flaring, 30x30 Tracker, Monitor. <https://skytruth.org/about/technology/>
- **Code for Africa — Africa Mining Watch** (partnership announcement).
- FOSS4G 2024 talk: "Leveraging AI and Open Source Geospatial Software to Combat Illegal Gold
  Mining in the Amazon". <https://talks.osgeo.org/foss4g-2024/talk/FX8X7S/>

### 5.5 Legal hooks

- **EU Open Data Directive**, Commission Implementing Regulation (EU) **2023/138**: six high-value
  dataset categories; "Geospatial" and "Earth observation and environment" are two of them.
  Obligation: free of charge, machine-readable, **API access and bulk download**, licensed
  **CC BY 4.0 or less restrictive**, metadata per Reg. (EC) 1205/2008, scales to 1:5000,
  current version plus history maintained. Compliance was due ~June 2024.
  <https://eur-lex.europa.eu/eli/reg_impl/2023/138/oj/eng>
  <https://datos.gob.es/en/blog/complying-europe-high-value-sites-earth-observation-and-environment-regulation>
- **Aarhus Convention** (access to environmental information, participation, access to justice) —
  the standing basis for a public-facing mining monitor in Europe.
  <https://environment.ec.europa.eu/law-and-governance/aarhus_en>
- **EITI Standard 2023** — systematic disclosure, open data policy, beneficial ownership and
  contract transparency. <https://eiti.org/sites/default/files/2023-06/2023%20EITI%20Standard.pdf>
  <https://eiti.org/documents/eiti-open-data-policy>
- **EU Accounting Directive, Chapter 10** — payments to governments reporting by extractive
  companies (the EU analogue of Canada's ESTMA).
- **Brazil**: Lei 14.066/2020 (new National Dam Safety Policy, post-Brumadinho, banning upstream
  dams and raising penalties); Lei 12.334/2010 (PNSB); Lei 12.527/2011 (Lei de Acesso à Informação).
- **QGIS** was recognised as a **Digital Public Good** by the Digital Public Goods Alliance in
  February 2025 — a precedent for classifying this platform as a DPG.
  <https://blog.qgis.org/2025/02/08/qgis-recognized-as-digital-public-good/>

### 5.6 Tooling caution
- **MinIO** community edition went into maintenance mode / was archived (late 2025 – 2026) after
  features were stripped from the AGPL build. Do **not** design a public-sector system around it.
  <https://stormdevelopments.ca/blog/minio-s-community-edition-is-archived-what-still-runs-in-2026/>
  <https://www.futuriom.com/articles/news/minio-faces-fallout-for-stripping-features-from-web-gui/2025/06>

### 5.7 Environment constraints observed in this build
- Outbound HTTP from the sandbox is proxy-restricted: package registries (PyPI, npm) and
  `git` to github.com work; arbitrary hosts (STAC endpoints, dadosabertos.anm.gov.br) do not.
- Consequence for the prototype: real provider code is written against the live APIs, and a
  deterministic synthetic provider lets the whole pipeline execute here end-to-end.

### 5.8 Sensor facts (verified 2026-08-19, needed for honest capability claims)

**Sentinel-1 (C-band SAR)**
- Sentinel-1D completed in-orbit commissioning and went live in 2026; user data opening 17 April 2026.
  Constellation now Sentinel-1A + 1C + 1D (Sentinel-1B failed and its mission ended August 2022).
  ESA is preparing Sentinel-1 Next Generation for continuity into the mid-2030s.
  <https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Sentinel-1D_goes_live_a_milestone_for_Europe_s_radar_mission>
  <https://dataspace.copernicus.eu/news/2026-4-16-sentinel-1d-user-data-opening-17042026>
- Radar: sees through cloud and at night. This is what makes tropical mining monitoring possible
  at all — optical alone loses the wet season.

**Sentinel-2 (optical MSI)**
- 13 spectral bands: four at 10 m, six at 20 m, three at 60 m. Swath 290 km.
- Revisit: 10 days with one satellite, 5 days with two, 2–3 days at mid-latitudes.
  Sentinel-2C launched 5 Sept 2024 and replaced 2A on 21 Jan 2025; 2A resumed on 13 Mar 2025 in an
  orbit 36° from 2B, giving a three-satellite constellation; the 2A extension campaign has been
  prolonged to the end of 2026.
- L1C (top-of-atmosphere) global from 2015; L2A (surface reflectance) is the analysis-ready product.
  <https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel2.html>
  <https://dataspace.copernicus.eu/news/2026-5-15-sentinel-2a-extension-campaign-prolonged-until-end-2026>

**Copernicus DEM**
- GLO-30 (30 m) and GLO-90 (90 m) global, ~149 M km²; EEA-10 (10 m) for 39 European countries.
- Absolute vertical accuracy <4 m (90% linear error); relative <2 m on slopes ≤20%, <4 m above.
- GLO-30/GLO-90 free worldwide; EEA-10 restricted to defined user categories. Cite
  <https://doi.org/10.5270/ESA-c5d3d65>. Access via Copernicus Browser, APIs, S3, OData.
  <https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM>
- Consequence: **free global elevation makes volumetric change estimation a public capability**,
  which is the closest open analogue to the drone-volumetrics products operators buy.

**RADD forest disturbance alerts**
- Wageningen University (Laboratory of Geo-Information Science and Remote Sensing), Sentinel-1 based,
  **10 m**, near-real-time, covering South America (13 countries), Central America (6), Africa (25),
  insular SE Asia (5), Pacific (1). **CC BY 4.0**. Cite Reiche et al. 2021, *Environ. Res. Lett.*,
  <https://doi.org/10.1088/1748-9326/abd0a8>. Distributed through Global Forest Watch.
  <https://gee-community-catalog.org/projects/radd/>

### 5.9 Evidence and admissibility

- Muhammad, Alif Nurfakhri. "The Admissibility of Earth Observation Data in Legal Proceedings:
  A Closer Look Towards Data Imaging." *Indonesia Law Review*, vol. 11, no. 1, 2021.
  Argument: the path from primary EO data to analysed information "requires a degree of
  manipulation", which is exactly where authenticity is contested. Proposes **data imaging and
  digital audit** as the mechanisms that preserve admissibility, and notes there is no settled
  international framework.
  <https://scholarhub.ui.ac.id/ilrev/vol11/iss1/2/>
- Design consequence for this platform: every derived product must carry its full derivation —
  source granule IDs, processing baseline, algorithm version, parameters, and a hash — or it is
  an opinion, not evidence. This is the single most important architectural requirement and the
  one most often missing from civic-tech monitoring tools.

### 5.10 Tooling-licence watch list (state as of 2026-08-19; re-verify before procurement)

Safe, well-governed, foundation-backed:
- QGIS — GPL-2.0-or-later; recognised as a Digital Public Good (Feb 2025).
- GDAL/OGR — MIT/X-style; OSGeo project.
- PostgreSQL (PostgreSQL Licence) + PostGIS (GPL-2.0-or-later).
- GeoServer (GPL-2.0), GeoNode (GPL-3.0), pygeoapi (MIT), CKAN (AGPL-3.0).
- STAC ecosystem: stac-spec, pystac, pystac-client, stac-fastapi, pgstac — Apache-2.0/MIT.
- Open Data Cube (Apache-2.0); openEO (Apache-2.0); eodag (Apache-2.0).
- rasterio (BSD-3), rioxarray (Apache-2.0), xarray (Apache-2.0), dask (BSD-3),
  scikit-image / scikit-learn (BSD-3), numpy (BSD-3).
- ESA SNAP (GPL-3.0); MintPy (GPL-3.0); LiCSBAS (GPL-3.0); ISCE2 (Apache-2.0);
  Orfeo ToolBox (Apache-2.0).
- TorchGeo (MIT), leafmap / segment-geospatial (MIT), TiTiler (MIT).
- MapLibre GL JS (BSD-3), deck.gl (MIT), Apache Airflow / Superset (Apache-2.0),
  DuckDB (MIT), Keycloak (Apache-2.0).

Do not build on without a second look:
- **MinIO** — community edition archived / maintenance mode after AGPL build was stripped of
  features (2025–2026). Use SeaweedFS (Apache-2.0), Garage (AGPL-3.0), Ceph RGW, or the sovereign
  cloud's own S3 service instead.
- Grafana (AGPL-3.0 since 2021) and Metabase OSS (AGPL-3.0) are fine to *run*, but AGPL has
  procurement implications if the institution modifies and exposes them as a service.
- Sen2Cor is free-to-use ESA software but is not an OSI-approved open-source licence — prefer
  consuming L2A products directly rather than depending on local Sen2Cor processing.

General trend context: source-available relicensing (BSL, SSPL, FSL) has continued to bite
infrastructure projects; a public-sector platform should pin to OSI-approved licences and keep an
exit path for every dependency.

## 6 GIS Prototype

### 6.1 What the map prototype adds

Everything above is a mirror, a translation layer, and a due-process machine. What it has
lacked, on paper, is a single surface where a case's geography and its cross-agency paper
trail sit side by side — where an inspector, a prosecutor or a journalist can click a site
and see not only where it is, but which registries already know about it, under which
number, and whether they agree with each other.

`map.html` is a working prototype of that surface, built over the same four
demonstration sites used throughout this document. It is delivered as a separate file rather
than folded into this report, for a specific technical reason: a live map needs to fetch map
tiles from a tile server over the network, and the sandboxed page this report itself is
published as cannot make that kind of request. Opened as its own file, the map has no such
restriction.

A note on the basemap itself: the prototype uses CARTO's free Positron/Dark Matter tiles
(built from OpenStreetMap data) rather than fetching directly from `tile.openstreetmap.org`.
OpenStreetMap's own tile servers are volunteer-run infrastructure with a usage policy that
blocks requests lacking a valid `Referer` header — which is exactly what a browser sends, or
fails to send, when a page is opened straight from disk (`file://`) rather than served over
`http(s)://`. Routing through CARTO's CDN, which does not enforce that check, keeps the map
usable however the file is opened, while the underlying map data is still OpenStreetMap's.

### 6.2 What is on the map

A CARTO base layer (light in a light browser theme, dark in a dark one), built from
OpenStreetMap data, the four sites plotted at their (synthetic) coordinates, each
with its licensed polygon, its detected disturbed-surface footprint, and — where relevant —
the protected-area polygon it overlaps. Clicking a site opens a panel with:

- The core geographic coordinates (WGS84 latitude/longitude, plus the UTM zone the pipeline
  actually computes in).
- The **cross-agency reference chain** — for a Brazilian site, this means, side by side: the
  ANM mining-process number (SIGMINE/Cadastro Mineiro), the IBAMA environmental-licensing
  process number where the activity requires federal licensing, the ICMBio conservation-unit
  reference where the site overlaps one, any open FUNAI matter where the footprint touches an
  Indigenous Land, the INCRA settlement (assentamento) reference where the site sits on or
  near an agrarian-reform settlement, and the ANA (water-resources) reference where a
  tailings structure is involved. Not every site has an entry in every registry — that
  absence is itself shown, not hidden, exactly as the rest of this architecture treats an
  observation gap as a finding rather than a null.
- The **evidence thread** — the same chain-of-custody the dossier layer already produces,
  shown as a short path from detection to registry: satellite scene → detector output →
  sealed `EvidenceManifest` (hash shown) → cadastral cross-check → the specific registry
  entries above → the case's current due-process state. This is the cybernetic point made
  concrete: each communication in the chain is shown, not asserted, so a reader can follow
  the thread to its source instead of taking the conclusion on faith.
- An **export** control that produces a CSV or GeoJSON containing, per site: the geographic
  coordinates, the case ID, and every cross-agency identifier above — so an interested party
  (a prosecutor's office, a journalist, an affected community's legal representative) can take
  the reference numbers and go query ANM, IBAMA, ICMBio, FUNAI, INCRA or ANA directly, rather
  than trusting a number this system asserts.

### 6.3 What is synthetic, and said so

Every registry number on the map is fabricated for the prototype — clearly marked as such, in
the same spirit as the rest of this project's refusal to let simulated evidence pass as real.
A production deployment replaces these with live lookups against each agency's own registry
(most of which — SIGMINE, the Cadastro Mineiro, SIGBM — are already catalogued in
`03-catalogues.xlsx`); IBAMA, ICMBio, FUNAI and INCRA do not yet have the same quality of
open, bulk-downloadable registries as ANM, which is itself a finding worth stating plainly:
the cross-agency reference chain is only as strong as the weakest registry in it, and today
that is not ANM.

## 7 References

Numbered in the order first cited, in ISO 690 numeric-reference format. Bracketed markers like **[1]** in §§2 and 5 above point here.

[1] CATERPILLAR INC. "Caterpillar Bolsters Mining Technology Solutions with RPMGlobal Acquisition." *Caterpillar Newsroom*, 2026. Available from: www.caterpillar.com/en/news/corporate-press-releases/h/rpm-global-acquisition.html. [Accessed: 19 Aug. 2026].

[2] COPERNICUS DATA SPACE ECOSYSTEM. "APIs." *Copernicus Data Space Ecosystem Documentation*. Available from: documentation.dataspace.copernicus.eu/APIs.html. [Accessed: 19 Aug. 2026].

[3] COPERNICUS DATA SPACE ECOSYSTEM. "Quotas and Limitations." *Copernicus Data Space Ecosystem Documentation*. Available from: documentation.dataspace.copernicus.eu/Quotas.html. [Accessed: 19 Aug. 2026].

[4] COPERNICUS DATA SPACE ECOSYSTEM. "Sentinel-2." *Copernicus Data Space Ecosystem Documentation*. Available from: documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel2.html. [Accessed: 19 Aug. 2026].

[5] COPERNICUS DATA SPACE ECOSYSTEM. "Sentinel-1D User Data Opening from 17/04/2026." *Copernicus Data Space Ecosystem*, 16 Apr. 2026. Available from: dataspace.copernicus.eu/news/2026-4-16-sentinel-1d-user-data-opening-17042026. [Accessed: 19 Aug. 2026].

[6] EARTHRISE MEDIA. *mining-detector*. GitHub. Available from: github.com/earthrise-media/mining-detector. [Accessed: 19 Aug. 2026].

[7] EARTH GENOME. *Amazon Mining Watch*. Available from: amazonminingwatch.org/en. [Accessed: 19 Aug. 2026].

[8] EUROPEAN COMMISSION. *Commission Implementing Regulation (EU) 2023/138 of 21 December 2022 Laying Down a List of Specific High-Value Datasets and the Arrangements for Their Publication and Re-use*. EUR-Lex. Available from: eur-lex.europa.eu/eli/reg_impl/2023/138/oj/eng. [Accessed: 19 Aug. 2026].

[9] EUROPEAN COMMISSION. "Aarhus Convention." *Environment*. Available from: environment.ec.europa.eu/law-and-governance/aarhus_en. [Accessed: 19 Aug. 2026].

[10] EUROPEAN ENVIRONMENT AGENCY. "European Ground Motion Service." *Copernicus Land Monitoring Service*. Available from: land.copernicus.eu/en/products/european-ground-motion-service. [Accessed: 19 Aug. 2026].

[11] EUROPEAN SPACE AGENCY. "Sentinel-1D Goes Live: A Milestone for Europe's Radar Mission." *ESA*, 2026. Available from: www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Sentinel-1D_goes_live_a_milestone_for_Europe_s_radar_mission. [Accessed: 19 Aug. 2026].

[12] EXTRACTIVE INDUSTRIES TRANSPARENCY INITIATIVE. *EITI Standard 2023*. EITI International Secretariat, 2023. Available from: eiti.org/sites/default/files/2023-06/2023%20EITI%20Standard.pdf. [Accessed: 19 Aug. 2026].

[13] GLOBAL ENERGY MONITOR. "Global Coal Mine Tracker: Methodology." Available from: globalenergymonitor.org/projects/global-coal-mine-tracker/methodology/. [Accessed: 19 Aug. 2026].

[14] GRID-ARENDAL. "About the Global Tailings Portal." *Global Tailings Portal*. Available from: tailing.grida.no/about. [Accessed: 19 Aug. 2026].

[15] JASANSKY, Simon, et al. "An Open Database on Global Coal and Metal Mine Production." *Scientific Data*, vol. 10, 2023. DOI: 10.1038/s41597-023-01965-y.

[16] MAPBIOMAS BRASIL. "Amazônia Concentra Mais de 90% do Garimpo no Brasil." 22 Sept. 2023. Available from: brasil.mapbiomas.org/en/2023/09/22/916-da-area-garimpada-no-brasil-ficam-no-bioma-amazonia/. [Accessed: 19 Aug. 2026].

[17] MAPBIOMAS BRASIL. "77% do Garimpo na Amazônia Está a Menos de 500 Metros da Água." 19 Apr. 2024. Available from: brasil.mapbiomas.org/en/2024/04/19/77-do-garimpo-na-amazonia-esta-a-menos-de-500-metros-da-agua/. [Accessed: 19 Aug. 2026].

[18] MAUS, Victor, et al. "An Update on Global Mining Land Use." *Scientific Data*, vol. 9, 2022. DOI: 10.1038/s41597-022-01547-4. Dataset: PANGAEA, DOI: 10.1594/PANGAEA.942325.

[19] MINES AND MONEY. "Global Mining Tech 50: The Top 50 Global Mining/Metals Tech Players." *IMARC*. Available from: minesandmoney.com/news/industry/global-mining-tech-50-the-top-50-global-mining-metals-tech-players. [Accessed: 19 Aug. 2026].

[20] MINING TECHNOLOGY. "Weir Completes Acquisition of Micromine." *Mining Technology*, 2025. Available from: www.mining-technology.com/news/weir-micromine-acquisition/. [Accessed: 19 Aug. 2026].

[21] MUHAMMAD, Alif Nurfakhri. "The Admissibility of Earth Observation Data in Legal Proceedings: A Closer Look Towards Data Imaging." *Indonesia Law Review*, vol. 11, no. 1, 2021. Available from: scholarhub.ui.ac.id/ilrev/vol11/iss1/2/. [Accessed: 19 Aug. 2026].

[22] QGIS PROJECT. "QGIS Recognized as Digital Public Good." *QGIS Blog*, 8 Feb. 2025. Available from: blog.qgis.org/2025/02/08/qgis-recognized-as-digital-public-good/. [Accessed: 19 Aug. 2026].

[23] REICHE, Johannes, et al. "Forest Disturbance Alerts for the Congo Basin Using Sentinel-1." *Environmental Research Letters*, vol. 16, no. 2, 2021. DOI: 10.1088/1748-9326/abd0a8.

[24] RIKIMARU, A., ROY, P. S., MIYATAKE, S. "Tropical Forest Cover Density Mapping." *Tropical Ecology*, vol. 43, no. 1, 2002, pp. 39-47.

[25] ROUSE, J. W., et al. "Monitoring Vegetation Systems in the Great Plains with ERTS." *Third ERTS Symposium*, NASA SP-351, 1974, pp. 309-317.

[26] SKYTRUTH. "Technology." Available from: skytruth.org/about/technology/. [Accessed: 19 Aug. 2026].

[27] SOURCEFORGE. "Mining Software in Europe." Available from: sourceforge.net/software/mining/europe/. [Accessed: 19 Aug. 2026].

[28] TRIBUNAL DE CONTAS DA UNIÃO. "TCU Cobra Agência de Mineração por Sonegação de R$ 16 bi em Impostos." Reported in *Agência Brasil*, 15 Oct. 2024. Available from: agenciabrasil.ebc.com.br/geral/noticia/2024-10/tcu-cobra-anm-por-sonegacao-de-rs-16-bi-de-mineradoras-em-impostos. [Accessed: 19 Aug. 2026].

[29] AGÊNCIA NACIONAL DE MINERAÇÃO. "Bases de Dados." *Dados Abertos*. Available from: www.gov.br/anm/pt-br/acesso-a-informacao/dados-abertos/bases-de-dados. [Accessed: 19 Aug. 2026].

[30] AGÊNCIA NACIONAL DE MINERAÇÃO. "Boletim Mensal de Barragens de Mineração — Outubro 2025." Available from: www.gov.br/anm/pt-br/assuntos/barragens/boletim-de-barragens-de-mineracao/boletim-mensal-outubro-2025. [Accessed: 19 Aug. 2026].

[31] XU, Hanqiu. "Modification of Normalised Difference Water Index (NDWI) to Enhance Open Water Features in Remotely Sensed Imagery." *International Journal of Remote Sensing*, vol. 27, no. 14, 2006, pp. 3025-3033.

---

*The Portuguese edition of this document follows below — full parity, same section numbers.*

---

# Observatório SOMA

**Uma análise do cenário, uma análise de assimetria, e um protótipo funcional de uma plataforma pública aberta**

Preparado para Bernardo Munayer · 19 de agosto de 2026 · edição em documento único

## 1 Sumário

Você perguntou três coisas: se eu tenho algum contato com os fornecedores de software de
mineração listados no SourceForge; se a necessidade do setor público de fiscalização
mineral pode ser atendida com dados públicos e software livre; e se seria possível
desenvolver um software que *comunique* essas necessidades adequadamente, em vez de apenas
detectar coisas.

**Não.** Não tenho relação, integração, parceria ou acesso privilegiado a nenhum fornecedor
citado neste documento — Deswik, Micromine, Datamine, Maptek, Hexagon, Seequent, RPMGlobal,
Envirosuite, Borealis ou qualquer outro. Tudo o que consta aqui sobre eles vem de seu próprio
material de marketing público e da imprensa setorial, o que se revela útil em vez de ser uma
limitação: uma lista pública de capacidades é uma especificação, e este relatório a trata
como tal (§2.2).

**Sim, e mais longe do que a maioria supõe — mas não de modo uniforme.** Parte do que um
operador enxerga pode ser espelhada a partir de dados públicos quase exatamente; parte pode
ser espelhada de forma aproximada e honesta, com margens de erro declaradas; parte não pode
ser espelhada de jeito nenhum. A seção 2.4 estabelece o que é o quê, camada por camada, e é o
núcleo analítico de todo o documento.

**Sim, e essa é a metade mais difícil do problema.** Um regulador não carece de imagens de
satélite — tudo o que se usa aqui já é gratuito e baixável hoje. O que falta ao setor público
é um aparato que converta o que as imagens mostram em comunicações que suas próprias
instituições consigam operar: uma ordem de fiscalização, uma notificação com fundamento legal
e prazo, um dossiê probatório que um juízo aceite, uma rubrica orçamentária que um parlamento
financie, uma página que uma comunidade consiga ler. A seção 2.8 sustenta que essa tradução
*é* o produto; a seção 2.9 descreve como ele foi construído; e praticamente tanto código foi
dedicado à camada de tradução (`dossier.py`) quanto aos próprios detectores.

A evidência mais clara da lacuna é brasileira, e é medida, não estimada: o Tribunal de Contas
da União (TCU) apurou R$ 16,4 bilhões em royalties minerários não arrecadados ao longo de
oito anos, uma equipe de seis pessoas contestando doze mil processos de cobrança,
fiscalizações em queda de 92% em cinco anos, e uma força de trabalho da agência reduzida em
41,9% desde 1996 — contra 443 mil hectares de área minerada mapeada, 92% dela na Amazônia
(§2.3). Nenhum aumento plausível de quadro fecha essa lacuna. Um satélite que revisita cada
ponto da Terra a cada poucos dias, de graça, talvez feche.

O **Observatório SOMA** é o protótipo construído em resposta. Uma frase governa todo o desenho: *todo número que o sistema exibe na tela deve
ser rederivável, por um terceiro, a partir de insumos públicos, usando apenas o manifesto que
o acompanha.* Tudo o mais — os detectores com suas travas, a tolerância cadastral aplicada em
favor do titular, a máquina de estados de devido processo, o livro-razão de evidências
encadeado por hash, a camada de tradução em cinco registros, a recusa em agir sobre evidência
simulada — decorre dessa única frase.

Exercitado às cegas contra um simulador determinístico com verdade de campo conhecida, o
protótipo recuperou a área antropizada com margem de poucos pontos percentuais, detectou e
quantificou corretamente uma mudança de taxa de crescimento de rotina para acelerada (0,70 →
4,65 ha/mês contra uma verdade simulada de 0,71 → 4,5), corretamente deixou de emitir um
alarme falso num sítio estável e regular, e corretamente manteve três dos quatro casos de
demonstração fora da visibilidade pública porque o devido processo ainda não havia se
completado — publicando apenas aquele que foi examinado e arquivado (§2.10; a §4 traz a
transcrição completa). Ele nunca viu uma imagem de satélite real; essa é a limitação mais
importante, e a §2.13 faz de prová-lo em imagem real o próximo passo, não o último.

**O que há neste documento.** Esta é a edição em documento único de tudo o que foi entregue,
com numeração decimal estrita — algarismos indo-arábicos em toda parte, sem numeração romana
— e um seletor de idioma: os botões **EN** / **PT** (códigos ISO 639-1) alternam este
documento inteiro, seção por seção, entre inglês e português do Brasil.

- **§2 — Relatório.** O argumento completo: a pilha do operador como especificação, a lacuna
  de capacidade medida, a tabela de assimetria, os patrimônios de dados públicos e de
  software livre, o argumento luhmanniano da tradução, a proposta do Observatório SOMA, os resultados do
  protótipo e seus limites honestos, os níveis de implantação e custo, as objeções levadas a
  sério, e os próximos passos.
- **§3 — Arquitetura Técnica.** A especificação de que um processo de licitação precisa:
  camada por camada, com o contrato de projeto, dependências, licenciamento e um mapa do
  repositório.
- **§4 — Transcrição da Demonstração.** Saída de comando verificada e reexecutada: a suíte de
  testes, a carteira de quatro sítios, a recuperação da verdade de campo, o livro-razão de
  evidências e o que ocorre quando ele é adulterado, a aplicação do devido processo, e a trava
  contra evidência simulada.
- **§5 — Base de Evidências.** As notas de pesquisa que sustentam cada afirmação factual do
  documento, organizadas por tema, cada linha carregando sua fonte.
- **§6 — Protótipo de SIG.** Onde e como os dados geoespaciais e os registros de múltiplos
  órgãos (ANM, IBAMA, ICMBio, FUNAI, INCRA, ANA) se encaixariam numa visão interativa, com
  exportação das coordenadas e dos identificadores de processo.
- **§7 — Referências.** Toda a bibliografia em formato numérico ISO 690, ligada às marcas de
  citação como **[1]** ao longo do texto acima.

Junto a este documento: `map.html` (o protótipo de SIG, com mapa OSM e exportação),
`dashboard.html` (o painel operacional — abra em qualquer navegador, sem necessidade
de rede), `soma/` (6.100 linhas de Python executável mais 720 linhas de testes,
compactadas), e `03-catalogues.xlsx` (toda fonte de dados públicos, componente de software
livre e jurisdição de que esta arquitetura depende, com licença, método de acesso e
maturidade).

O protótipo roda sobre imagens **simuladas**, deliberadamente, por razões que a §2.10.2
explica — mas nada neste pacote é uma afirmação sobre qualquer empresa ou sítio real, e o
software se recusa, por desenho, a emitir um ato legal a partir de evidência simulada.

## 2 Relatório

### 2.1 A pergunta, reformulada

"Vigilância de mineração" é uma expressão infeliz num documento que será lido por advogados,
de modo que a substituo por uma mais precisa.

Uma operação de mineração é uma assimetria informacional com um buraco no chão acoplado. O
operador sabe, de forma contínua e com precisão de poucos centímetros, onde está a frente de
lavra, quanto material moveu no último turno, quanta água há atrás de sua barragem de
rejeitos, quanto a crista avançou neste mês, e o que declarará ao Estado ao fim do trimestre.
O Estado sabe o que o operador lhe diz, quando lhe diz, na forma que o operador escolhe. A
comunidade afetada sabe o que consegue ver da estrada.

Todas as falhas graves de governança mineral da última década cabem dentro dessa lacuna.
Brumadinho foi uma barragem cuja declaração de condição de estabilidade estava assinada. A
sub-arrecadação de royalties é uma diferença entre produção declarada e produção efetiva. A
extração ilegal em terra indígena é extração que o Estado não observou. A lacuna não é uma
falha de política pública; é uma falha *observacional* com consequências de política
pública.

Logo, a pergunta não é "como vigiamos as mineradoras". É:

> **Pode uma autoridade pública obter, a partir de dados aos quais já tem direito, um
> retrato independente de uma operação de mineração bom o bastante para agir — e pode esse
> retrato ser produzido em uma forma que tanto as próprias instituições do Estado quanto o
> direito de defesa do operador consigam suportar?**

Este relatório sustenta que sim, delimita exatamente até onde alcança esse "bom o bastante",
e entrega um protótipo funcional dessa resposta.

---

### 2.2 O que faz a pilha de software do operador

#### 2.2.1 A lista que você enviou é uma especificação

A listagem do SourceForge para software de mineração na Europa mostra trinta produtos [27].
Organizados pelo que efetivamente fazem, e não pelo fornecedor, eles cobrem doze camadas
funcionais:

| Camada | Produtos representativos na página |
|---|---|
| Titularidade, licenças e gestão fundiária | trueMINER; (e, fora da página, acQuire, Landfolio) |
| Modelagem geológica e visualização de subsuperfície | RockWorks, LogPlot8, Surfer |
| Projeto, planejamento e sequenciamento de lavra | MineCycle (Bentley), Promine, Reactore/MineOne |
| Controle de curto prazo e execução | ShiftManager (RPMGlobal), Lightship |
| Perfuração e desmonte | Blast Management System (MineExcellence) |
| Geotecnia e estabilidade de taludes | Rocscience |
| Levantamento, volumetria e avanço | Propeller (drone), Strayos (IA 3D) |
| Química de processo e contabilidade metalúrgica | HSC Chemistry (Metso), INVENTEO (Caspeo, AMIRA P754) |
| Dados e monitoramento ambiental | Envirosuite, EnviroDataVault (RPMGlobal) |
| SSMA, inspeções e força de trabalho | Intelex, EHS Insight, SafetyIQ, PeopleTray, Pervidi, Inspectivity, Dashpivot |
| Engajamento de partes interessadas e ouvidoria | Borealis |
| Gestão e controle de ativos empresariais | 4site, FrameworX, MineTwin, EarthCache |

Duas coisas merecem ser notadas. Primeiro, trata-se de um aparato completo de
*autobservação*: um operador que roda toda essa pilha sabe mais sobre o próprio sítio do que
qualquer regulador poderia aprender visitando-o. Segundo, várias dessas camadas existem
precisamente porque o operador deve prestar contas ao Estado — a gestão de dados ambientais,
o módulo de ouvidoria, a contabilidade metalúrgica segundo um código reconhecido. **Os
instrumentos dos quais o Estado depende para fiscalizar o setor são, em sua maior parte, de
propriedade, operação e manutenção do próprio setor.** Isso não é uma acusação de má-fé; é
uma descrição estrutural, e é exatamente o assunto deste projeto.

#### 2.2.2 O mercado ao redor disso

O Global Mining Tech 50 estima a receita de tecnologia para mineração e metais em 2025,
entre os cinquenta maiores fornecedores, em cerca de **US$ 6,8 bilhões**, um crescimento de
**73,5%** em cinco anos [19]. A consolidação é vertical e recente:

- A Caterpillar adquiriu a **RPMGlobal** por cerca de **US$ 728–735 milhões**, com fechamento
  em fevereiro de 2026 [1].
- A Weir adquiriu a **Micromine** por cerca de **US$ 840 milhões**, com fechamento em abril
  de 2025 [20].
- A Sandvik é dona da **Deswik**; a Bentley é dona da **Seequent** (Leapfrog, Evo).
- A **Constellation Software** comprou mais de trinta empresas de software de mineração
  desde 2011; seu principal ativo é a **Datamine**.
- A **Epiroc** adquiriu treze empresas de tecnologia para mineração desde 2021.

Fabricantes de equipamentos estão comprando o software que planeja o trabalho que suas
máquinas executam. A consequência prática para um regulador é que a camada de planejamento,
a camada de execução e a camada de relato passam a residir, cada vez mais, dentro de uma
única relação comercial, e as interfaces entre elas não são públicas.

#### 2.2.3 Quanto custaria a um órgão público igualar isso por meio de compras

Nada neste relatório exige uma estimativa de valores de licenciamento, porque o argumento não
depende disso. Basta observar que um regulador nacional de mineração, num país de renda
média, não vai contratar uma pilha Deswik-e-Envirosuite para cada sítio que supervisiona e
que, mesmo que o fizesse, estaria comprando as próprias ferramentas do operador, aplicadas a
dados que o próprio operador fornece. O espelho precisa ser construído com outra coisa.

---

### 2.3 O que o setor público de fato tem

Os números brasileiros são a evidência publicada mais clara, em qualquer lugar, dessa lacuna
de capacidade, porque o Tribunal de Contas da União a mediu.

Do acórdão do TCU de 2024 sobre a Agência Nacional de Mineração [28]:

- Aproximadamente **R$ 16,4 bilhões** em receita mineral não foram arrecadados ao longo de
  oito anos: R$ 12,4 bi não recuperados entre 2014 e 2021, R$ 4 bi perdidos por prescrição
  entre 2017 e 2021, e **R$ 20 bi em risco de prescrição**.
- A equipe responsável por contestar a arrecadação de royalties da CFEM é de **seis
  servidores e um chefe**, para aproximadamente **12.000** processos de cobrança.
- A força de trabalho da agência caiu **41,9%** em relação ao nível de 1996, chegando a 695
  servidores no período de 2010–2023.
- As fiscalizações caíram **92%**: de **2.184 auditorias em 2014 para 173 em 2019**.
- O TCU determinou que a ANM apresentasse, em sessenta dias, um plano para um sistema de
  arrecadação e fiscalização.

Em contraste com isso: o registro de barragens de rejeitos da ANM (SIGBM) continha **917
barragens** [30] em novembro de 2025, das quais **470** estão sujeitas à PNSB, com **93
estruturas** em alerta ou emergência declarada (1 em nível 3, 8 em nível 2, 62 em nível 1, 22
em alerta). E o MapBiomas apurou que a superfície minerada do Brasil chegou a **443.000
hectares** [16] em 2022 — 263.000 ha de garimpo artesanal —, dos quais **92%** estão no bioma
Amazônia, com mais de 25.000 ha dentro de Terras Indígenas e 78.000 ha dentro de unidades de
conservação. A mineração dentro de territórios protegidos cresceu **190%** entre 2018 e
2022; dentro de Terras Indígenas, **265%**.

A aritmética é o argumento inteiro. Cento e setenta fiscalizações por ano, diante de dezenas
de milhares de títulos, centenas de barragens e 443.000 hectares de solo revolvido, não é um
regime de fiscalização. É um erro amostral. Nenhum aumento plausível de quadro de pessoal
fecha essa lacuna; um satélite que revisita cada ponto da Terra a cada poucos dias, de graça,
talvez feche.

Isso não é uma peculiaridade brasileira, ainda que o Brasil a tenha medido com mais
honestidade do que a maioria. Qualquer jurisdição em que o número de sítios supervisionados
exceda em muito o número de pessoas que os supervisionam tem a mesma estrutura, e isso vale
para quase todas elas.

---

### 2.4 A assimetria, camada por camada

Este é o núcleo analítico do relatório: o que um operador enxerga, o que um órgão público
consegue enxergar a partir de dados públicos e — dito sem rodeios — o que não consegue.

| # | Capacidade do operador | Exemplos de fornecedores | Espelho público | Dados públicos por trás | Fidelidade |
|---|---|---|---|---|---|
| 1 | Gestão de titularidade e licenças | trueMINER, acQuire | **Motor cadastral** — registro de polígonos, detecção de sobreposição com áreas protegidas, linha do tempo do status do título | SIGMINE (diário, SHP+KML); registros dos Estados-membros da UE sob o regime de conjuntos de dados de alto valor | **Total.** O registro *é* a cópia pública. |
| 2 | Levantamento da superfície lavrada | Estação total, fotogrametria por drone | **Delineamento da área antropizada** — mapeamento da superfície perturbada a 10 m, a cada 5 dias | Sentinel-2 L2A; Landsat 8/9 para a linha de base pré-2015 | **Alta** para extensão; o operador vence em precisão, o público vence em frequência e histórico |
| 3 | Volumetria e avanço | Propeller, Strayos | **Diferenciação de MDE** — corte/aterro e tonelagem implícita, com incerteza explícita | Copernicus DEM GLO-30 (gratuito, <4 m de acurácia vertical absoluta); NASADEM/SRTM para uma linha de base de 2000; MDS fotogramétricos nacionais | **Moderada.** Ordem de grandeza, intervalos largos. Útil como limite superior, nunca como número de produção. |
| 4 | Geotecnia e monitoramento de barragens | Rocscience, cristas instrumentadas | **Triagem de deslocamento por InSAR** — movimento em linha de visada e aceleração, na escala de mm | EGMS (Europa, anual, gratuito); Sentinel-1 processado internamente via ISCE2/SNAP + MintPy/LiCSBAS em outros lugares | **Alta para movimento, nenhuma para causa.** Detecta que uma crista está se movendo; não consegue dizer por quê nem prever ruptura. |
| 5 | Rejeitos e gestão de água | RPMGlobal, Envirosuite | **Extensão da bacia, gradiente de turbidez, proxy de borda livre** | Sentinel-2; JRC Global Surface Water; SIGBM e o Global Tailings Portal para o registro | **Moderada.** Apenas comportamento superficial. |
| 6 | Monitoramento ambiental | Envirosuite, EnviroDataVault | **Triagem de impacto** — perda de vegetação, alertas de desmatamento, proxies de poeira e pluma | RADD (Sentinel-1, 10 m, quase em tempo real, CC BY); DETER/PRODES; Sentinel-5P para SO₂/NO₂ | **Moderada a alta** para cobertura do solo; **baixa** para concentrações ambientais sem estações terrestres. |
| 7 | Contabilidade metalúrgica | INVENTEO (AMIRA P754) | **Triagem de declarações** — produção declarada por hectare ativo, comparada com pares; consistência entre declarações distintas | CFEM; Anuário Mineral Brasileiro; relatórios do EITI; Diretiva Contábil da UE, Cap. 10; ESTMA | **Baixa como medição, alta como triagem.** Não é possível calcular a tonelagem deles. É possível classificar quem vale a pena auditar. |
| 8 | Gestão de partes interessadas e ouvidoria | Borealis | **Canal público de recebimento de denúncias**, com obrigação de resposta publicada | Construído, não emprestado (ao estilo ODK/Kobo) | **Total**, e possivelmente melhor: o registro não fica em poder da parte reclamada. |
| 9 | Gestão de incidentes de SSMA | Intelex, EHS Insight | **Registro público de incidentes**, cruzado com registros do regulador e da imprensa | Boletins de agências, dados da inspeção do trabalho, imprensa | **Parcial.** Depende inteiramente do regime de divulgação. |
| 10 | Planejamento de lavra, sequenciamento, modelagem de reservas | Deswik, Vulcan, Datamine, Leapfrog | **Nenhum** | — | **Não espelhável.** Exige o banco de dados de sondagens. |
| 11 | Gestão e despacho de frota | Modular, Wenco, Cat MineStar | **Nenhum** | — | **Não espelhável, e nem deveria ser.** |
| 12 | Controle de processo / SCADA | FrameworX | **Nenhum** | — | **Não espelhável.** |

Três observações sobre esta tabela.

**O setor público vence no tempo, não na precisão.** O levantamento do operador é
centimétrico e mensal; o espelho público é métrico e a cada cinco dias, com arquivo contínuo
desde 2015 (Sentinel-2) ou 1984 (Landsat). Para as perguntas que um regulador de fato faz —
*a área saiu do limite; quando a taxa mudou; a crista está acelerando* —, frequência e
histórico vencem precisão.

**As linhas 10 a 12 não são uma lacuna a ser fechada.** Um regulador não precisa modelar o
corpo de minério nem despachar caminhões, e construir nessa direção seria tanto inútil
quanto uma intromissão legítima. Ser explícito quanto a isso é o que torna o restante
crível. Uma proposta que alega espelhar tudo é descartada; uma que diz "exatamente estas
quatro coisas, e não estas três" é lida com atenção.

**A linha 7 é onde as pessoas erram.** A tentação é converter a área observada em toneladas
e comparar isso com a produção declarada. Não faça isso. A conversão exige relação
estéril/minério, teor do minério, umidade, manejo de rejeitos e movimentação de pilhas —
nada disso é público —, e uma exigência construída sobre essa cadeia não sobrevive ao
contraditório. O que sobrevive é o raciocínio relativo: intensidade comparada a pares,
consistência entre as próprias declarações do operador, e o caso limpo de atividade visível
sem absolutamente nada declarado.

---

### 2.5 O patrimônio de dados públicos

Tudo nesta seção é gratuito, licenciado para reutilização e está disponível hoje.

#### 2.5.1 Observação da Terra

**Sentinel-1 (radar em banda C).** O Sentinel-1D concluiu sua fase de comissionamento [5, 11] e teve
os dados abertos aos usuários em 17 de abril de 2026, levando a constelação a 1A + 1C + 1D
(o 1B havia falhado em 2022). O radar enxerga através de nuvens e à noite — o fato isolado
que torna possível, sequer, o monitoramento de mineração em clima tropical, já que sensores
ópticos perdem toda a estação chuvosa.

**Sentinel-2 (óptico).** Treze bandas — quatro a 10 m, seis a 20 m, três a 60 m — em uma
faixa de imageamento de 290 km. A revisita é de 10 dias com um satélite, de 5 com dois, e de
2–3 dias em latitudes médias; uma configuração com três satélites está em operação desde
março de 2025, com a campanha de extensão do 2A agora prorrogada até o fim de 2026. A
reflectância de superfície L2A é o produto pronto para análise; o arquivo remonta a 2015.

**Copernicus DEM.** O GLO-30 (30 m) e o GLO-90, de cobertura global, gratuitos em todo o
mundo, com acurácia vertical absoluta melhor que 4 m (erro linear a 90%) e acurácia relativa
inferior a 2 m em declives de até 20%. O EEA-10 (10 m) cobre 39 países europeus, sob acesso
restrito. É isso que torna a estimativa volumétrica sequer uma capacidade pública possível.

**European Ground Motion Service.** Interferometria Sentinel-1 em toda a Europa, com
precisão milimétrica, atualização anual, em níveis Basic / Calibrated / Ortho, disponível
para download no EGMS Explorer [10]. Ele existe explicitamente para autoridades que monitoram
barragens e infraestrutura, e para subsidência induzida por mineração. Para uma implantação
europeia, a camada tecnicamente mais difícil de toda esta arquitetura chega pronta, em forma
de tabela.

**Landsat 8/9.** A linha de base anterior ao Sentinel, remontando a 1984 em todo o arquivo —
indispensável para estabelecer como era um sítio antes que alguém estivesse observando.

#### 2.5.2 O custo de tudo isso

As cotas gratuitas do Copernicus Data Space Ecosystem [3], conforme publicadas, para um usuário
comum registrado:

- **12 TB a cada 30 dias corridos** via S3/OData/STAC, a 2.000 requisições por minuto e até
  20 MB/s por conexão, em quatro conexões simultâneas. Exceder a cota degrada a taxa de
  transferência para 1 MB/s, em vez de cortar o acesso.
- **50.000 requisições diretas a COG por mês**; **10.000 requisições à API do Sentinel Hub**
  e **10.000 unidades de processamento** por mês; **10.000 créditos openEO** por mês.

Doze terabytes por mês não é uma restrição para um programa nacional de monitoramento de
mineração — é, repetidamente, aproximadamente todo o arquivo Sentinel-2 sobre uma grande
província mineral. **O custo de dados para monitorar toda mina de um país é zero.** O custo é
computação, armazenamento e — de longe, o principal — as pessoas que leem os resultados e
decidem o que fazer.

#### 2.5.3 Registros e cadastro

**Brasil.** A ANM publica, por meio do dados.gov.br e de seus próprios endpoints de dados
abertos: o SIGMINE (polígonos de todo processo minerário ativo e inativo, em shapefile e
KML, diariamente); o Cadastro Mineiro (requerimentos, títulos, titulares, regimes, em
microdados diários); dados de arrecadação da CFEM; o SIGBM (barragens de rejeitos, com
características técnicas e tipo de rejeito, em tempo real); a TAH (taxa anual por hectare,
por processo, ano, titular e área); o Anuário Mineral Brasileiro (produção e destinação
desde 2010); o SICOP; o cadastro de dívida ativa; o DIPEM; e o SOPLE. Os arquivos em lote
ficam em `dadosabertos.anm.gov.br`, com um serviço ArcGIS REST em `geo.anm.gov.br`.

Essa combinação é incomumente forte. Polígonos de títulos somados a pagamentos de royalties,
somados ao registro de barragens, somado ao anuário de produção — tudo público e tudo
legível por máquina — é exatamente o conjunto de insumos de que esta arquitetura precisa.

**União Europeia.** O Regulamento de Execução (UE) 2023/138 da Comissão designa seis
categorias de conjuntos de dados de alto valor, das quais duas — **Geoespacial** e
**Observação da Terra e meio ambiente** — cobrem o material relevante. Os Estados-membros
devem publicá-los gratuitamente, em formato legível por máquina, **com API e download em
lote**, sob licença **CC BY 4.0 ou menos restritiva**, com metadados conforme o Regulamento
(CE) 1205/2008, em escalas de até 1:5000, e devem manter tanto versões atuais quanto
históricas. A conformidade era devida por volta de meados de 2024.

Isso importa mais do que parece à primeira vista. A UE já legislou o lado da oferta desta
arquitetura. Um Estado-membro que implementou o regime de conjuntos de dados de alto valor
já provisionou, sem ter essa intenção, os insumos cadastrais e ambientais de que um monitor
público de mineração precisa.

#### 2.5.4 Dinheiro

- **CFEM** (Brasil) — pagamentos de royalties por processo: o proxy da produção declarada.
- **Diretiva Contábil da UE, Capítulo 10** — pagamentos a governos por empresas extrativas.
- **ESTMA** (Canadá) e regimes equivalentes em outros países.
- **Padrão EITI 2023** [12] — divulgação sistemática, uma política explícita de dados abertos, e
  requisitos reforçados de transparência quanto a beneficiários finais e contratos.

A verificação mais produtiva disponível não precisa de satélite algum: comparar o que uma
mesma empresa declarou, para o mesmo sítio e período, a três regimes diferentes. Divergências
entre as próprias declarações de um operador são o sinal mais forte e mais barato de toda
esta arquitetura.

#### 2.5.5 Meio ambiente

- **Alertas RADD de perturbação florestal** — da Universidade de Wageningen, baseados em
  Sentinel-1, a **10 m**, quase em tempo real, cobrindo 13 países da América do Sul, 6 da
  América Central, 25 da África, 5 insulares do Sudeste Asiático e 1 do Pacífico, sob
  licença **CC BY 4.0** [23].
- **DETER e PRODES** (INPE) — desmatamento quase em tempo real e anual para o Brasil, com
  download aberto e uma API por meio do TerraBrasilis.
- **MapBiomas** — série anual de cobertura e uso do solo, incluindo um módulo dedicado a
  mineração e garimpo, com atribuição de substância.
- **Sentinel-5P** — colunas de SO₂ e NO₂, úteis para fundição e processamento, com resolução
  grosseira demais para uma única cava.

#### 2.5.6 Conjuntos de dados de referência

- **Global-scale mining polygons v2** (Maus et al. 2022): **44.929 polígonos**, **101.583
  km²**, **145 países**, digitalizados a partir de mosaicos Sentinel-2 sem nuvens de 2019, em
  buffers de 10 km ao redor de 34.820 localizações de minas conhecidas. Acurácia geral de
  88,3%, acurácia do usuário de 97,2%, acurácia do produtor de 78,9%, F1 de 0,87. Licença CC
  BY-SA 4.0, no PANGAEA [18].
- **Open database on global coal and metal mine production** (Jasansky et al. 2023):
  **1.171 minas**, **80 materiais**, 2000–2021, 80 países (Brasil: 89 instalações),
  construído manualmente a partir de mais de 1.900 relatórios públicos de empresas, com cada
  dado vinculado ao seu documento-fonte. Licença CC BY 4.0 no Zenodo; código R sob GPL-3.
  Limitações conhecidas: cobertura insuficiente da China; cobertura de cobre de 60–70%, de
  ouro de 30–40%; exclui mineração artesanal e lixiviação in situ [15].
- **Global Tailings Portal** (GRID-Arendal em conjunto com a Investor Mining and Tailings
  Safety Initiative): cerca de **1.800 instalações** de aproximadamente **100 empresas**, com
  vinte categorias de campos, incluindo método de alteamento, altura, volume, classificação
  de risco e impacto a jusante. Apenas **332 das 727** empresas de capital aberto consultadas
  responderam — o que já é, em si, um achado sobre o regime de divulgação [14].
- **Global Coal Mine Tracker** [13] (Global Energy Monitor): banco de dados somado a wiki,
  validado com base em fontes governamentais, relatórios de empresas, imprensa, ONGs locais
  e contatos de campo; ciclo de atualização anual desde 2023.

---

### 2.6 O patrimônio de código aberto

#### 2.6.1 O que existe, e é bom

A pilha geoespacial de código aberto é madura, governada por fundações e está em uso de
produção por agências nacionais. O QGIS foi reconhecido como **Bem Público Digital** [22] pela
Digital Public Goods Alliance em fevereiro de 2025 — um precedente útil para a classificação
da plataforma proposta aqui.

| Função | Componente | Licença |
|---|---|---|
| SIG de desktop | QGIS | GPL-2.0-or-later |
| E/S e reprojeção de raster/vetor | GDAL/OGR | MIT/X-style |
| Banco de dados espacial | PostgreSQL + PostGIS | PostgreSQL Licence + GPL-2.0-or-later |
| Catálogo de imagens | especificação STAC, pystac, pystac-client, stac-fastapi, pgstac | Apache-2.0 / MIT |
| Cubos de dados e processamento | Open Data Cube; openEO | Apache-2.0 |
| Acesso a arquivo | eodag; clientes OData/STAC/S3 do CDSE | Apache-2.0 |
| Processamento de arrays | numpy, xarray, dask, rasterio, rioxarray | BSD-3 / Apache-2.0 |
| Análise de imagem e aprendizado de máquina | scikit-image, scikit-learn, TorchGeo, segment-geospatial | BSD-3 / MIT |
| SAR e InSAR | ESA SNAP; ISCE2; MintPy; LiCSBAS; Orfeo ToolBox | GPL-3.0 / Apache-2.0 |
| Tiles e serviços | TiTiler, GeoServer, pygeoapi | MIT / GPL-2.0 |
| Portal e catálogo | GeoNode, CKAN | GPL-3.0 / AGPL-3.0 |
| Mapas web | MapLibre GL JS, deck.gl, leafmap | BSD-3 / MIT |
| Orquestração | Apache Airflow, Prefect | Apache-2.0 |
| Analytics | DuckDB, GeoParquet, Apache Superset | MIT / Apache-2.0 |
| Identidade | Keycloak | Apache-2.0 |

#### 2.6.2 O que não existe em código aberto

Não existe equivalente crível em código aberto para o Deswik, o Vulcan, o Surpac, o Datamine
ou o Leapfrog. O GemPy é um excelente modelador geológico implícito de código aberto, e o
pygslib cobre geoestatística, mas nenhum dos dois é um sistema de planejamento de lavra, e a
lacuna em sequenciamento, relato de reservas e contabilidade metalúrgica é total.

**Isso não importa para o espelho público**, porque são as linhas 10–12 da tabela de
assimetria: capacidades de que um regulador não precisa. Importa enormemente se alguém
propuser uma alternativa de código aberto para *operadores*, o que é um projeto diferente e
muito mais difícil. Manter os dois separados é importante; confundi-los é o jeito mais
rápido de perder uma plateia de engenheiros.

#### 2.6.3 Uma ressalva sobre licenciamento

**A edição comunitária do MinIO entrou em modo de manutenção e foi arquivada ao longo de
2025–2026**, depois que funcionalidades foram retiradas da versão sob AGPL. Qualquer
arquitetura que tenha pressuposto o MinIO como sua camada S3 agora tem um problema. Use o
SeaweedFS (Apache-2.0), o Garage (AGPL-3.0), o Ceph RGW, ou o próprio armazenamento de
objetos da nuvem soberana.

A lição geral é de política de contratação, não de escolha de tecnologia: fixar-se a
licenças aprovadas pela OSI, manter uma rota de saída documentada para cada dependência, e
reverificar as licenças a cada ciclo de contratação. Relicenciamentos do tipo
"source-available" continuam pegando projetos de infraestrutura de surpresa, e um órgão
público que descobre isso depois de já ter implantado o sistema tem um problema muito pior
do que um que se planejou para isso.

---

### 2.7 O que já existe no interesse público — e por que não basta

Sistemas reais, funcionais e críveis já fazem partes disso.

**Amazon Mining Watch** [7, 6] (Earth Genome / Earthrise Media, com o Pulitzer Center) cobre os
nove países amazônicos. Seu detector é um ensemble de seis redes convolucionais sobre
patches Sentinel-2 de 48×48×13 — cerca de 480 m de lado —, a maioria com em torno de 800 mil
parâmetros, mais um modelo menor, com média entre eles; ele roda sobre composições medianas
multimensais em toda a bacia de 8,2 milhões de km². Num holdout geográfico da Venezuela,
reporta **99,4% de especificidade e 89,5% de sensibilidade**; a avaliação combinada dá
99,8%/92,4%. As máscaras de cicatriz são derivadas com o SAM2. O código é **MIT**, os
produtos de dados são **CC BY 4.0**, e as saídas em lote estão no Source Cooperative.

O **MAAP** publica análises quase em tempo real de desmatamento por garimpo de ouro para a
Amazônia andina. O **SkyTruth** constrói ferramentas gratuitas e abertas, incluindo um
rastreador de mineração de topo de montanha. O **MapBiomas** produz a série anual
brasileira. O **Global Energy Monitor** e o **Global Tailings Portal** mantêm os registros de
instalações. O **Code for Africa** iniciou um Africa Mining Watch.

Este é um trabalho excelente, e a arquitetura proposta aqui deve consumir seus produtos em
vez de duplicá-los — o detector do Amazon Mining Watch é melhor do que o baseado em regras do
protótipo, e a seção 9 diz isso explicitamente.

Mas nenhum deles produz um **ato administrável**. Eles produzem mapas, conjuntos de dados e
jornalismo. O que não produzem — porque não é sua função — é um registro que um servidor
possa assinar, que indique fundamento legal, que abra um prazo de manifestação para a parte
afetada, que registre o que essa parte disse, e que um juízo possa aceitar. A distância entre
"um modelo de IA deu a este pixel a pontuação 0,87" e "o titular do título 830.123/2018 fica
notificado de que foram observados 36,6 hectares de perturbação fora de seu polígono, entre
estas datas, com base nesta evidência, e tem trinta dias para se manifestar" é a distância
inteira entre tecnologia cívica e administração pública.

Essa distância é a lacuna que este projeto endereça.

---

### 2.8 O verdadeiro problema de projeto: tradução entre sistemas

Você trabalha com Luhmann, de modo que formularei o argumento nesses termos, porque isso não
é decoração — foi o que determinou a arquitetura.

Uma detecção por satélite é uma comunicação no registro do sensoriamento remoto. Ela é
*destituída de sentido* para o sistema jurídico, que processa comunicações pelo código
binário lícito/ilícito; para o sistema administrativo, que as processa como competência,
procedimento e ato; para o sistema político, que as processa como orçamento e mandato; e
para a esfera pública, que as processa como dano e responsabilidade. Uma grandeza que não
consegue atravessar essas fronteiras permanece dentro do sistema técnico e não muda nada.
Esse é o destino observado de uma enorme quantidade de monitoramento ambiental muito
bem-feito: a ciência está correta, os pixels estão certos, e nada acontece, porque o achado
nunca se tornou uma comunicação que qualquer outro sistema pudesse operar.

O meio ambiente "irrita" o sistema jurídico; não fala com ele. O que fala com ele é uma
comunicação devidamente formada. Logo, o requisito do produto não é a *detecção*. É o
**acoplamento estrutural**: um aparato que toma uma irritação ambiental e produz, a partir
dela, comunicações que cada sistema receptor consiga processar pelo seu próprio código.

Concretamente, o mesmo achado selado precisa ser renderizado de cinco maneiras — não cinco
resumos dele, cinco *traduções*, cada uma carregando o achado inteiro para uma forma que o
sistema receptor consiga operar, e cada uma explícita quanto ao que não está afirmando:

| Registro | Artefato | O que precisa carregar | O que precisa recusar |
|---|---|---|---|
| Técnico | **Anexo técnico** | Todo insumo, versão de algoritmo, parâmetro, hash; uma receita de reprodução | Conclusões de direito |
| Administrativo | **Notificação de fatos observados** | Fato, norma aplicável, prazo de manifestação, como contestar, onde obter os dados brutos | Qualquer juízo de infração — isso é reservado ao servidor que assina |
| Jurídico | **Dossiê probatório** | Cadeia de custódia, a distinção entre dado primário e derivado, limitações declaradas, histórico processual | Dolo, autoria, ou a existência de infração |
| Político | **Informe de supervisão** | Sítios observados por servidor, casos levantados, casos arquivados, qual seria a cobertura contrafactual | Hectares como manchete |
| Público | **Ficha do sítio** | O quê, onde, quanto, em linguagem simples; se o operador já se manifestou | Qualquer insinuação de que uma detecção é uma condenação |

É por isso que "um software que comunique essas necessidades adequadamente" é a maneira
correta de ter formulado o pedido, e por isso o protótipo dedica tanto código a
`dossier.py` quanto aos detectores.

Uma consequência merece destaque, porque é aí que a maioria das plataformas de monitoramento
fracassa politicamente. **O operador também é um sistema receptor.** A notificação é dirigida
a ele; ele precisa poder responder; sua resposta precisa entrar no mesmo registro, com as
mesmas garantias; e, se a resposta resolver a questão, o caso precisa ser encerrado
*visivelmente*. Uma plataforma que só acusa produz um fluxo de alegações infalsificáveis, e
em um único ciclo orçamentário ninguém no governo a defenderá.

---

### 2.9 Observatório SOMA: a proposta

#### 2.9.1 O contrato epistêmico

Uma frase governa todo o projeto:

> **Todo número que o sistema exibe em tela precisa ser rederivável, por um terceiro, a
> partir de insumos públicos, usando apenas o manifesto que o acompanha.**

Isso é testável, e é testado. É também o que separa o instrumento de um regulador de uma
caixa-preta: um operador que não consegue reproduzir um achado não consegue contestá-lo de
forma significativa, e um achado que não pode ser contestado de forma significativa não
sobrevive ao controle judicial.

Consequências que decorrem diretamente disso: nenhuma imagem proprietária no caminho
probatório; nenhum algoritmo sem versionamento; nenhum parâmetro não documentado; nenhum
modelo cujos dados de treinamento não possam ser divulgados no caminho crítico para um ato
coercitivo.

#### 2.9.2 As oito perguntas

O sistema existe para responder a oito perguntas, e se recusa a responder a outras:

1. Há extração onde não existe título algum?
2. A extração está fora do polígono do título que a autoriza?
3. A extração está dentro de uma área onde é categoricamente proibida?
4. Um título registrado como inativo, suspenso ou apenas requerido está mostrando atividade?
5. A taxa de expansão está mudando, e quando mudou?
6. Uma estrutura de rejeitos está se movendo, e está acelerando?
7. A lâmina d'água represada está se aproximando dos limites de sua bacia de contenção?
8. O que foi declarado é consistente com o que é visível, e com as demais declarações do
   próprio operador?

#### 2.9.3 Detectores, e por que uma regra vence uma rede neural aqui

O detector de área antropizada no protótipo é uma regra espectral publicada — NDVI abaixo de
0,30 [25], MNDWI abaixo de 0,10 [31], BSI acima de 0,00 [24], reflectância SWIR-1 acima de 0,12, com limpeza
morfológica e unidade mínima de mapeamento de 0,5 ha — e não uma rede convolucional. Uma
rede seria mais acurada. Três razões pelas quais a regra é o padrão e a rede é o
aprimoramento:

1. **Ela pode ser escrita dentro de uma decisão.** Aquela frase com os limiares pode entrar
   em um ato administrativo e ser contestada no mérito. "O ensemble deu pontuação 0,87" não
   pode.
2. **Ela não tem problema de proveniência do conjunto de treinamento.** Um modelo aprendido
   importa os vieses de onde quer que seus rótulos tenham vindo, e, quando usado para
   justificar uma ação coercitiva contra uma parte identificada, essa proveniência se torna
   objeto de descoberta processual.
3. **Ela se degrada de forma legível.** Quando falha, dá para ver qual termo falhou.

A arquitetura correta é as duas coisas: a regra como a linha de base responsabilizável, um
modelo (o do Amazon Mining Watch é o candidato óbvio — licenciado sob MIT, já validado) como
reforço de revocação, cujas detecções *extras* são triadas por um humano antes de entrarem
em um caso. Nunca o modelo sozinho no caminho até um ato.

#### 2.9.4 Devido processo como máquina de estados

Os casos avançam por: `observed → screened → corroborated → notified → contested → reviewed
→ substantiated | dismissed | referred → closed`.

As transições são impostas em código, não em política:

- **Nenhuma transição sem um servidor nomeado e cargo.** O avanço automático levanta uma
  exceção. O software não faz um caso avançar.
- **Nenhuma notificação a partir de um caso não corroborado.** Uma detecção de sensor único
  não é base suficiente para um ato coercitivo, de modo que a máquina de estados não permite
  uma.
- **Nenhuma revisão enquanto o prazo de manifestação estiver aberto.** O caso não pode
  prosseguir até que a parte notificada tenha tido a chance de se manifestar ou o prazo
  tenha expirado.
- **Nada é publicado antes da notificação**, e um caso que foi notificado mas ainda não
  resolvido é visível ao notificado e a mais ninguém. Publicar uma alegação não resolvida
  impõe a sanção reputacional antes do procedimento que deveria decidi-la.
- **O arquivamento publica um resumo.** Ser inocentado é um fato público.

Isso é devido processo administrativo ordinário — CF/88, art. 5º, LIV e LV; Lei 9.784/1999;
art. 41 da Carta de Direitos Fundamentais da UE — expresso como máquina de estados para que
o software não consiga pular etapas. Na carteira de quatro sítios do protótipo, o único caso
publicamente visível é o que foi *arquivado*. Esse é o comportamento correto, e ele surpreende
as pessoas, o que é exatamente o motivo pelo qual vale a pena demonstrá-lo.

#### 2.9.5 Evidência e o livro-razão

Todo achado carrega um `EvidenceManifest`: insumos (identificados, com fonte, com data e
hora, com hash), algoritmos (nomeados e versionados), cada parâmetro, saídas (com hash),
premissas declaradas e limitações declaradas. O próprio manifesto é canonicalizado e recebe
um hash, sendo anexado a um livro-razão JSONL encadeado por hash, no qual cada registro
carrega o hash de seu predecessor. Apagar ou editar qualquer achado passado invalida, de
forma detectável, todos os achados posteriores.

Isso é uma cadeia de hashes, não uma blockchain: sem consenso, sem tokens, sem nada
distribuído. A administração pública não precisa de confiança distribuída; precisa de um
registro pelo qual possa ser responsabilizada. Onde se queiram garantias mais fortes, a
cabeça do livro-razão pode receber carimbo de tempo conforme a RFC 3161, ou ser publicada
periodicamente em diário oficial — que é como a prática notarial resolve isso há um século.

A literatura acadêmica relevante é escassa, mas certeira: a análise de Muhammad [21] sobre a
admissibilidade de dados de observação da Terra identifica exatamente a vulnerabilidade aqui
endereçada — que o caminho do dado primário até a informação analisada "requer certo grau de
manipulação", e que é precisamente aí que a autenticidade é contestada. Os remédios que ele
propõe, o imageamento de dados (data imaging) e a auditoria digital, são o que o manifesto e
o livro-razão implementam.

#### 2.9.6 O que o sistema se recusa a fazer

Formuladas como restrições de projeto, porque as recusas de um sistema são mais informativas
do que suas funcionalidades:

- Não prevê ruptura de barragem de rejeitos. Reporta que uma crista está se movendo mais
  rápido do que antes e recomenda uma vistoria de engenharia.
- Não calcula tonelagem a partir de uma área e não apura royalties devidos. Classifica
  sítios para auditoria e diz por quê.
- Não reporta turbidez como contaminação. Aciona uma campanha de amostragem.
- Não computa contra um titular a área dentro da tolerância de fronteira.
- Não emite notificação administrativa nem dossiê judicial a partir de evidência simulada —
  isso é imposto por uma trava, com um teste por trás dela.
- Não trata ausência de observação como ausência de atividade. Lacunas de observação são
  reportadas como achados por direito próprio.

---

### 2.10 O protótipo, e o que ele mostrou

#### 2.10.1 O que foi construído

Cerca de 6.100 linhas de Python, com mais 720 de testes: geometria sobre o elipsoide, sem
dependência de pilha geoespacial; um modelo de cena com validade por pixel; um provedor STAC
real, escrito contra o Copernicus Data Space Ecosystem e o Earth Search da Element 84; um
simulador determinístico; cinco detectores (área antropizada, água, mudança, deformação,
volume); cruzamentos cadastral e de declarações; o manifesto de evidência e o livro-razão; a
máquina de estados dos casos; o gerador de dossiês nos cinco registros; renderização de
gráficos e imagens de evidência; uma CLI; e **49 testes, todos passando**.

O núcleo **não tem dependências geoespaciais obrigatórias**. numpy é exigido; scipy e
scikit-image são usados quando presentes. GDAL, rasterio, shapely e pyproj são aceleradores
opcionais. Uma secretaria municipal de meio ambiente, com um único notebook e sem orçamento
de compras, consegue rodar a biblioteca de detecção. Isso foi um objetivo de projeto, não um
acaso.

#### 2.10.2 Por que a demonstração roda sobre imagens simuladas

O sandbox em que isso foi construído não tem acesso de rede de saída aos endpoints STAC, de
modo que o pipeline não pôde ser apontado para dados do Copernicus ao vivo. Em vez de
entregar pseudocódigo, a interface do provedor foi dividida: um `StacSentinel2Provider` real,
escrito contra as APIs ao vivo, e um `SyntheticProvider` que gera reflectância Sentinel-2
L2A fisicamente plausível para um sítio simulado — incluindo uma cava em crescimento, uma
bacia de rejeitos, estradas de acesso, um rio, nebulosidade sazonal com perda na estação
chuvosa, e um MDE pareado.

Isso acabou por valer a pena manter de qualquer forma, por três razões que uma agência
adotante vai reconhecer: os detectores podem ser testados por regressão contra uma verdade
de campo conhecida, de modo que uma mudança de limiar que custe 3 ha de revocação aparece na
integração contínua; uma agência pode observar o sistema encontrar algo cuja resposta ela já
conhece, antes de confiar nele para algo que não conhece; e o pipeline inteiro é
demonstrável sem rede alguma, numa promotoria ou numa sala de audiência.

#### 2.10.3 Resultados

O simulador foi configurado com uma verdade conhecida: expansão de rotina a cerca de **0,7 ha
por mês**, saltando para cerca de **4,5 ha por mês** em julho de 2025, com a frente de lavra
cruzando o limite da licença em setembro de 2025, rumo a uma unidade de conservação vizinha.

Rodando às cegas sobre as imagens resultantes, o pipeline reportou:

| Grandeza | Detectado | Verdade simulada |
|---|---|---|
| Área antropizada, jul/2026 | 129,7 ha | 126,2 ha |
| Taxa de crescimento antes da mudança | 0,70 ha/mês | ~0,71 ha/mês |
| Taxa de crescimento depois da mudança | 4,65 ha/mês | ~4,5 ha/mês |
| Data da mudança de taxa | mai/2025 | jul/2025 |
| Fora do polígono do título | 36,6 ha | (por construção, pós-set/2025) |
| Dentro da unidade de conservação | 30,6 ha | (por construção) |
| Água represada, pico | 22,3 ha | 22,3 ha |

As áreas acompanham a verdade com margem de poucos pontos percentuais nas datas totalmente
observadas. A mudança de taxa foi encontrada e quantificada corretamente; sua *data* foi
recuperada com dois meses de antecipação, o que é uma caracterização honesta do que um
ajuste de ponto de ruptura sobre composições mensais consegue fazer, e é reportado como tal,
em vez de ser dissimulado.

Igualmente importante é o que o sistema **não** reportou. Dos quatro sítios da carteira de
demonstração, um estava inteiramente conforme. Foi levantado pela triagem de rotina,
examinado, e **arquivado** — e é o único dos quatro cujo caso está publicamente visível,
porque os outros três estão, ou antes da notificação, ou notificados e não resolvidos. Um
sítio estável não recebeu um alerta espúrio de "mudança de taxa"; isso exigiu acrescentar
uma trava que exige que as duas inclinações de segmento sejam estatisticamente separadas,
sem a qual sítios tranquilos reportavam mudanças de regime toda vez que uma série curta e
desfalcada por nuvens oscilava. Essa trava tem um teste de regressão, porque um sistema que
grita "lobo" sobre mudanças de taxa deixa de ser lido dentro de um mês.

#### 2.10.4 Limites honestos do protótipo

- Imagem simulada não é imagem real. Cenas reais têm sombra de relevo, neblina, artefatos de
  sensor, solo agrícola exposto que parece espectralmente com uma mina, e cicatrizes de
  queimada. A taxa de falsos positivos em dados reais é desconhecida e precisa ser medida
  antes da implantação.
- Os limiares são padrões para clima tropical úmido. Precisam ser calibrados contra verdade
  de campo local para qualquer outro contexto.
- O módulo de InSAR consome séries temporais de deslocamento; não processa interferogramas.
  Para a Europa, o EGMS os fornece. Em outros lugares, é preciso montar a cadeia ISCE2/SNAP +
  MintPy, e isso é trabalho de verdade.
- O módulo volumétrico foi exercitado sobre um par de MDE sintéticos, com uma escavação
  conhecida. Em MDEs reais, o erro sistemático de coregistro domina — o modelo de erro
  reflete isso, mas nenhum modelo de erro consegue removê-lo; isso exige coregistro sobre
  terreno estável.

---

### 2.11 Implantando

#### 2.11.1 Três níveis

**Nível 1 — um município ou uma promotoria.** Um analista, um notebook, o QGIS, a biblioteca
de detecção, imagens obtidas da camada gratuita do Copernicus para um punhado de sítios.
Roda offline. Produz anexos e notificações para casos que alguém já está trabalhando. A
implantação leva semanas, não anos, e custa o tempo do analista.

**Nível 2 — um órgão ambiental estadual.** Um servidor modesto, PostGIS, Airflow, um catálogo
STAC, de vinte a algumas centenas de sítios em cadência mensal, um portal público sob o
regime de acesso à informação. Um ou dois servidores técnicos, somados aos fiscais que já
existem.

**Nível 3 — um regulador nacional.** Cobertura cadastral completa, triagem sistemática de
todo título ativo, o registro de barragens de rejeitos conectado a um serviço de deformação,
integração com o sistema de royalties, dados abertos publicados, uma API. É aqui que a
constatação do TCU recebe resposta: não recontratando os 41,9% do quadro da ANM que se
perdeu, mas garantindo que as 173 fiscalizações por ano que de fato ocorrem sejam
direcionadas aos 173 sítios certos.

#### 2.11.2 Custo

Dados: **zero**, dentro de cotas que não são restritivas nessa escala. Software: **zero** em
termos de licenciamento, com todos os componentes sob licenças da OSI. Computação e
armazenamento: modestos — este é um trabalho embaraçosamente paralelizável sobre imagens de
10 m em áreas pequenas, e um servidor de porte médio dá conta de um programa nacional.

O custo real é de pessoas, e não é pequeno: analistas para triar, servidores técnicos para
corroborar, autoridades para assinar, advogados para redigir, e a vontade institucional de
agir sobre o que sai do sistema. Qualquer proposta que apresente isso como uma compra de
tecnologia, em vez de um programa de capacitação institucional, está distorcendo a questão.

#### 2.11.3 Soberania e o caminho do bem público digital

A plataforma deveria ser desenvolvida como um **bem público digital**: licença aprovada pela
OSI, padrões abertos (STAC, OGC API, GeoParquet, COG), nenhum aprisionamento a fornecedor,
implantável em infraestrutura nacional ou isolada de rede. O reconhecimento do QGIS pela
Digital Public Goods Alliance em fevereiro de 2025 é o precedente, e o DPG Standard é a
lista de verificação.

A razão não é ideológica. O sistema de monitoramento de um regulador de mineração que roda
sobre uma plataforma comercial estrangeira é um sistema de monitoramento cuja continuidade
depende de uma relação comercial que o regulador não controla, num setor em que as partes
reguladas têm porte suficiente para ter interesse nisso. Soberania, aqui, é controle de
risco.

---

### 2.12 Objeções, levadas a sério

**"Isto é vigilância."** É a observação de atividade industrial em terra sob título público,
a partir de dados que qualquer pessoa pode baixar, de sítios cujas coordenadas já estão
publicadas no cadastro. Não é observação de pessoas. O projeto exclui deliberadamente
qualquer coisa na resolução em que indivíduos se tornam identificáveis, e trabalha com
imagens públicas de 10 m, em vez de imagens comerciais submétricas. A palavra na sua
mensagem original é a palavra certa para a função e a palavra errada para a política;
"supervisão" ou "verificação" chegarão mais longe.

**"A evidência de satélite não vai se sustentar."** Às vezes não vai mesmo, e a resposta
honesta é projetar o sistema para isso, em vez de negá-lo. O manifesto, a fixação de
versões, o registro de parâmetros, a cadeia de hashes e a receita de reprodução existem
porque a vulnerabilidade é real e está identificada na literatura. Note-se também que as
saídas do sistema, em sua maioria, *não* são oferecidas como prova de uma infração: são
oferecidas como base para uma notificação que abre um procedimento. Essa é uma exigência
muito mais baixa, e muito mais defensável.

**"O órgão não consegue agir sobre mais alertas do que os que já ignora."** Esta é a
objeção mais forte, e é a razão pela qual a classificação por gravidade e o caminho do
arquivamento fazem parte do projeto. O valor do sistema no Nível 3 não é mais alertas; é *o
mesmo número de fiscalizações, mas melhor direcionadas*. Um informe de supervisão que
reporta sítios por fiscal e casos arquivados, em vez de hectares detectados, é redigido
exatamente para responder a este argumento.

**"Os operadores vão burlar o sistema."** Alguns vão. Trabalhando sob nuvem, revegetando
rapidamente, dispondo material para parecer uma pilha de estoque. O radar neutraliza o
primeiro; o arquivo neutraliza o segundo; a diferenciação de MDE limita o terceiro. Mais
relevante ainda: burlar um detector público é caro e detectável, e os operadores mais
propensos a tentar são justamente aqueles cujo comportamento mais se quer tornar caro.

**"Vai ser usado politicamente."** Sim — qualquer instrumento de supervisão pode ser. As
mitigações são estruturais, não retóricas: regras de publicação que impedem que uma
alegação não resolvida seja veiculada; um caminho de arquivamento que é público; uma cadeia
de evidência que torna detectável a exclusão seletiva; e saídas que qualquer pessoa pode
reproduzir, de modo que um achado politicamente motivado possa ser verificado pelo outro
lado.

**"Falsos positivos vão destruir sua credibilidade."** Correto, e este é o risco
operacional que mais importa. Daí a unidade mínima de mapeamento, a tolerância de fronteira
aplicada em favor do titular, a exigência de corroboração antes de qualquer notificação, a
trava de inclinações separadas sobre mudanças de taxa, e o tratamento do arquivamento como
uma métrica de qualidade, e não como um fracasso. Um sistema de triagem com taxa de
arquivamento zero não está triando; está apenas confirmando o que já se acreditava.

**"Isto duplica o MapBiomas / o Amazon Mining Watch / o sistema próprio do órgão."** O
sistema os consome, em vez de duplicá-los. O que nenhum deles fornece é a camada
administrativa e probatória, e é essa a entrega.

---

### 2.13 O que eu faria a seguir

**Meses 0–3 — provar em imagem real.** Apontar o provedor STAC para o Copernicus Data Space
Ecosystem. Tomar vinte sítios brasileiros com desfecho conhecido — idealmente com processos
já em curso na ANM ou no MPF, de modo que exista verdade de campo — e medir precisão e
revocação em dados reais. Publicar a matriz de confusão. Este é o passo que valida ou mata o
projeto, e deve vir primeiro.

**Meses 3–6 — calibrar e robustecer.** Limiares locais. Acrescentar o modelo do Amazon
Mining Watch como segunda opinião. Ligar a ingestão de SIGMINE, CFEM e SIGBM aos endpoints
reais. Montar a cadeia ISCE2/MintPy para uma estrutura de rejeitos e compará-la com qualquer
registro instrumentado existente.

**Meses 6–9 — colocar diante de uma instituição.** Não uma implantação-piloto: um único caso
real, trabalhado de ponta a ponta com um servidor real, passando por notificação e resposta,
até um desfecho real. Tudo o que importa aprender, aprende-se ali.

**Meses 9–12 — publicar.** Código sob licença OSI, submetido ao registro de Bens Públicos
Digitais. Artigo de metodologia. Um endpoint de dados abertos para os achados que sejam
legalmente publicáveis. Em seguida, procurar uma segunda jurisdição, porque é a segunda
implantação que prova que se trata de uma plataforma, e não de um projeto isolado.

**Uma observação sobre por onde começar institucionalmente.** Não comece pelo regulador de
mineração. Comece pelo tribunal de contas ou pelo Ministério Público — um órgão cujo mandato
é o controle, e não o fomento setorial, que já dispõe de poder de requisição de informação, e
que já identificou publicamente a lacuna de capacidade. O TCU fez exatamente isso, por
escrito. Um instrumento que responde a uma constatação que a própria instituição já fez
sobre si mesma tem um caminho muito mais fácil do que um que chega como crítica externa.

---

## 3 Arquitetura Técnica

**Verificação de Extração Mineral e Responsabilização Regulatória.** Um espelho aberto da pilha de software do operador de mineração, para o setor público. Versão 0.1.0 · especificação companheira do §2.

### 3.1 Design contract

Tudo o que segue decorre de um único compromisso:

> Todo número que o sistema exibir em uma tela deve ser rederivável, por um terceiro, a partir
> de insumos públicos, usando apenas o manifesto que o acompanha.

Seis consequências, cada uma delas uma restrição rígida, não uma preferência:

| Restrição | Porque |
|---|---|
| Nenhuma imagem proprietária no caminho probatório | Um achado que a parte afetada não consegue reproduzir não pode ser contestado de forma significativa |
| Todo algoritmo versionado; mudança de comportamento exige incremento de versão | Do contrário, achados passados são silenciosamente invalidados — o equivalente geoespacial de perder a cadeia de custódia |
| Todo parâmetro registrado no manifesto, não em um arquivo de configuração qualquer | Um limiar que não está no registro é um limiar que ninguém pode contestar |
| Nenhum modelo cujos dados de treinamento não possam ser divulgados no caminho para um ato coercitivo | A proveniência do conjunto de treinamento torna-se exigível no momento em que a saída justifica ação contra uma parte nomeada |
| Nenhuma transição sem um ser humano nomeado | O software não decide; os servidores decidem |
| Lacunas de observação são achados, não nulos | "Não conseguimos ver" e "nada aconteceu" são afirmações diferentes e jamais podem ser colapsadas em uma só |

---

### 3.2 Camadas

```
┌──────────────────────────────────────────────────────────────────────────┐
│  8  AUDIT           append-only hash-chained ledger · replay recipes     │
├──────────────────────────────────────────────────────────────────────────┤
│  7  PUBLICATION     OGC API Features/Tiles/Records · open-data export    │
│                     public portal · notification channels                │
├──────────────────────────────────────────────────────────────────────────┤
│  6  TRANSLATION     technical annex · administrative notice ·            │
│                     judicial dossier · oversight brief · public card     │
├──────────────────────────────────────────────────────────────────────────┤
│  5  CASE            state machine with due process enforced in code      │
├──────────────────────────────────────────────────────────────────────────┤
│  4  RECONCILIATION  cadastre · restricted areas · declarations · filings │
├──────────────────────────────────────────────────────────────────────────┤
│  3  OBSERVATION     footprint · water · change · deformation · volume    │
├──────────────────────────────────────────────────────────────────────────┤
│  2  STORE           PostGIS · object store (COG) · STAC · GeoParquet     │
├──────────────────────────────────────────────────────────────────────────┤
│  1  ACQUISITION     STAC providers · registry connectors · InSAR feeds   │
├──────────────────────────────────────────────────────────────────────────┤
│  0  PLATFORM        sovereign infrastructure · OSI-licensed throughout   │
└──────────────────────────────────────────────────────────────────────────┘
```

As camadas 1, 3, 4, 5, 6 e 8 estão implementadas no protótipo. As camadas 2 e 7 são
especificadas aqui e são convencionais; não há nada de inovador nelas, e nada de difícil.

---

### 3.3 Camada 1 — aquisição

#### 3.3.1 Provedores de imagens

Um provedor transforma *(geometria do sítio, intervalo de datas)* em uma lista de objetos
`Scene`. A interface é deliberadamente estreita, de modo que uma implantação nacional possa
acrescentar seu próprio arquivo — o CBERS-4A no Brasil, uma estação de recepção regional na
África — sem tocar em nenhum detector.

```python
class SceneProvider(ABC):
    def search(self, site_id, aoi, start, end, grid=None, max_cloud=0.6) -> List[Scene]: ...
```

Duas implementações são entregues:

**`StacSentinel2Provider`** — produção. Escrita contra:

| Catálogo | Raiz | Coleção | Autenticação |
|---|---|---|---|
| Copernicus Data Space Ecosystem | `https://catalogue.dataspace.copernicus.eu/stac` | `SENTINEL-2` | sim |
| Element 84 Earth Search | `https://earth-search.aws.element84.com/v1` | `sentinel-2-l2a` | não |

Trata as duas convenções de chave de ativo (`blue`/`B02`, `swir16`/`B11`, `scl`/`SCL`), aplica
o **deslocamento L2A de −1000 para baseline de processamento ≥ 04.00** — errar isso desloca
todos os índices e é o erro mais comum em pipelines Sentinel-2 — e faz a triagem com a Scene
Classification Layer, rejeitando as classes 0, 1, 3, 8, 9 e 10.

Os compostos são **medianas** por pixel sobre os pixels válidos dentro de um mês-calendário.
Mediana, e não média: uma única borda de nuvem não detectada enviesa uma média e não move uma
mediana, e o objetivo de um composto mensal é sobreviver aos trópicos.

**`SyntheticProvider`** — simulação determinística para testes, aceitação e demonstração
isolada da rede (air-gapped). Gera refletância L2A plausível para uma paisagem com uma cava em
crescimento, uma barragem de rejeitos, pilhas de estéril, estradas de acesso, um rio, nuvens
sazonais com perda total ocasional na estação chuvosa, e um MDE pareado. Todo artefato que
produz é marcado como `provider="synthetic"`, e a camada de dossiê recusa-se a emitir um ato
legal a partir dele.

#### 3.3.2 Conectores de registro

| Fonte | Endpoint | Cadência |
|---|---|---|
| ANM SIGMINE (polígonos de títulos) | `dadosabertos.anm.gov.br/SIGMINE/PROCESSOS_MINERARIOS/`; ArcGIS REST em `geo.anm.gov.br` | diária |
| ANM Cadastro Mineiro, CFEM, SIGBM, TAH, AMB, SICOP, Dívida Ativa, DIPEM, SOPLE | dados.gov.br | diária a tempo real |
| Áreas protegidas | CNUC, FUNAI, WDPA | conforme publicado |
| Cadastros de Estados-membros da UE | endpoints nacionais de HVD sob o Reg. (UE) 2023/138 — API e em lote, CC BY 4.0 | por Estado-membro |
| Movimento do solo EGMS | `egms.land.copernicus.eu` | anual |
| Alertas RADD | Global Forest Watch / Wageningen | quase em tempo real |
| DETER / PRODES | TerraBrasilis | quase em tempo real / anual |

Todo conector registra o que buscou, quando, de onde, sob qual licença e com qual checksum.
Esse registro é um insumo do manifesto e não é opcional.

#### 3.3.3 InSAR

Dois caminhos, escolhidos pela geografia:

- **Europa** — consumir os produtos pontuais EGMS Nível 2b/3 diretamente. As séries temporais
  de velocidade e deslocamento chegam como uma tabela; nenhum processamento.
- **Demais regiões** — ISCE2 ou ESA SNAP para interferogramas, MintPy ou LiCSBAS para inversão
  de série temporal. Mais pesado, inteiramente aberto, inteiramente reproduzível.

O módulo de observação consome objetos `DeformationSeries` em qualquer um dos casos, de modo
que o código a jusante não sabe nem precisa saber qual caminho os produziu.

---

### 3.4 Camada 2 — armazenamento

Convencional e deliberadamente sem novidades:

| Preocupação | Escolha | Nota |
|---|---|---|
| Vetorial, casos, livro-razão | PostgreSQL 16 + PostGIS 3 | O livro-razão também é espelhado em JSONL simples, de modo que sobrevive ao banco de dados |
| Imagens | Cloud-Optimised GeoTIFF em um armazenamento compatível com S3 | **Não o MinIO** — a edição community foi arquivada em 2025–26. Usar SeaweedFS, Garage, Ceph RGW, ou a nuvem própria do provedor soberano |
| Catálogo de imagens | STAC via `stac-fastapi` + `pgstac` | O mesmo padrão que os arquivos de origem usam |
| Análise | GeoParquet + DuckDB | As tabelas de achados são pequenas; isso não requer cluster |
| Orquestração | Apache Airflow (ou Prefect) | Um DAG por sítio por cadência |
| Identidade | Keycloak | Papéis abaixo |

**Papéis.** `analyst` (pode fazer triagem), `technical_officer` (pode corroborar),
`inspecting_official` (pode notificar, pode registrar resposta), `legal` (pode encaminhar),
`coordinator` (pode encerrar), `public` (vê apenas o que as regras de publicação permitem). A
máquina de estados do caso verifica o papel a cada transição; não há caminho que a contorne.

**Retenção.** Manifestos e entradas do livro-razão são permanentes. As imagens não precisam
ser: o manifesto nomeia os identificadores de grânulo, e os grânulos são reobteníveis do
arquivo público enquanto o arquivo existir — o que, no caso do Copernicus, é um compromisso de
política, não a boa vontade de um fornecedor.

---

### 3.5 Camada 3 — observação

Todo detector devolve um `Observation`, nunca um número isolado:

```python
@dataclass
class Observation:
    site_id: str; acquired: date
    detector: str; algorithm_version: str
    quantity: str; value: float; units: str
    valid_fraction: float          # share of the assessment area actually observable
    reliability: str               # ok | degraded | unusable
    params: dict; detail: dict; mask: Optional[np.ndarray]
```

**`reliability` tem três estados, não dois.** Um regulador precisa distinguir "medimos" de
"medimos pela metade" de "não conseguimos ver". Colapsar os dois últimos em um nulo é como os
programas de monitoramento acabam sub-relatando atividade exatamente na estação chuvosa, quando
operadores ilegais preferem trabalhar.

**A visibilidade é julgada sobre uma área de avaliação, não sobre a cena.** Nuvem sobre um
canto vazio nada diz sobre quão bem as frentes de lavra foram vistas; nuvem sobre as frentes de
lavra diz tudo. A área de avaliação padrão é o polígono da licença ampliado por um buffer de
1 km — larga o suficiente para conter uma incursão plausível, estreita o suficiente para que o
clima no canto distante não descarte uma boa medição.

#### 3.5.1 Área antropizada (`footprint.spectral_rule` v1.0.0)

```
disturbed = NDVI < 0.30
          & MNDWI < 0.10
          & BSI   > 0.00
          & B11   > 0.12
          & NBR   < 0.62
          & valid
→ morphological opening (r=1) then closing (r=2)
→ drop components below the 0.5 ha minimum mapping unit
```

Os índices são os publicados (Rouse 1974; Xu 2006; Rikimaru et al. 2002; Key & Benson 2006), e
as citações acompanham o manifesto. Os limiares são padrões para clima tropical úmido, são
parâmetros, e devem ser calibrados localmente antes que qualquer coisa seja emitida.

*Caminho de evolução.* Acrescentar um detector aprendido como uma **segunda opinião**, não
como substituto — o conjunto do Earth Genome / Amazon Mining Watch tem licença MIT e já está
validado (99,4% de especificidade / 89,5% de sensibilidade em um holdout geográfico). Suas
detecções *adicionais* passam por triagem humana antes de poderem entrar em um caso. A regra
permanece como base responsável para tudo o que chega a um ato.

#### 3.5.2 Água (`water.pond_extent` v1.0.0)

MNDWI > 0,10 e NDVI < 0,20, com abertura morfológica, com mínimo de 0,5 ha. A água de processo
é separada da água natural por turbidez (NDTI) e brilho no verde. Restrito ao polígono da
licença: a pergunta é quanta água o operador está represando, e um rio que atravessa a cena não
é isso. Um `freeboard_proxy` expressa a área da lagoa como fração da extensão mapeada da
estrutura de contenção; acima de 0,90 a superfície da água está se aproximando da crista da
estrutura.

`turbidity_gradient` compara o NDTI entre um trecho a montante e um a jusante do mesmo rio,
usando o rio como seu próprio controle para cancelar a maior parte do erro atmosférico e de
iluminação. A saída é um **proxy de triagem para sedimento em suspensão e um gatilho para
amostragem** — nunca uma determinação de qualidade da água, e o dossiê o diz nesses termos.

#### 3.5.3 Mudança (`change.robust_trend` v1.0.0)

Ajusta apenas datas totalmente observadas. Datas limitadas por nuvem são limites inferiores e
são relatadas separadamente, nunca unidas à linha — unir essas datas desenha uma queda na área
antropizada que nunca aconteceu.

- **Theil–Sen** mediana das inclinações par a par, com um intervalo de 68% a partir dos
  percentis 16 e 84. Ponto de ruptura de 29%; os mínimos quadrados ordinários têm ponto de
  ruptura zero, propriedade errada para compostos com triagem de nuvem.
- **Busca de ponto de quebra único** com quatro guardas, cada uma existindo porque, sem ela, o
  ajuste relata uma mudança de regime que não existe:
  1. ≥ 5 observações de cada lado;
  2. ≥ 5 meses de intervalo de cada lado;
  3. ≥ 25% de melhoria na soma dos quadrados dos resíduos em relação ao ajuste de reta única;
  4. **os intervalos de 68% das inclinações dos dois segmentos não podem se sobrepor.** A
     guarda 4 faz a maior parte do trabalho. Sem ela, um sítio tranquilo e conforme relata
     mudança de taxa sempre que seus primeiros meses oscilam — e um regulador informado de uma
     mudança de taxa que não existe deixa de acreditar nas que existem.
- **`current_rate_per_month`** é a inclinação pós-ponto de quebra, quando existe um; caso
  contrário, a inclinação do período inteiro. Quando uma série tem mudança de regime, a
  inclinação do período inteiro é uma mistura de duas taxas e não descreve nenhuma delas.
- **`observation_gaps`** lista todo intervalo maior que 75 dias sem observação utilizável.
  Relatado junto com toda tendência.

#### 3.5.4 Deformação (`deformation.velocity_screen` v1.0.0)

Consome séries de dispersores persistentes. Faz a triagem pela velocidade **recente** (padrão:
últimos 365 dias), e não pela velocidade de todo o histórico, e relata ambas. Uma crista que se
arrastou a 2 mm/ano por quatro anos e a 30 mm/ano por seis meses tem velocidade de todo o
histórico de cerca de 6 mm/ano, o que é tranquilizador e errado.

Sinalizadores: `velocity_exceeds_threshold` (percentil 10 das velocidades recentes além de
−10 mm/ano), `accelerating` (termo quadrático mediano além de −6 mm/ano²), e
`recent_velocity_at_least_double_historic`.

Menos de cinco pontos coerentes sobre a estrutura devolve `unusable`, com motivo declarado e
uma recomendação — cristas vegetadas ou recém-remanejadas decorrelacionam, e a saída honesta é
"esta técnica não consegue ver esta estrutura; usar refletores de canto ou outro método", e não
um número.

**O módulo não prevê ruptura.** Ele relata que uma crista está se movendo mais rápido do que
antes e que uma inspeção de engenharia é recomendável.

#### 3.5.5 Volume (`volume.dem_difference` v1.0.0)

Corte e aterro entre duas superfícies de elevação, com um modelo de erro de dois termos:

```
sigma_random     = sigma_z · cell_area · L · sqrt(n)      # L = correlation length, default 10 cells
sigma_systematic = bias_sigma · changed_area             # default bias_sigma = 0.5 m
sigma_total      = hypot(sigma_random, sigma_systematic)
```

O termo sistemático normalmente domina e só é reduzido co-registrando as duas superfícies sobre
terreno estável fora das frentes de lavra; uma implantação deve registrar que isso foi feito. A
suposição ingênua de erro independente subestima o intervalo em aproximadamente uma ordem de
grandeza.

A saída é um **intervalo**, nunca um valor pontual, e é rotulada como *material movimentado,
não material vendido* — estéril, capeamento e remanejo de pilhas estão todos incluídos. Usar
como limite superior de extração; nunca como número de produção.

---

### 3.6 Camada 4 — reconciliação

#### 3.6.1 Cadastro (`crosscheck.cadastre` v1.0.0)

Divide a área antropizada em três classes em relação a cada título:

- **confiavelmente dentro** — dentro do polígono erodido pela tolerância de fronteira;
- **confiavelmente fora** — fora do polígono dilatado pela tolerância;
- **indeterminado** — no anel entre os dois.

`BOUNDARY_TOLERANCE_M = 25.0` por padrão: a geolocalização do Sentinel-2 é especificada melhor
que 11 m a 95%, e o erro do vetor cadastral na maioria dos registros é da mesma ordem ou pior.
**A tolerância é aplicada em favor do titular, e a área indeterminada nunca é computada como
violação.** Essa única decisão é a diferença entre um sistema que um advogado de mineração
desmonta em uma tarde e um que se sustenta.

Também emite notas de registro: atividade dentro de um título dormente, suspenso, vencido ou
meramente requerido; atividade onde nenhum título de qualquer status cobre a área; atividade
dentro de um título em fase de pesquisa, que não autoriza extração.

#### 3.6.2 Declarações (`crosscheck.declaration` v1.0.0)

**Não converter área antropizada em toneladas para comparar com a produção declarada.** A
conversão exige relação estéril/minério, teor do minério, umidade, manejo de estéril e
movimentação de pilhas, nada disso público. Uma exigência construída sobre essa cadeia não
sobrevive ao contraditório.

O que o módulo faz em vez disso:

| Verificação | Sinal |
|---|---|
| **Atividade sem declaração** | ≥ 5 ha de superfície ativa antropizada em um período sem nada declarado. Não requer nenhum fator de conversão. |
| **Intensidade contra pares** | Toneladas declaradas por hectare ativo por mês, posicionadas na distribuição em decis de operações comparáveis (mesma commodity, método, região). O decil inferior é um sinalizador. |
| **Crescimento contra declaração** | Crescimento de área antropizada no decil superior combinado com intensidade declarada no decil inferior. |
| **Consistência entre declarações** | A mesma grandeza reportada à CFEM, aos acionistas, e sob o Cap. 10 da Diretiva Contábil da UE / ESTMA. Não requer sensoriamento remoto algum e é frequentemente a verificação mais produtiva disponível. |

A saída é um **escore de prioridade de auditoria com motivos**, marcado:

> RESULTADO DE TRIAGEM — apenas priorização de auditoria. Não é uma apuração de tributo ou
> royalty devido, e não é prova de subdeclaração.

Todo sinalizador vem acompanhado de suas explicações inocentes nomeadas — decapeamento
adiantado em relação ao minério, formação de pilha, desenvolvimento pré-produção — porque a
auditoria existe para testá-las.

#### 3.6.3 Gravidade

Classificada pelo que está em jogo, não por hectares:

| Nível | Gatilho |
|---|---|
| **crítico** | sinalizadores de deformação em uma estrutura de rejeitos; > 5 ha dentro de área restrita; > 5 ha em um título que nada autoriza (requerido/vencido) |
| **alto** | > 5 ha fora do polígono titulado; > 5 ha em um título suspenso; prioridade de auditoria ≥ 0,5; qualquer sobreposição com área restrita |
| **médio** | > 1 ha fora do polígono, ou qualquer sinalizador de declaração |
| **baixo** | tudo o mais |

Dez hectares dentro de uma unidade de conservação superam cinquenta hectares de expansão
lícita, e uma crista em aceleração supera ambos — nada mais na lista pode matar alguém.

---

### 3.7 Camada 5 — caso, e devido processo em código

```
observed → screened → corroborated → notified → contested → reviewed
                          ↓              ↓          ↓          ↓
                      dismissed ←────────┴──────────┴──── substantiated → referred → closed
```

Invariantes impostas, cada uma com um teste:

| Invariante | Aplicação |
|---|---|
| Toda transição nomeia um ser humano e um papel | `DueProcessError` sobre ator vazio |
| Uma notificação exige um caso corroborado | `administrative_notice()` recusa caso contrário |
| Um caso não pode ser revisado enquanto a janela de resposta estiver aberta | `DueProcessError`, a menos que uma resposta tenha sido registrada ou a janela tenha expirado |
| Nada é público antes da notificação | `public_view()` devolve `None` |
| Um caso notificado mas não resolvido é visível apenas à parte notificada | `PublicationState.PARTY_ONLY` |
| Um arquivamento é publicado como resumo | `PublicationState.PUBLIC_SUMMARY` |
| Uma resposta é prova do mesmo grau que a do Estado | armazenada, com hash, registrada no livro-razão |

Estados de publicação: `internal → notified_party_only → public_summary | public_full`.

A razão pela qual um caso notificado mas não resolvido permanece fora da visão pública não é
pudor. Publicar uma alegação não resolvida impõe a penalidade reputacional antes do
procedimento que deveria decidi-la — e uma plataforma que faz isso será, corretamente,
proibida por decisão judicial.

---

### 3.8 Camada 6 — tradução

O mesmo achado selado, renderizado de cinco maneiras. Não cinco resumos: cinco traduções, cada
uma explícita sobre o que não afirma.

| Método | Registro | Carrega | Recusa |
|---|---|---|---|
| `technical_annex()` | técnico | cada insumo, algoritmo, parâmetro, hash; receita de reprodução | conclusões de direito |
| `administrative_notice()` | administrativo | fato, norma, prazo, como contestar, onde obter os dados brutos | qualquer apuração de infração |
| `judicial_dossier()` | jurídico | custódia, distinção entre dado primário e derivado, limitações, histórico processual | dolo, autoria, existência de infração |
| `oversight_brief()` | político | sítios por servidor, casos abertos, casos encerrados | hectares como manchete |
| `public_card()` | esfera pública | o quê, onde, quanto, em linguagem simples; se o operador respondeu | qualquer sugestão de que uma detecção é uma condenação |

As jurisdições são configuradas como objetos `LegalFrame` que carregam as normas aplicáveis;
`BRAZIL` e `EUROPEAN_UNION` são entregues, e a notificação é renderizada em português ou inglês
conforme o caso.

**A salvaguarda contra evidência sintética.** `administrative_notice()` e `judicial_dossier()`
levantam `SyntheticEvidenceError` se a cadeia de evidência contiver insumos simulados. O anexo
técnico é permitido, com um aviso de SIMULATION.

---

### 3.9 Camada 8 — auditoria

**`EvidenceManifest`** — `manifest_id`, `site_id`, a questão regulatória, carimbo de tempo de
criação, versões de software, insumos (tipo, identificador, fonte, momento de obtenção,
licença, checksum), algoritmos (nome, versão, parâmetros, referência), saídas (nome, valor,
unidades, digest), pressupostos, limitações, jurisdição, status probatório, `prev_hash`,
`manifest_hash`. JSON canônico — chaves ordenadas, sem espaços em branco incidentais — de modo
que uma única serialização produz um único hash.

**`Ledger`** — JSONL apenas para acréscimo (append-only), cada entrada carregando o hash de sua
predecessora. `verify_chain()` recalcula todo hash e todo elo e devolve um relatório em vez de
lançar exceção: uma cadeia quebrada é um fato a ser relatado a quem é responsável pelo registro,
não uma exceção a ser engolida.

**`replay_recipe()`** emite os comandos e insumos que reproduzem um achado.

Para garantias mais fortes do que uma cadeia interna oferece, carimbar o topo do livro-razão com
RFC 3161, ou publicá-lo periodicamente em um diário oficial. Isto é uma cadeia de hash, não uma
blockchain: a administração pública não precisa de confiança distribuída, precisa de um
registro pelo qual possa ser responsabilizada.

---

### 3.10 Dependências e licenciamento

**Núcleo (obrigatório):** Python ≥ 3.10, numpy. Isso é tudo.
**Recomendado:** scipy, scikit-image, matplotlib, Pillow.
**Produção:** pystac-client, rasterio, GDAL, PostgreSQL + PostGIS, Airflow, Keycloak.
**Aceleradores opcionais:** shapely, pyproj, dask, TorchGeo.

O núcleo não tem dependências geoespaciais obrigatórias. Uma secretaria municipal com um único
notebook e sem orçamento de compras pode rodar a biblioteca de detecção — objetivo de projeto,
não acaso.

Política de licenciamento: apenas aprovadas pela OSI; um caminho de saída documentado para cada
dependência; licenças reverificadas a cada ciclo de compras. **O MinIO é excluído** (a edição
community foi arquivada em 2025–26). Componentes AGPL (Grafana, Metabase OSS, CKAN, Garage) são
adequados para uso, mas têm implicações de compras se a instituição os modificar e os expuser
como serviço.

Classificação-alvo: **Bem Público Digital**, conforme o DPG Standard, seguindo o reconhecimento
do QGIS em fevereiro de 2025.

---

### 3.11 Níveis de implantação

| | Nível 1 — município / Ministério Público | Nível 2 — órgão estadual | Nível 3 — regulador nacional |
|---|---|---|---|
| Sítios | 1–20 | 20–500 | cadastro completo |
| Cadência | sob demanda | mensal | mensal, com alerta por radar no intervalo |
| Infraestrutura | um notebook, offline | um servidor | um pequeno cluster |
| Armazenamento | GB | poucos TB | dezenas de TB |
| Custo de imagens | 0 | 0 | 0 (dentro das cotas gratuitas do CDSE) |
| Equipe | 1 analista | 1–2 técnicos + fiscais existentes | pequena unidade + corpo de fiscalização existente |
| Saídas | anexos para casos já abertos | portal + notificações | dados abertos, API, integração com royalties |

---

### 3.12 O que não foi construído, e o que seria preciso

| Lacuna | Esforço | Nota |
|---|---|---|
| Ingestão STAC ao vivo, exercitada com imagens reais | 2–4 semanas | O provedor está escrito; o ambiente de testes não tinha saída de rede (egress). **Fazer isso primeiro.** |
| Precisão/revocação em cenas reais com desfechos conhecidos | 4–8 semanas | A etapa que valida ou mata o projeto |
| Cadeia de processamento InSAR fora da Europa | 6–10 semanas | ISCE2/SNAP + MintPy; a Europa tem o EGMS de graça |
| Detector aprendido como segunda opinião | 3–5 semanas | Os pesos do Amazon Mining Watch são MIT |
| Portal, API OGC, exportação de dados abertos | 6–8 semanas | Convencional; GeoNode ou pygeoapi |
| Recebimento de denúncias (grievance intake) | 4 semanas | Padrão ODK/Kobo |
| Identidade e auditoria multi-inquilino | 4 semanas | Keycloak |
| Localização além de pt/en | contínuo | A abstração `LegalFrame` é o ponto de encaixe |

---

### 3.13 Mapa do repositório

```
src/soma/
  geom.py                  ellipsoidal geometry, no geospatial stack
  scene.py                 the unit of observation; content hashing
  indices.py               spectral indices with citations
  providers/
    base.py                SceneProvider interface
    stac_sentinel2.py      CDSE / Earth Search — production
    synthetic.py           deterministic simulator
  detectors/
    base.py                Observation; three-state reliability
    footprint.py           disturbed-surface delineation
    water.py               pond extent, turbidity gradient, freeboard proxy
    change.py              Theil–Sen trend, guarded breakpoint, gaps
    deformation.py         InSAR velocity screen
    volume.py              DEM differencing with a two-term error model
  crosscheck/
    cadastre.py            inside / outside / indeterminate; registry notes
    declaration.py         intensity, cross-filing, audit priority
  evidence.py              manifest, canonical JSON, hash-chained ledger
  cases.py                 state machine with due process enforced
  dossier.py               the five translations; legal frames; guards
  render.py                evidence images and charts
  pipeline.py              end-to-end run for one site
  portfolio.py             the four-site demonstration
  dashboard.py             self-contained HTML build
  cli.py                   soma demo | ledger | case
tests/                     49 tests; run with pytest or tests/run_tests.py
```

## 4 Transcrição da Demonstração

Tudo abaixo foi produzido executando o código entregue em 19 de agosto de 2026, a partir de um diretório de trabalho limpo. Nada aqui foi transcrito à mão: esta seção é gerada reexecutando cada comando e capturando sua saída.

### 4.1 A suíte de testes

Roda com pytest, ou com o executor embutido quando o pytest não está instalado — que é
a situação em um ambiente governamental de acesso restrito.

```
$ python3 tests/run_tests.py
  ok    test_geom.test_hemisphere_area
  ok    test_geom.test_point_in_concave_ring
  ok    test_geom.test_point_in_ring
  ok    test_geom.test_square_area_at_equator

49 passed, 0 failed
```

### 4.2 A carteira de quatro sítios

```
$ PYTHONPATH=src python3 -c "from soma.portfolio import run_portfolio; run_portfolio()"

SITE         SEVERITY  STATE        DISTURBED   OUTSIDE    INDET   RATE NOW
BR-PA-0001   critical  contested       129.7h     36.6h     3.6h     4.65/mo
BR-MT-0002   critical  notified         76.9h     22.5h     5.7h     1.33/mo
BR-MG-0003   high      screened         67.8h      3.3h     2.3h     0.36/mo
BR-GO-0004   low       closed           58.5h      0.2h     0.2h     0.25/mo
```

#### O que é cada sítio

- **BR-PA-0001** — a expansão acelera de 0.70 para 4.65 ha/mês, depois cruza o limite da
  licença rumo a uma unidade de conservação. A declaração não acompanha o ritmo. O titular
  respondeu a parte dela, de modo que o caso permanece em `contested`.
- **BR-MT-0002** — extração sustentada com base em nada além de um requerimento pendente. Um
  requerimento de pesquisa não autoriza nenhuma obra.
- **BR-MG-0003** — título registrado como suspenso, superfície de lavra ainda em crescimento,
  nada declarado. Sua estrutura de rejeitos avança de forma constante, mas *não* está
  acelerando, de modo que a triagem deliberadamente não o eleva a crítico.
- **BR-GO-0004** — inteiramente regular. Levantado pela triagem de rotina, examinado,
  **arquivado**, e encerrado. É o único dos quatro cujo caso está publicamente visível.

### 4.3 Recuperação da verdade simulada de referência

O simulador foi configurado com crescimento de rotina a cerca de 0.7 ha/mês, saltando para
cerca de 4.5 ha/mês em julho de 2025, com a frente de lavra cruzando o limite da licença em
setembro de 2025. Rodando às cegas sobre as imagens resultantes:

```
quantity                                detected   simulated truth
------------------------------------------------------------------
disturbed surface, Jul 2026 (ha)           129.7             126.2
growth before the change (ha/mo)            0.70              0.71
growth after the change (ha/mo)             4.65              4.50
date of the rate change               2025-05-01        2025-07-01
impounded water, peak (ha)                  22.3              22.3
observations used / cloud-limited          25/18         43 months
```

As áreas acompanham a verdade com margem de poucos pontos percentuais nas datas plenamente
observadas. A mudança de taxa foi encontrada e quantificada corretamente; sua data foi
recuperada com dois meses de antecipação, o que é uma caracterização honesta do que um ajuste
de ponto de quebra sobre composições mensais é capaz de fazer, e é reportado como tal, em vez
de suavizado.

### 4.4 O livro-razão de evidências, e o que ocorre quando ele é alterado

```
$ PYTHONPATH=src python3 -m soma.cli ledger verify --root data/out/cases
{
  "entries": 4,
  "intact": true,
  "head": "9b709edf5694b13eed0b07222ace0ad7952b80c46fd2bee99f1671ce4ba5aed1",
  "problems": []
}
```

Agora altere um número em um lançamento passado — 22.5 hectares fora do título viram zero —
e verifique novamente:

```
{
  "entries": 4,
  "intact": false,
  "head": "9b709edf5694b13eed0b07222ace0ad7952b80c46fd2bee99f1671ce4ba5aed1",
  "problems": [
    "entry 1 (MNV-b4f8c05596c1d20b) hash mismatch: stored c76b54398c93f1c180487963867792c1a023e8e4a4ec2e73a606242ce564423e, recomputed 96538b9d9422e5f735b1d798e67ca7617f99665dd918dc1aecf2bc7b1520d740"
  ]
}
```

O achado não pode ser silenciosamente reescrito. Essa propriedade é o que permite a um
operador provar que o registro do Estado não foi alterado, e ao Estado provar o mesmo perante
um tribunal.

### 4.5 Devido processo, aplicado em vez de prometido

```
unnamed actor         -> every transition must name a responsible person and their role; automated adva
skipping notification -> cannot move a case from corroborated to substantiated. Permitted: ['notified',
review during window  -> the response window is open until 2026-09-18T05:10:40+00:00. A case cannot be 
publicly visible now  -> None
```

E a trava contra a emissão de um ato legal a partir de evidência simulada:

```
administrative_notice -> refused: refusing to produce an administrative notice: the evidence chain c
judicial_dossier      -> refused: refusing to produce a judicial dossier: the evidence chain contain
technical_annex       -> permitted, with a SIMULATION banner
```

### 4.6 O que é publicável, e quando

```
CASE-2026-2A4FF177     publishable=True   58.5 hectares of mining disturbance mapped, all of it inside t
CASE-2026-5E1E5198     publishable=False  The holder has been notified and the response window is runnin
CASE-2026-9A84C406     publishable=False  The affected party has not yet been notified. Publishing befor
CASE-2026-B4F8C055     publishable=False  The holder has been notified and the response window is runnin
```

Somente o caso arquivado é público. Os outros três estão ou antes da notificação ou
notificados e não resolvidos, e publicar uma alegação não resolvida imporia a sanção
reputacional antes do procedimento que deveria decidi-la.

## 5 Base de Evidências

Notas de pesquisa de trabalho. Cada linha carrega uma fonte. Verificado durante a rodada de pesquisa de 19-08-2026; reverifique antes de qualquer licitação, pois licenças e endpoints mudam.

### 5.1 O arsenal comercial (o que os operadores já têm)

- Global Mining Tech 50 (IMARC / Mines and Money, 2026): os 50 principais fornecedores de
  tecnologia de mineração venderam ~US$6,8 bi em tecnologia de mineração/metais em 2025;
  +73,5% em cinco anos.
  <https://minesandmoney.com/news/industry/global-mining-tech-50-the-top-50-global-mining-metals-tech-players>
- A consolidação está se acelerando e é *vertical* (fabricantes de equipamento comprando o
  software que planeja o trabalho que suas máquinas executam):
  - A Caterpillar adquiriu a **RPMGlobal** (~US$728–735 mi), concluída em fevereiro de 2026.
    <https://www.caterpillar.com/en/news/corporate-press-releases/h/rpm-global-acquisition.html>
    <https://im-mining.com/2026/02/18/caterpillar-competes-rpmglobal-acquisition-expanding-data-driven-mining-technology-and-software-solutions-2/>
  - A Weir adquiriu a **Micromine** (~US$840 mi; concluída em abril de 2025 — verificado
    de forma independente em <https://www.mining-technology.com/news/weir-micromine-acquisition/>;
    o valor de ~US$800 mi citado pela IMARC era a cifra anunciada, não a concluída).
  - A Sandvik é dona da **Deswik**. A Bentley é dona da **Seequent** (Leapfrog, Evo).
  - A **Constellation Software** adquiriu mais de 30 empresas de software de mineração
    desde 2011; carro-chefe **Datamine**.
  - A Epiroc adquiriu 13 empresas de tecnologia de mineração desde 2021.
  (tudo conforme a matéria do Global Mining Tech 50 acima)
- Listagem do SourceForge "Mining software / Europe" (o link do usuário) — 30 produtos
  visíveis, que se distribuem nas seguintes camadas funcionais: SSMA (Intelex, EHS Insight,
  SafetyIQ, PeopleTray, Pervidi), SCADA/IIoT (FrameworX), gestão de partes interessadas e de
  reclamações (Borealis), química de processo (HSC Chemistry / Metso), superfícies e
  geoestatística (Surfer, RockWorks, LogPlot8), gestão de dados ambientais
  (EnviroDataVault/RPMGlobal, Envirosuite), inspeção (Inspectivity, Dashpivot), acesso a
  observação da Terra (EarthCache/SkyWatch), projeto de mina (MineCycle/Bentley, Promine), IA
  sobre dados 3D (Strayos), contabilidade metalúrgica (INVENTEO/Caspeo, AMIRA P754), titularidade
  e licenças (trueMINER), gêmeos digitais (MineTwin), perfuração e desmonte
  (MineExcellence BIMS), geotecnia (Rocscience), volumetria por drone (Propeller), controle de
  intervalo curto (ShiftManager/RPMGlobal), gestão de ativos empresariais (4site), integração
  de automação (Lightship).
  <https://sourceforge.net/software/mining/europe/>
  → NOTA: trata-se de uma *lista de capacidades autodeclaradas*. Tratada neste projeto como a
    especificação que o setor público precisa igualar, não como um endosso.

### 5.2 A lacuna de capacidade do setor público (Brasil, medida)

Tribunal de Contas da União (TCU), acórdão de 2024 sobre a ANM (Agência Nacional de Mineração):
- ~R$ 16,4 bi de receita mineral não arrecadada em oito anos; R$ 12,4 bi não recuperados
  entre 2014 e 2021; R$ 4 bi perdidos por prescrição entre 2017 e 2021; R$ 20 bi em risco de
  prescrição.
- A equipe de fiscalização da CFEM é de **seis servidores mais um chefe** para
  aproximadamente **12.000** processos de cobrança da CFEM.
- A força de trabalho da ANM caiu **41,9%** desde 1996; 695 servidores no período 2010–2023.
- As fiscalizações caíram **92%**: de 2.184 auditorias em 2014 para 173 em 2019.
- O TCU determinou que a ANM apresentasse, em 60 dias, um plano para um sistema de
  arrecadação e fiscalização.
  <https://agenciabrasil.ebc.com.br/geral/noticia/2024-10/tcu-cobra-anm-por-sonegacao-de-rs-16-bi-de-mineradoras-em-impostos>

Boletim de barragens de rejeitos da ANM, outubro de 2025 (publicado em nov. de 2025):
- **917** barragens de mineração registradas no SIGBM; **470** enquadradas na PNSB (política
  de segurança de barragens).
- Nível de emergência 3: **1**; nível 2: **8**; nível 1: **62**; situação de alerta: **22** →
  **93** estruturas em alerta ou emergência declarada.
- 1.241 inspeções de barragens realizadas em 2025 até aquele ponto.
  <https://www.gov.br/anm/pt-br/assuntos/barragens/boletim-de-barragens-de-mineracao/boletim-mensal-outubro-2025>

MapBiomas (módulo de mineração da Coleção 8, publicado em 2023, ano de referência 2022):
- Área total minerada no Brasil: **443.000 ha**; garimpo: **263.000 ha** (59%); industrial:
  **180.000 ha** (41%).
- +35.000 ha somente em 2022.
- **92%** da área minerada está no bioma Amazônia.
- **>25.000 ha** dentro de Terras Indígenas; **>78.000 ha** dentro de Unidades de Conservação
  — juntas, 39%.
- Mineração dentro de territórios protegidos +190% no período 2018–2022; em Terras
  Indígenas, +265%.
- Cinco bacias hidrográficas concentram 66% da mineração nacional; Tapajós 20% (54.800 ha),
  Teles Pires 18% (48.100 ha).
  <https://brasil.mapbiomas.org/en/2023/09/22/amazonia-concentra-mais-de-90-do-garimpo-no-brasil/>
- Achado correlato do MapBiomas: 77% do garimpo na Amazônia está a menos de 500 m de água [17].
  <https://brasil.mapbiomas.org/en/2024/04/19/77-do-garimpo-na-amazonia-esta-a-menos-de-500-metros-da-agua/>

### 5.3 Dados públicos que já existem (a matéria-prima)

#### Brasil — dados abertos da ANM (dados.gov.br, diário/tempo real)
| Conjunto de dados | O que ele oferece |
|---|---|
| SIGMINE | polígonos de todo processo minerário ativo/inativo, SHP + KML, atualizado diariamente |
| Cadastro Mineiro | requerimentos, títulos, titulares, regimes; microdados diários |
| CFEM (Sistema de Arrecadação) | pagamentos de royalties — a proxy de produção declarada |
| SIGBM | barragens de rejeitos: características técnicas, tipo de rejeito, atualizações em tempo real |
| TAH | taxa anual por hectare: processo, ano, titular, hectares, valor |
| AMB (Anuário Mineral Brasileiro) | produção e destinação (vendas, transferências, consumo) desde 2010 |
| SICOP | controle de processos administrativos |
| Dívida Ativa | créditos não pagos registrados para cobrança |
| DIPEM | investimento declarado em pesquisa mineral por município e substância |
| SOPLE | oferta pública / leilão de áreas disponíveis |
<https://www.gov.br/anm/pt-br/acesso-a-informacao/dados-abertos/bases-de-dados>
Endpoints de dados em massa: <https://dadosabertos.anm.gov.br/SIGMINE/PROCESSOS_MINERARIOS/>
Serviço ArcGIS REST: <https://geo.anm.gov.br/arcgis/rest/services/SIGMINE/dados_anm/MapServer>
Visualizador público de barragens de rejeitos: <https://sigbm.anm.gov.br/Publico>

#### Brasil — INPE
- DETER (alertas de desmatamento quase em tempo real) e PRODES (corte raso anual),
  publicados via TerraBrasilis com download aberto e API.
  <https://terrabrasilis.dpi.inpe.br/en/data-access/>

#### Europa — Copernicus Data Space Ecosystem (CDSE)
Cotas do plano gratuito para um "Usuário Geral Copernicus" (este é todo o argumento de custo):
- APIs do Sentinel Hub: 10.000 requisições/mês, 10.000 unidades de processamento/mês, teto de
  300 PU/min, 300 req/min.
- openEO: 10.000 créditos/mês, 12 requisições/min, 2 jobs simultâneos.
- S3 / OData / STAC: **12 TB por período móvel de 30 dias**, 2.000 req/min, 4 conexões
  simultâneas, 20 MB/s por conexão; acima da cota, degrada para 1 MB/s em vez de cortar o
  acesso.
- Acesso direto via HTTP a COG: 50.000 requisições/mês.
- Tokens de acesso válidos por 10 minutos, renováveis dentro de 60.
  <https://documentation.dataspace.copernicus.eu/Quotas.html>
APIs oferecidas: OData, STAC, OpenSearch, Catalog Subscriptions, Sentinel Hub, openEO, S3,
Traceability API, On-Demand Production (CARD-BS, CARD-COH6/12).
  <https://documentation.dataspace.copernicus.eu/APIs.html>

#### Europa — European Ground Motion Service (EGMS)
- InSAR Sentinel-1 de movimento do solo, **precisão milimétrica**, cobertura de toda a
  Europa, **atualizado anualmente**, níveis de produto Básico / Calibrado / Ortho,
  disponível para download no EGMS Explorer (apenas as duas versões mais recentes
  permanecem on-line). Voltado explicitamente para autoridades que monitoram barragens,
  pontes, ferrovias e edificações, e para subsidência induzida por mineração.
  <https://land.copernicus.eu/en/products/european-ground-motion-service>
  <https://egms.land.copernicus.eu/>

#### Conjuntos de dados globais
- **Global-scale mining polygons v2** (Maus et al. 2022, *Scientific Data*), PANGAEA, CC BY.
  <https://doi.pangaea.de/10.1594/PANGAEA.942325> · <https://www.nature.com/articles/s41597-022-01547-4>
- **Open database on global coal and metal mine production** (Jasansky et al. 2023,
  *Scientific Data*): 1.171 minas, 80 materiais (6 tipos de carvão, 21 minérios,
  12 concentrados, 19 metais), 2000–2021, 80 países (EUA 233, Austrália 213, Rússia 100,
  África do Sul 100, China 95, **Brasil 89**). Construído manualmente a partir de mais de
  1.900 relatórios públicos de empresas, cada dado vinculado ao seu documento-fonte.
  GeoPackage + CSV no Zenodo sob licença CC BY 4.0; código em R no GitHub sob GPL-3.
  Lacunas conhecidas: China subcoberta; cobertura de cobre ~60–70%, ouro ~30–40%; exclui
  garimpo e lixiviação in situ. <https://www.nature.com/articles/s41597-023-01965-y>
  <https://doi.org/10.5281/zenodo.7369478>
- **Global Tailings Portal** (GRID-Arendal com a Investor Mining and Tailings Safety
  Initiative, copresidida pelo Church of England Pensions Board e pelo Council on Ethics dos
  fundos de pensão suecos AP, com apoio do PNUMA). ~1.800 instalações de rejeitos de
  ~100 empresas; 20 campos de dados, incluindo método de alteamento, altura, volume,
  classificação de risco, histórico de estabilidade, impacto a jusante. Apenas 332 das 727
  empresas listadas pesquisadas responderam. Pesquisável on-line; download em massa mediante
  solicitação.
  <https://tailing.grida.no/about>
- **Global Coal Mine Tracker** (Global Energy Monitor): banco de dados + wiki, validado com
  fontes governamentais, relatórios de empresas, mídia, ONGs locais e contatos de campo;
  metano estimado a partir de produção, teor de gás e coeficientes de emissão; força de
  trabalho estimada por aprendizado de máquina quando não divulgada; ciclo de atualização
  anual desde 2023.
  <https://globalenergymonitor.org/projects/global-coal-mine-tracker/methodology/>

### 5.4 Monitoramento de interesse público que já funciona

- **Amazon Mining Watch** (Earth Genome / Earthrise Media, com o Pulitzer Center e
  parceiros) — cobre os nove países amazônicos, voltado a jornalistas, ativistas,
  pesquisadores e formuladores de política.
  <https://amazonminingwatch.org/en>
  Código: **MIT**; produtos de dados **CC BY 4.0**; produtos em massa no Source Cooperative.
  Modelo: conjunto de seis CNNs sobre recortes Sentinel-2 L1C de 48×48×13
  (~480 m por lado), a maioria com ~800 mil parâmetros mais um modelo de ~100 mil, escores
  em média; composições medianas multimensais sobre a bacia de 8,2 milhões de km². Teste
  geográfico de retenção na Venezuela: **99,4% de especificidade / 89,5% de sensibilidade**;
  avaliação combinada **99,8% / 92,4%**. Máscaras de cicatriz derivadas com SAM2.
  <https://github.com/earthrise-media/mining-detector>
  <https://source.coop/earthgenome/amazon-mining-watch>
- **MAAP** (Monitoring of the Andean Amazon Project) — relatórios quase em tempo real sobre
  desmatamento por mineração de ouro. <https://www.maapprogram.org/amazon-gold-mining-2025/>
- **SkyTruth** — ferramentas gratuitas e de código aberto; projetos nomeados Cerulean
  (petróleo), Mining (remoção de topo de montanha), Flaring, 30x30 Tracker, Monitor.
  <https://skytruth.org/about/technology/>
- **Code for Africa — Africa Mining Watch** (anúncio de parceria).
- Palestra na FOSS4G 2024: "Leveraging AI and Open Source Geospatial Software to Combat
  Illegal Gold Mining in the Amazon". <https://talks.osgeo.org/foss4g-2024/talk/FX8X7S/>

### 5.5 Ganchos jurídicos

- **Diretiva de Dados Abertos da UE**, Regulamento de Execução da Comissão (UE) **2023/138**:
  seis categorias de conjuntos de dados de alto valor; "Geoespacial" e "Observação da Terra e
  meio ambiente" são duas delas. Obrigação: gratuito, legível por máquina, **acesso via API e
  download em massa**, licenciado sob **CC BY 4.0 ou licença menos restritiva**, metadados
  conforme o Reg. (CE) 1205/2008, escala até 1:5000, versão vigente mais histórico mantidos.
  A conformidade era devida por volta de junho de 2024.
  <https://eur-lex.europa.eu/eli/reg_impl/2023/138/oj/eng>
  <https://datos.gob.es/en/blog/complying-europe-high-value-sites-earth-observation-and-environment-regulation>
- **Convenção de Aarhus** (acesso à informação ambiental, participação, acesso à justiça) —
  o fundamento jurídico permanente para um monitor de mineração voltado ao público na Europa.
  <https://environment.ec.europa.eu/law-and-governance/aarhus_en>
- **EITI Standard 2023** — divulgação sistemática, política de dados abertos, propriedade
  beneficiária e transparência contratual.
  <https://eiti.org/sites/default/files/2023-06/2023%20EITI%20Standard.pdf>
  <https://eiti.org/documents/eiti-open-data-policy>
- **Diretiva Contábil da UE, Capítulo 10** — divulgação de pagamentos a governos por empresas
  extrativas (o análogo europeu da ESTMA canadense).
- **Brasil**: Lei 14.066/2020 (nova Política Nacional de Segurança de Barragens, pós-Brumadinho,
  proibindo barragens a montante e agravando penalidades); Lei 12.334/2010 (PNSB);
  Lei 12.527/2011 (Lei de Acesso à Informação).
- O **QGIS** foi reconhecido como **Bem Público Digital** pela Digital Public Goods Alliance
  em fevereiro de 2025 — um precedente para classificar esta plataforma como um BPD.
  <https://blog.qgis.org/2025/02/08/qgis-recognized-as-digital-public-good/>

### 5.6 Ressalva sobre ferramentas
- A edição comunitária do **MinIO** entrou em modo de manutenção / foi arquivada
  (final de 2025 – 2026) depois que funcionalidades foram retiradas da versão AGPL. **Não**
  projete um sistema do setor público em torno dela.
  <https://stormdevelopments.ca/blog/minio-s-community-edition-is-archived-what-still-runs-in-2026/>
  <https://www.futuriom.com/articles/news/minio-faces-fallout-for-stripping-features-from-web-gui/2025/06>

### 5.7 Restrições de ambiente observadas nesta construção
- O tráfego HTTP de saída do sandbox é restrito por proxy: registros de pacotes (PyPI, npm)
  e `git` para github.com funcionam; hosts arbitrários (endpoints STAC,
  dadosabertos.anm.gov.br) não funcionam.
- Consequência para o protótipo: o código real dos provedores é escrito contra as APIs ao
  vivo, e um provedor sintético determinístico permite que todo o pipeline seja executado
  aqui de ponta a ponta.

### 5.8 Fatos sobre sensores (verificados em 19/08/2026, necessários para alegações honestas de capacidade)

**Sentinel-1 (radar em banda C)**
- O Sentinel-1D concluiu a comissão em órbita e entrou em operação em 2026; abertura dos
  dados aos usuários em 17 de abril de 2026. Constelação agora composta por
  Sentinel-1A + 1C + 1D (o Sentinel-1B falhou e sua missão foi encerrada em agosto de 2022).
  A ESA está preparando o Sentinel-1 Next Generation para dar continuidade até meados
  da década de 2030.
  <https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Sentinel-1D_goes_live_a_milestone_for_Europe_s_radar_mission>
  <https://dataspace.copernicus.eu/news/2026-4-16-sentinel-1d-user-data-opening-17042026>
- Radar: enxerga através de nuvens e à noite. É isso que torna possível, sequer, o
  monitoramento de mineração em ambiente tropical — o óptico sozinho perde toda a estação
  chuvosa.

**Sentinel-2 (óptico MSI)**
- 13 bandas espectrais: quatro a 10 m, seis a 20 m, três a 60 m. Faixa de imageamento
  de 290 km.
- Revisita: 10 dias com um satélite, 5 dias com dois, 2–3 dias em latitudes médias.
- O Sentinel-2C foi lançado em 5 de setembro de 2024 e substituiu o 2A em 21 de janeiro de
  2025; o 2A voltou a operar em 13 de março de 2025 em órbita 36° defasada do 2B, formando
  uma constelação de três satélites; a campanha de extensão do 2A foi prorrogada até o final
  de 2026.
- L1C (topo da atmosfera) com cobertura global desde 2015; L2A (reflectância de superfície)
  é o produto pronto para análise.
  <https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel2.html>
  <https://dataspace.copernicus.eu/news/2026-5-15-sentinel-2a-extension-campaign-prolonged-until-end-2026>

**Copernicus DEM**
- GLO-30 (30 m) e GLO-90 (90 m) global, ~149 milhões de km²; EEA-10 (10 m) para 39 países
  europeus.
- Acurácia vertical absoluta <4 m (erro linear a 90%); relativa <2 m em declividades ≤20%,
  <4 m acima disso.
- GLO-30/GLO-90 gratuitos no mundo todo; EEA-10 restrito a categorias definidas de usuários.
  Citar <https://doi.org/10.5270/ESA-c5d3d65>. Acesso via Copernicus Browser, APIs, S3, OData.
  <https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM>
- Consequência: **a elevação global gratuita torna a estimativa volumétrica de mudança uma
  capacidade pública**, o que é o análogo aberto mais próximo dos produtos de volumetria por
  drone que os operadores compram.

**Alertas RADD de perturbação florestal**
- Universidade de Wageningen (Laboratory of Geo-Information Science and Remote Sensing),
  baseado em Sentinel-1, **10 m**, quase em tempo real, cobrindo América do Sul (13 países),
  América Central (6), África (25), Sudeste Asiático insular (5), Pacífico (1). **CC BY 4.0**.
  Citar Reiche et al. 2021, *Environ. Res. Lett.*, <https://doi.org/10.1088/1748-9326/abd0a8>.
  Distribuído pelo Global Forest Watch.
  <https://gee-community-catalog.org/projects/radd/>

### 5.9 Evidência e admissibilidade

- Muhammad, Alif Nurfakhri. "The Admissibility of Earth Observation Data in Legal
  Proceedings: A Closer Look Towards Data Imaging." *Indonesia Law Review*, vol. 11, n. 1,
  2021. Argumento: o caminho do dado bruto de observação da Terra até a informação analisada
  "requer um grau de manipulação", que é exatamente onde a autenticidade é contestada.
  Propõe a **captura de imagem de dados (data imaging) e auditoria digital** como os
  mecanismos que preservam a admissibilidade, e observa que não há arcabouço internacional
  consolidado.
  <https://scholarhub.ui.ac.id/ilrev/vol11/iss1/2/>
- Consequência de projeto para esta plataforma: todo produto derivado precisa carregar sua
  derivação completa — IDs dos grânulos de origem, linha de base de processamento, versão do
  algoritmo, parâmetros e um hash — ou é uma opinião, não uma evidência. Este é o requisito
  arquitetural mais importante de todos e o que mais costuma faltar em ferramentas cívicas de
  monitoramento.

### 5.10 Lista de vigilância de licenças de ferramentas (situação em 19/08/2026; reverificar antes de qualquer aquisição)

Seguras, bem governadas, apoiadas por fundações:
- QGIS — GPL-2.0-or-later; reconhecido como Bem Público Digital (fev. de 2025).
- GDAL/OGR — estilo MIT/X; projeto OSGeo.
- PostgreSQL (Licença PostgreSQL) + PostGIS (GPL-2.0-or-later).
- GeoServer (GPL-2.0), GeoNode (GPL-3.0), pygeoapi (MIT), CKAN (AGPL-3.0).
- Ecossistema STAC: stac-spec, pystac, pystac-client, stac-fastapi, pgstac —
  Apache-2.0/MIT.
- Open Data Cube (Apache-2.0); openEO (Apache-2.0); eodag (Apache-2.0).
- rasterio (BSD-3), rioxarray (Apache-2.0), xarray (Apache-2.0), dask (BSD-3),
  scikit-image / scikit-learn (BSD-3), numpy (BSD-3).
- ESA SNAP (GPL-3.0); MintPy (GPL-3.0); LiCSBAS (GPL-3.0); ISCE2 (Apache-2.0);
  Orfeo ToolBox (Apache-2.0).
- TorchGeo (MIT), leafmap / segment-geospatial (MIT), TiTiler (MIT).
- MapLibre GL JS (BSD-3), deck.gl (MIT), Apache Airflow / Superset (Apache-2.0),
  DuckDB (MIT), Keycloak (Apache-2.0).

Não construir sobre, sem uma segunda análise:
- **MinIO** — edição comunitária arquivada / em modo de manutenção depois que a versão AGPL
  teve funcionalidades retiradas (2025–2026). Usar SeaweedFS (Apache-2.0), Garage
  (AGPL-3.0), Ceph RGW, ou o próprio serviço S3 da nuvem soberana em seu lugar.
- Grafana (AGPL-3.0 desde 2021) e Metabase OSS (AGPL-3.0) são adequados para *executar*, mas
  a AGPL tem implicações para aquisições caso a instituição os modifique e os exponha como
  serviço.
- O Sen2Cor é software gratuito da ESA, mas não tem licença de código aberto aprovada pela
  OSI — preferir consumir diretamente os produtos L2A em vez de depender de processamento
  local com o Sen2Cor.

Contexto geral de tendência: o relicenciamento como source-available (BSL, SSPL, FSL) tem
continuado a afetar projetos de infraestrutura; uma plataforma do setor público deve fixar-se
em licenças aprovadas pela OSI e manter uma via de saída para cada dependência.

## 6 Protótipo de SIG

### 6.1 O que o protótipo de mapa acrescenta

Tudo o que veio antes é um espelho, uma camada de tradução e uma máquina de devido processo.
O que faltava, no papel, era uma única superfície onde a geografia de um caso e sua trilha
documental entre órgãos aparecessem lado a lado — onde um fiscal, um promotor ou um
jornalista possa clicar num sítio e ver não apenas onde ele fica, mas quais registros já o
conhecem, sob qual número, e se concordam entre si.

O `map.html` é um protótipo funcional dessa superfície, construído sobre os mesmos
quatro sítios de demonstração usados ao longo deste documento. Ele é entregue como um arquivo
separado, e não incorporado a este relatório, por uma razão técnica específica: um mapa ao
vivo precisa buscar blocos de mapa (tiles) de um servidor pela rede, e a página em sandbox na
qual este próprio relatório é publicado não pode fazer esse tipo de requisição. Aberto como
arquivo próprio, o mapa não tem essa restrição.

Uma nota sobre a própria camada de base: o protótipo usa os tiles gratuitos Positron/Dark
Matter da CARTO (construídos a partir de dados do OpenStreetMap), em vez de buscar
diretamente em `tile.openstreetmap.org`. Os servidores de tiles do próprio OpenStreetMap são
infraestrutura mantida por voluntários, com uma política de uso que bloqueia requisições sem
um cabeçalho `Referer` válido — exatamente o que um navegador envia, ou deixa de enviar,
quando uma página é aberta diretamente do disco (`file://`) em vez de servida via
`http(s)://`. Passar pelo CDN da CARTO, que não aplica essa verificação, mantém o mapa
utilizável seja como for que o arquivo seja aberto, enquanto os dados de mapa subjacentes
continuam sendo do OpenStreetMap.

### 6.2 O que está no mapa

Uma camada de base da CARTO (clara em tema claro, escura em tema escuro), construída a
partir de dados do OpenStreetMap, os quatro sítios plotados em suas coordenadas
(sintéticas), cada um com seu polígono licenciado, sua área antropizada detectada e — onde
pertinente — o polígono da área protegida com a qual se sobrepõe. Clicar num sítio abre um
painel com:

- As coordenadas geográficas centrais (latitude/longitude WGS84, mais o fuso UTM em que o
  pipeline efetivamente calcula).
- A **cadeia de referências entre órgãos** — para um sítio brasileiro, isso significa, lado a
  lado: o número do processo minerário da ANM (SIGMINE/Cadastro Mineiro), o número do
  processo de licenciamento ambiental do IBAMA onde a atividade exige licenciamento federal, a
  referência de unidade de conservação do ICMBio onde o sítio se sobrepõe a uma, qualquer
  processo aberto da FUNAI onde a área antropizada toca uma Terra Indígena, a referência de
  assentamento do INCRA onde o sítio está sobre ou próximo de um assentamento de reforma
  agrária, e a referência da ANA (recursos hídricos) onde há uma estrutura de rejeitos
  envolvida. Nem todo sítio tem entrada em todo registro — essa ausência é mostrada, não
  ocultada, exatamente como o resto desta arquitetura trata uma lacuna de observação como um
  achado, e não como um nulo.
- A **trilha de evidência** — a mesma cadeia de custódia que a camada de dossiê já produz,
  mostrada como um caminho curto da detecção ao registro: cena de satélite → saída do detector
  → `EvidenceManifest` selado (com o hash exibido) → cruzamento cadastral → as entradas de
  registro específicas acima → o estado atual de devido processo do caso. É o ponto
  cibernético tornado concreto: cada comunicação da cadeia é mostrada, não afirmada, de modo
  que um leitor possa seguir a trilha até sua fonte, em vez de aceitar a conclusão por fé.
- Um controle de **exportação** que produz um CSV ou GeoJSON contendo, por sítio: as
  coordenadas geográficas, o ID do caso e todos os identificadores entre órgãos acima — para
  que uma parte interessada (um Ministério Público, um jornalista, o representante legal de
  uma comunidade afetada) possa levar os números de referência e consultar diretamente ANM,
  IBAMA, ICMBio, FUNAI, INCRA ou ANA, em vez de confiar num número que este sistema apenas
  afirma.

### 6.3 O que é sintético, e dito como tal

Todo número de registro no mapa é fabricado para o protótipo — claramente identificado como
tal, no mesmo espírito da recusa deste projeto, em todo o resto, de deixar evidência simulada
passar por real. Uma implantação em produção substitui isso por consultas ao vivo aos
registros de cada órgão (a maioria dos quais — SIGMINE, o Cadastro Mineiro, o SIGBM — já está
catalogada em `03-catalogues.xlsx`); IBAMA, ICMBio, FUNAI e INCRA ainda não têm registros
abertos e disponíveis em lote da mesma qualidade que a ANM, o que é, em si, um achado que vale
a pena declarar com todas as letras: a cadeia de referências entre órgãos só é tão forte
quanto o registro mais fraco dentro dela, e hoje esse não é o da ANM.

## 7 Referências

Numeradas na ordem da primeira citação, em formato numérico ISO 690. As marcas entre colchetes como **[1]** nos §§2 e 5 acima apontam para cá.

[1] CATERPILLAR INC. "Caterpillar Bolsters Mining Technology Solutions with RPMGlobal Acquisition." *Caterpillar Newsroom*, 2026. Disponível em: www.caterpillar.com/en/news/corporate-press-releases/h/rpm-global-acquisition.html. [Acesso em: 19 ago. 2026].

[2] COPERNICUS DATA SPACE ECOSYSTEM. "APIs." *Copernicus Data Space Ecosystem Documentation*. Disponível em: documentation.dataspace.copernicus.eu/APIs.html. [Acesso em: 19 ago. 2026].

[3] COPERNICUS DATA SPACE ECOSYSTEM. "Quotas and Limitations." *Copernicus Data Space Ecosystem Documentation*. Disponível em: documentation.dataspace.copernicus.eu/Quotas.html. [Acesso em: 19 ago. 2026].

[4] COPERNICUS DATA SPACE ECOSYSTEM. "Sentinel-2." *Copernicus Data Space Ecosystem Documentation*. Disponível em: documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel2.html. [Acesso em: 19 ago. 2026].

[5] COPERNICUS DATA SPACE ECOSYSTEM. "Sentinel-1D User Data Opening from 17/04/2026." *Copernicus Data Space Ecosystem*, 16 Apr. 2026. Disponível em: dataspace.copernicus.eu/news/2026-4-16-sentinel-1d-user-data-opening-17042026. [Acesso em: 19 ago. 2026].

[6] EARTHRISE MEDIA. *mining-detector*. GitHub. Disponível em: github.com/earthrise-media/mining-detector. [Acesso em: 19 ago. 2026].

[7] EARTH GENOME. *Amazon Mining Watch*. Disponível em: amazonminingwatch.org/en. [Acesso em: 19 ago. 2026].

[8] EUROPEAN COMMISSION. *Commission Implementing Regulation (EU) 2023/138 of 21 December 2022 Laying Down a List of Specific High-Value Datasets and the Arrangements for Their Publication and Re-use*. EUR-Lex. Disponível em: eur-lex.europa.eu/eli/reg_impl/2023/138/oj/eng. [Acesso em: 19 ago. 2026].

[9] EUROPEAN COMMISSION. "Aarhus Convention." *Environment*. Disponível em: environment.ec.europa.eu/law-and-governance/aarhus_en. [Acesso em: 19 ago. 2026].

[10] EUROPEAN ENVIRONMENT AGENCY. "European Ground Motion Service." *Copernicus Land Monitoring Service*. Disponível em: land.copernicus.eu/en/products/european-ground-motion-service. [Acesso em: 19 ago. 2026].

[11] EUROPEAN SPACE AGENCY. "Sentinel-1D Goes Live: A Milestone for Europe's Radar Mission." *ESA*, 2026. Disponível em: www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Sentinel-1D_goes_live_a_milestone_for_Europe_s_radar_mission. [Acesso em: 19 ago. 2026].

[12] EXTRACTIVE INDUSTRIES TRANSPARENCY INITIATIVE. *EITI Standard 2023*. EITI International Secretariat, 2023. Disponível em: eiti.org/sites/default/files/2023-06/2023%20EITI%20Standard.pdf. [Acesso em: 19 ago. 2026].

[13] GLOBAL ENERGY MONITOR. "Global Coal Mine Tracker: Methodology." Disponível em: globalenergymonitor.org/projects/global-coal-mine-tracker/methodology/. [Acesso em: 19 ago. 2026].

[14] GRID-ARENDAL. "About the Global Tailings Portal." *Global Tailings Portal*. Disponível em: tailing.grida.no/about. [Acesso em: 19 ago. 2026].

[15] JASANSKY, Simon, et al. "An Open Database on Global Coal and Metal Mine Production." *Scientific Data*, vol. 10, 2023. DOI: 10.1038/s41597-023-01965-y.

[16] MAPBIOMAS BRASIL. "Amazônia Concentra Mais de 90% do Garimpo no Brasil." 22 Sept. 2023. Disponível em: brasil.mapbiomas.org/en/2023/09/22/916-da-area-garimpada-no-brasil-ficam-no-bioma-amazonia/. [Acesso em: 19 ago. 2026].

[17] MAPBIOMAS BRASIL. "77% do Garimpo na Amazônia Está a Menos de 500 Metros da Água." 19 Apr. 2024. Disponível em: brasil.mapbiomas.org/en/2024/04/19/77-do-garimpo-na-amazonia-esta-a-menos-de-500-metros-da-agua/. [Acesso em: 19 ago. 2026].

[18] MAUS, Victor, et al. "An Update on Global Mining Land Use." *Scientific Data*, vol. 9, 2022. DOI: 10.1038/s41597-022-01547-4. Dataset: PANGAEA, DOI: 10.1594/PANGAEA.942325.

[19] MINES AND MONEY. "Global Mining Tech 50: The Top 50 Global Mining/Metals Tech Players." *IMARC*. Disponível em: minesandmoney.com/news/industry/global-mining-tech-50-the-top-50-global-mining-metals-tech-players. [Acesso em: 19 ago. 2026].

[20] MINING TECHNOLOGY. "Weir Completes Acquisition of Micromine." *Mining Technology*, 2025. Disponível em: www.mining-technology.com/news/weir-micromine-acquisition/. [Acesso em: 19 ago. 2026].

[21] MUHAMMAD, Alif Nurfakhri. "The Admissibility of Earth Observation Data in Legal Proceedings: A Closer Look Towards Data Imaging." *Indonesia Law Review*, vol. 11, no. 1, 2021. Disponível em: scholarhub.ui.ac.id/ilrev/vol11/iss1/2/. [Acesso em: 19 ago. 2026].

[22] QGIS PROJECT. "QGIS Recognized as Digital Public Good." *QGIS Blog*, 8 Feb. 2025. Disponível em: blog.qgis.org/2025/02/08/qgis-recognized-as-digital-public-good/. [Acesso em: 19 ago. 2026].

[23] REICHE, Johannes, et al. "Forest Disturbance Alerts for the Congo Basin Using Sentinel-1." *Environmental Research Letters*, vol. 16, no. 2, 2021. DOI: 10.1088/1748-9326/abd0a8.

[24] RIKIMARU, A., ROY, P. S., MIYATAKE, S. "Tropical Forest Cover Density Mapping." *Tropical Ecology*, vol. 43, no. 1, 2002, pp. 39-47.

[25] ROUSE, J. W., et al. "Monitoring Vegetation Systems in the Great Plains with ERTS." *Third ERTS Symposium*, NASA SP-351, 1974, pp. 309-317.

[26] SKYTRUTH. "Technology." Disponível em: skytruth.org/about/technology/. [Acesso em: 19 ago. 2026].

[27] SOURCEFORGE. "Mining Software in Europe." Disponível em: sourceforge.net/software/mining/europe/. [Acesso em: 19 ago. 2026].

[28] TRIBUNAL DE CONTAS DA UNIÃO. "TCU Cobra Agência de Mineração por Sonegação de R$ 16 bi em Impostos." Reported in *Agência Brasil*, 15 Oct. 2024. Disponível em: agenciabrasil.ebc.com.br/geral/noticia/2024-10/tcu-cobra-anm-por-sonegacao-de-rs-16-bi-de-mineradoras-em-impostos. [Acesso em: 19 ago. 2026].

[29] AGÊNCIA NACIONAL DE MINERAÇÃO. "Bases de Dados." *Dados Abertos*. Disponível em: www.gov.br/anm/pt-br/acesso-a-informacao/dados-abertos/bases-de-dados. [Acesso em: 19 ago. 2026].

[30] AGÊNCIA NACIONAL DE MINERAÇÃO. "Boletim Mensal de Barragens de Mineração — Outubro 2025." Disponível em: www.gov.br/anm/pt-br/assuntos/barragens/boletim-de-barragens-de-mineracao/boletim-mensal-outubro-2025. [Acesso em: 19 ago. 2026].

[31] XU, Hanqiu. "Modification of Normalised Difference Water Index (NDWI) to Enhance Open Water Features in Remotely Sensed Imagery." *International Journal of Remote Sensing*, vol. 27, no. 14, 2006, pp. 3025-3033.
