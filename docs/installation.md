# Installation

## Requirements

- Python 3.8+
- A working `z3-solver` installation (installed as Python dependency)

## Install from source

```bash
pip install .
```

## Optional data considerations

MCC can work with online lookups and optional local database files. Local files
improve reproducibility and speed for repeated runs.

- Default data folder: `./data`
- Configure via `data_path=...`
- BioCyc local data can be supplied via `biocyc_path=...`

## Verify installation

```python
from MCC import MassChargeCuration
```

If this import succeeds, the package is available.
