# HeatOps Product Requirements

## Product statement

HeatOps helps municipal response teams allocate temporary cooling resources during urban heat events. It combines hyperlocal heat intelligence with exposure, vulnerability, accessibility, and budget constraints to produce an explainable intervention plan.

## Problem

Temperature dashboards describe hazards but do not decide how scarce resources should be allocated. The hottest location is not automatically the highest-priority location: duration, population exposure, vulnerability, existing cooling access, and travel distance also matter.

## Primary user

A municipal heat-response coordinator preparing an operational plan for the next day or heat-event window.

## Core user story

As a response coordinator, I want to specify an area, time window, available resource count, and policy priority so that I receive a transparent placement plan and can compare its estimated coverage with a naive baseline.

## Inputs

- area of interest;
- heat snapshot, exceedance, and persistence;
- population or activity exposure;
- vulnerability indicators;
- existing cooling access;
- candidate intervention sites;
- intervention budget or count.

## Outputs

- inspectable risk layer;
- selected temporary-resource locations;
- estimated high-risk exposure covered;
- comparison against a baseline placement;
- explanation of each selection;
- concise operational action brief;
- limitations and uncertainty notes.

## Success criteria

1. The complete demo runs even if the external API is temporarily unavailable.
2. Every displayed metric has a defined unit and provenance.
3. The optimizer produces deterministic results for identical inputs.
4. A user can change the budget and understand why the plan changes.
5. The product never describes synthetic data as real observations.
6. The final demo completes its central story in under three minutes.

## Non-goals for the hackathon

- clinical heat-illness prediction;
- ambulance dispatch;
- causal prediction of cooling from trees or reflective materials;
- real-time tracking of identifiable individuals;
- replacing municipal emergency management;
- supporting every possible intervention type.

