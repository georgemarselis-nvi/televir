# TELE-Vir Repository: Development Report (May 2025 – May 2026)

**Date:** 2026-05-22  
**Period:** 23 May 2025 – 21 May 2026  
**Total commits:** 139  
**Contributors:** 1 (SantosJGND)  
**Active branches:** `install-stdl`, `develop`, `bwa-filter`, `expand_organisms`, `merge_safe`, `metaphlen`, `main`

---

## Phase 1: Stabilization (May – Jun 2025) — 9 commits

Bug fixes and maintenance to the initial working version:

- Kaiju download and Voyager checks fixed
- MetaPhlAn database install corrected
- `xopen` replaced with `bgzip` for compression
- Kraken2 viral changed to build-from-construct instead of download
- Code linting

*A ~9-month gap followed (Jun 2025 – Mar 2026).*

---

## Phase 2: Docker & Architecture Overhaul (Mar 13–27, 2026) — ~40 commits

A major rewrite of the entire installation system.

### Docker transformation
- Dockerfile and `entrypoint.sh` introduced
- Standalone deployment scripts removed; Docker became the primary deployment method
- Container commands: `move`, `install`, `update`, `check`, `status`, `sources`

### SQLite registration system
- `utility_local.db` introduced to track all installed databases and software
- Standardized DB registration table with versions, descriptions, and paths
- SQLAlchemy engine with proper connection management
- Automatic table reset on startup; description columns added

### Centralized sources management
- `sources.yaml` became the single source of truth (version `1.0`)
- `sources_cli.py` CLI tool for querying available sources
- Installation classes aligned with YAML structure
- All database download control moved to `sources.yaml`

### GUI status dashboard
- `televir_status.py` with Tkinter-based graphical interface
- Two-panel layout: Databases and Software tables with name, category, available/installed columns
- Version display and "Check Status" button for live refresh
- Software checks integration

---

## Phase 3: Database & Metadata Expansion (Apr 2026) — ~50 commits

### Accession database
- Local SQLite accession DB for taxid metadata storage
- Nucleotide and protein taxid parsing with SQL persistence
- Automatic NCBI taxdump download for taxonomy resolution
- Optimized metadata processing for both protein and nucleotide data

### BLAST integration
- BLAST database indexes created for all protein and nucleotide databases
- FVE (Fast Virome Explorer) BLAST databases registered in the SQL table

### Host genomes re-introduced
- Host installation restored as part of the standard pipeline
- Better file handling for host and protein downloads
- File compression fix for host files

### Unified download & update
- `file_dl` function standardized all file downloads
- Integrity verification of downloaded sequence databases
- Update mode made uniform: removes old data, re-downloads, re-registers
- 16S rRNA databases (RefSeq, SILVA) installed via unified pipeline
- RefSeq install config structure merged

---

## Phase 4: Centrifuge & Kraken2 Rework (Apr 29 – May 11, 2026) — ~25 commits

### Prebuilt indices
- Support for user-provided pre-built Centrifuge and Kraken2 indices
- Paths configured in `sources.yaml` under `prebuilt_indices`
- Centrifuge: expects `.1.cf`, `.2.cf` index files
- Kraken2: expects `taxo.k2d` in the database directory
- Prebuilt path made dependent only on `sources.yaml`

### Centrifuge overhaul
- Deprecated legacy `centrifuge-download` Perl script
- Switched to git-based Centrifuge install from source
- Custom database download and rename logic
- Added Centrifuge standard 2016 database; set default to true
- `install_config.py` added to entrypoint file copies

### Kraken2 updates
- Database links updated
- Bacteria database support added; standard DB installed when bacteria requested
- Improved custom database handling
- KrakenUniq database install registered

---

## Phase 5: Recent Developments (May 13–21, 2026) — ~15 commits

- **Assembly environment** — dedicated conda YAML file and environment configuration added
- **CLARK** — reinstated and updated
- **Virosaurus** — download versions and filenames fixed; CLARK enabled
- **FVE databases** — limited to unsplit reference files
- **Dynamic request sequences** — configurable via `sources.yaml` (path + description); registered in `fastas["nuc"]` as `requests_<basename>`
- **Accession ID parsing** — reverted to legacy method
- **Update defaults** — nucleotide updates disabled by default; traditional update mode used

---

## Summary

Over the past year, TELE-Vir transformed from a standalone Python CLI installer into a **Docker-centric deployment system** with:

| Area | Change |
|------|--------|
| Deployment | Standalone → Docker-based (`move`/`install`/`update`/`check`) |
| Configuration | Hardcoded → Centralized `sources.yaml` |
| Tracking | None → SQLite registration (`utility_local.db`) |
| UI | CLI-only → Tkinter GUI status dashboard |
| Centrifuge | Perl script → Git source + custom DB download |
| Metadata | None → Local accession DB with taxid resolution |
| Extensibility | Code changes required → YAML-driven database addition |
