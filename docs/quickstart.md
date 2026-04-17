# Quickstart

## Minimal usage

```python
import cobra
from MCC import MassChargeCuration

model = cobra.io.read_sbml_model("path/to/model.xml")
curator = MassChargeCuration(model, update_ids=True)
```

This constructs the balancing pipeline and updates metabolite assignments in the
internal model representation.

To persist curated assignments back to SBML, write via the model interface:

```python
curator.model_interface.write_model("curated_model.xml")
```

## With explicit data directories

```python
import cobra
from MCC import MassChargeCuration

model = cobra.io.read_sbml_model("path/to/model.xml")
curator = MassChargeCuration(
    model,
    update_ids=True,
    data_path="../database_path",
    biocyc_path="../data/25.1/data",
)
```

## Generate reports

```python
metabolite_df = curator.generate_metabolite_report("my_model_metabolites")
reaction_df = curator.generate_reaction_report("my_model_reactions")
curator.generate_visual_report("my_model_visual")
```

## Inspect uncertain assignments

```python
import pandas as pd

df = curator.generate_metabolite_report()
pd.set_option("display.max_rows", None)

# Assignments inferred without direct database support
inferred = df[df["Inferrence Type"] != "Clean"]

# Assignments different from the original model
changed = df[df["Similarity"] != "Same"]
```
