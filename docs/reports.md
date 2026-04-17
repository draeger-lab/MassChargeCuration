# Reports

MCC provides three report outputs from a completed curation run for comparing
draft and curated assignments {cite}`mostolizadeh2026mcc`.

## Metabolite report

`generate_metabolite_report()` returns a `pandas.DataFrame` with curated and
previous assignments, inferred reasoning, and similarity categories.

Key columns include:

- `Determined Formula`, `Determined Charge`
- `Previous Formula`, `Previous Charge`
- `Inferrence Type` (`Clean`, `Inferred`, `Unconstrained`)
- `Reasoning`
- `Similarity` (`Same`, `Proton Diff`, `Diff`)

These categories use the report terminology defined in
{cite}`mostolizadeh2026mcc`.

Write to CSV by passing `filename`.

## Reaction report

`generate_reaction_report()` returns unbalanced reactions after curation,
including imbalanced type, possible reasons, shared metabolites, and
mass/charge differences.

The optional `proton_threshold` controls whether high proton adjustments are
included as notable entries.

## Visual report

`generate_visual_report()` creates a summary donut chart comparing metabolite
assignment classes and similarity to original assignments.

If `filename` is provided, the plot is written as PNG.

In the case study, this visualization summarizes metabolite curation outcomes and
their relation to previously imbalanced reactions {cite}`mostolizadeh2026mcc`.

## Example

```python
reaction_df = curator.generate_reaction_report("model_reactions")
metabolite_df = curator.generate_metabolite_report("model_metabolites")
fig = curator.generate_visual_report("model_visual")
```
