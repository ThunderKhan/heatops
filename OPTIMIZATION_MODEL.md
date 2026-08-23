# HeatOps Placement Optimization

## Decision problem

Given a set of risk cells, candidate temporary-resource sites, a coverage radius, and a resource limit `k`, select at most `k` sites that maximize covered risk burden.

For risk cell `i` and candidate site `j`:

- `r_i` is the cell's continuous HeatOps risk score;
- `a_ij = 1` when site `j` is within the coverage radius of cell `i`;
- `x_j = 1` when candidate `j` is selected;
- `z_i = 1` when at least one selected candidate covers cell `i`.

The maximum-coverage formulation is:

\[
\max \sum_i r_i z_i
\]

subject to:

\[
\sum_j x_j \leq k
\]

and:

\[
z_i \leq \sum_j a_{ij}x_j
\]

## Milestone 3 solver

The implementation uses deterministic greedy weighted maximum coverage:

1. Begin with no covered cells.
2. Calculate every unselected site's marginal uncovered risk.
3. Select the site with the greatest marginal gain.
4. Repeat until `k` sites are selected or no positive gain remains.

For monotone maximum coverage, this algorithm has the classic `1 - 1/e` approximation guarantee relative to the optimum. Ties are resolved by stable site identifier, so identical inputs produce identical plans.

## Baseline

The baseline selects the `k` cells with the highest individual risk scores without considering overlapping coverage. It represents a plausible but spatially naive policy.

The API evaluates both plans. A baseline guard ensures the returned optimized plan never covers less risk than the baseline on the same inputs.

## Coverage

Distances between candidate points and risk-cell centroids are calculated using the haversine formula. A cell is considered covered when its centroid lies within the configured radius.

## Reported metrics

- total risk burden;
- covered risk burden;
- covered-risk percentage;
- covered cell count;
- selected sites and marginal gain;
- improvement over baseline in percentage points.

These values measure modeled prioritization coverage—not population served, illnesses prevented, or lives saved.

## Current limitations

- Candidate sites are synthetic cell centroids, not field-verified feasible locations.
- Straight-line distance does not represent walking time, barriers, or road access.
- Every temporary resource currently has identical capacity and cost.
- A cell is treated as covered through its centroid rather than its full area.
- The greedy solver is approximate, though deterministic and bounded.
- Risk scores are prioritization weights, not calibrated health outcomes.

