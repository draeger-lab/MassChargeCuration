# Workflow

This page describes the internal balancing workflow implemented by
`MCC.Balancing.MassChargeCuration` as presented in
{cite}`mostolizadeh2026mcc`.

## Pipeline stages

1. Data collection.
   Gather and sanitize candidate metabolite formula/charge assignments from
   databases.
2. SMT encoding.
   Encode metabolite assignment constraints plus reaction balancing constraints
   (non-hydrogen mass balance and hydrogen/charge coupling).
3. Determine a balanceable SAT core.
   Remove conflicting reactions until a satisfiable balanced core is found.
4. Reintroduce unsatisfiable reactions heuristically.
   Re-test removed reactions with priority rules to recover as many as possible
   while maintaining consistency.
5. Optimize assignments.
   Prefer adherence to original model assignments when possible and choose
   detailed/plausible assignments under balance constraints.
6. Post-processing.
   Handle unconstrained formulas, choose hydrogen/charge representations, and
   adjust protons for full mass-balance consistency.

## Notes on scope

MCC addresses mass/charge curation as one key step in GEM reconstruction. It is
not a complete replacement for all reconstruction and validation steps required
for full model development.

## Pseudo reactions

Pseudo reactions are excluded from strict balancing, including:

- reactions with only reactants or only products (exchange/sink style)
- reactions marked with SBO term 629
- reactions with "growth" in the reaction name

## Main entrypoint

```{eval-rst}
.. autoclass:: MCC.Balancing.MCC.MassChargeCuration
   :members:
   :undoc-members:
   :show-inheritance:
```

## Inputs and tuning parameters

Important constructor arguments:

- `model`: SBML path, `libsbml.Model`, or `cobra.Model`
- `data_collector`: optional preconfigured `DataCollector`
- `data_path`: directory for local cache/downloads
- `fixed_assignments`: lock metabolite assignments (`id -> (formula, charge)`)
- `fixed_reactions`: prioritize preserving specific reactions in unsat handling
- `run_optimization`: enable/disable post-SAT optimization stages
- `cache_ids`: planned id cache support (currently limited)

## Outputs

After construction, the curator object exposes:

- curated `model_interface`
- `unbalancable_reactions`
- `unknown_metabolites`
- `reaction_reasons`
- `assignments`
- report generators (`generate_*_report`)
