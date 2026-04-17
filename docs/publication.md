# Study Summary

This project documents the method and outcomes published in
{cite}`mostolizadeh2026mcc`.

## What We Introduced

In the study, we introduced MCC as a Python package for automated mass and
charge curation in genome-scale metabolic models. MCC consolidates metabolite
formula/charge candidates from multiple resources, applies SMT-based balancing,
and updates model information with traceable curation results.

## Algorithm in MCC

Our workflow is implemented as six stages:

1. Data collection and sanitization of candidate formula/charge assignments.
2. SMT encoding of metabolite assignments and reaction balancing constraints.
3. Identification of a balanceable SAT core.
4. Heuristic reintroduction of unsatisfiable reactions.
5. Optimization of assignments under balance constraints.
6. Post-processing for unconstrained formulas and proton/charge representation.

## Report Outputs

MCC produces the same report semantics used in the manuscript:

- Metabolite inference types: `Clean`, `Inferred`, `Unconstrained`.
- Similarity categories: `Same`, `Proton Diff`, `Diff`.
- Reaction report fields: imbalanced type, reason, shared metabolites,
  mass difference, and charge difference.

## Case Study in The Paper

In the study, MCC was applied to *C. tuberculostearicum* DSM 44922 and curated model
`iCTUB2024RM`, including growth simulations in SNM3 conditions. In the
visualization example reported in the manuscript, metabolite formulas were
compared for 42 of 109 initially imbalanced reactions in less than 1,200 s.

These numeric outcomes come from this study and provide a reference point for
curated GEM workflows.
