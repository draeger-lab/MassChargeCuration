# Overview

MassChargeCuration (MCC) is a Python package for automated mass and charge
curation in genome-scale metabolic models (GEMs), introduced in
{cite}`mostolizadeh2026mcc`.

## What MCC does

MCC combines database evidence and constraint solving to:

1. Gather candidate formula/charge assignments for metabolites.
2. Build a satisfiability model of metabolite assignments and reaction balance constraints.
3. Resolve unsatisfiable cores to isolate reactions that cannot be balanced together.
4. Optimize remaining assignments to adhere to the original model where possible.
5. Produce reports that summarize changed assignments and remaining unbalanced reactions.

## Key capabilities

- Accepts models as SBML path, `libsbml.Model`, or `cobra.Model`.
- Consolidates assignments from multiple resources.
- Handles partially known compounds via wildcard-aware formula handling.
- Detects pseudo reactions (exchange/sink/growth) and excludes them from balancing.
- Updates model `notes` fields with curation information and provides tabular/visual reports.

## Package structure

- `MCC.Balancing`: SAT-based balancing and optimization pipeline.
- `MCC.DataCollection`: database integration and identifier propagation.
- `MCC.ModelInterface`: adapters for libSBML and COBRA models.
- `MCC.ReportGeneration`: metabolite/reaction tables and visual summaries.
- `MCC.core`: core domain objects (`Formula`, `Metabolite`, `Reaction`).
- `MCC.util`: helper functions for balancing workflow support.

## Scope and assumptions

MCC targets SBML-based flux-balance models and related metabolic
reconstructions where metabolites have formulae/charges and reactions use
stoichiometric coefficients. Quality depends on both model annotations and
available database evidence.

## Study context

In the study, MCC was used in curation of
*Corynebacterium tuberculostearicum* DSM 44922 and reports simulation of growth
in synthetic nasal medium 3 (SNM3), resulting in model `iCTUB2024RM`
{cite}`mostolizadeh2026mcc`.
