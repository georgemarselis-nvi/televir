## Metagenomic Prep

Scripts to install metagenomic databases for the software used in benchmarking
the metagenomics installation pipeline. 

### Instructions: 

#### Environmnent

Install and activate the `mngsbench_install.yml` environment provided in the root directory. 

####  Configuration

In the INSTALL_PARAMS dictionary, provide ROOT as the root directory for sequence and software database installation. Within the INSTALL_PARAMS > ENVSDIR dictionary, make sure that SOURCE points to an existing conda sh file and ROOT points to the directory where environments will be installed (typically within $HOME, but not necessarily). 

Verify that these values correspond to those in the ENVS_PARAMS dictionary for the corresponding keys. 

The `INSTALL_PARAMS["ENVSDIR"]` dict maps software names (e.g., "kraken2", "centrifuge") to environment subdirectories. The `ENVS_PARAMS["ENVS"]` dict maps those subdirectories to yaml files (e.g., `HD.yml`, `Krk2.yml`). This dual mapping enables binary presence verification in `televir_status.py`. 

#### Database Configuration

Database installation is now controlled via `sources.yaml`. The `install_config.py` file 
only handles hosts and software-specific flags (kraken2, centrifuge, etc.).

**Configuration Options per Database:**

| Field | Values | Description |
|-------|--------|-------------|
| `install` | `true`/`false` | Enable/disable download |
| `install_types` | `["filter"]`, `["prot"]`, `["nuc"]`, `["host"]` | Which indices to build |
| `db_key` | `filter`, `prot`, `nuc`, `host` | Storage location (optional, inferred) |

**Categories in sources.yaml:**

| Category | Description | install_types |
|----------|-------------|---------------|
| `ribosomal_rna` | 16S rRNA databases | `["filter"]` |
| `protein` | UniRef, SwissProt, RVDB | `["prot"]` |
| `nucleotide` | Virosaurus | `["nuc"]` |
| `refseq` | RefSeq viral/bacterial protein/genome | `["prot"]` or `["nuc"]` |

**Example - Enable SILVA 16S and build BWA index:**

```yaml
databases:
  ribosomal_rna:
    silva_16s:
      url: "https://www.arb-silva.de/..."
      install: true
      install_types: ["filter"]
      db_key: "filter"
```

**Default Values (matching previous install_config.py):**

- `refseq_viral_protein`: install=true, install_types=["prot"]
- `refseq_viral_genome`: install=true, install_types=["nuc"]
- `virosaurus`: install=true, install_types=["nuc"]
- `silva_16s`, `refseq_16s`: install=true, install_types=["filter"]
- `swissprot`, `rvdb`, etc.: install=false

**Adding New Databases:**

Simply add an entry to the appropriate category in `sources.yaml`. The installation 
code automatically discovers and processes all enabled databases - no code changes needed.

#### Deployment

The main_install.py script allows for four boolean tags:

- --envs: installs environments; 
- --seqdl: downloads reference sequence databases; 
- --soft: generates software databases. 
- --nanopore: if given, will also install software specific to 3d generation sequencing technologies. 

finally, main_install also accepts the argument `--taxdump`. This should be the argument to a local instance of ncbi's taxdump.tar.gz. if given, the software will use this to rescue corruped files on download for those software that require it. Recommended when running locally. 

**warning** when choosing `--nanopore`, installation of the software deSAMBA requires the installation of some dependencies using sudo. Verify that you have root priviledges.

Run
`
python main_install.py -h 
`
for detail. 