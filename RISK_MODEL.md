# HeatOps Risk Model

## Purpose

The score ranks grid cells for temporary heat-response resources. It is a transparent prioritization proxy, not a prediction of illness, mortality, or individual medical risk.

## Components

All components are normalized to the closed interval `[0, 1]`.

| Symbol | Component | Interpretation |
|---|---|---|
| `H` | Heat hazard | Normalized snapshot, exceedance, or persistence |
| `E` | Exposure | Relative presence of people or relevant assets |
| `V` | Vulnerability | Relative sensitivity and socioeconomic vulnerability |
| `C` | Cooling access | Existing access to cooling resources |
| `A` | Lack of access | `1 - C` |

The context score is:

\[
Q_i = w_E E_i + w_V V_i + w_A(1-C_i)
\]

The final risk score is:

\[
R_i = H_i Q_i
\]

with:

\[
w_E+w_V+w_A=1
\]

Default weights are `0.35`, `0.40`, and `0.25` respectively.

This formulation makes heat a necessary gate while keeping the social and infrastructure contributions additive and inspectable. It also prevents a single zero-valued contextual component from erasing all other evidence.

## Hazard normalization

During the mock-data milestone:

- snapshot temperature maps from `threshold - 5°C` to `threshold + 5°C`;
- exceedance maps from `0` to `12` hours;
- persistence maps from `0` to `8` continuous hours.

Values outside each range are clipped. These development scales are explicit assumptions and must be reviewed against FortyGuard output distributions when real data becomes available.

## Classification

| Score | Level |
|---:|---|
| `< 0.25` | Low |
| `0.25–<0.50` | Moderate |
| `0.50–<0.75` | High |
| `>= 0.75` | Critical |

The continuous score—not the label—is used by future optimization.

## Explainability

Every feature contains:

- the original heat measurement and unit;
- normalized hazard;
- exposure, vulnerability, cooling access, and lack of access;
- the contribution of every weighted component;
- final score and classification;
- heat and context provenance;
- a synthetic-data flag.

## Limitations

- Synthetic context values are only for development and demonstrations.
- Normalization is sensitive to chosen bounds.
- Default weights encode a policy preference and are not universal scientific constants.
- A high score identifies priority for assessment; it does not establish causality.
- Real deployments require locally validated demographic, mobility, and infrastructure data.

