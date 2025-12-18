# RedRun

RedRun is a deterministic CI failure analysis tool that parses raw build logs from failed CI runs and extracts high-signal error information. It classifies failures into clear, actionable categories such as test failures, dependency issues, and infrastructure timeouts, reducing the need to manually sift through noisy CI output. RedRun is designed as a lightweight DevEx tool that prioritizes predictability, explainability, and fast feedback.

## Motivation

Modern CI systems surface large volumes of log output but provide little structure when builds fail. Developers often spend significant time identifying the root cause of failures and distinguishing primary errors from secondary noise. RedRun focuses on surfacing signal over noise by automatically identifying and categorizing common CI failure modes.

## Features (MVP)

- Parses raw CI log output from failed runs
- Extracts error signals and stack traces
- Classifies failures using deterministic, rule-based logic
- Groups failures into actionable categories
- Produces concise CLI summaries for fast debugging

## Design Principles

- Deterministic by default; no machine learning in the critical path
- Explainable output; every classification is traceable to a rule
- Low noise; prioritizes root causes over raw logs
- Extensible architecture for future enhancements

## Example Usage

```bash
redrun analyze build.log


FAILURE SUMMARY
---------------
Test Failures: 4
Dependency Failures: 2
Infra Timeouts: 1

Top Error:
AssertionError in UserServiceTest



redrun/
├── cli/          # CLI entrypoint
├── ingest/       # log ingestion and normalization
├── extract/      # error extraction
├── classify/     # rule-based failure classification
└── output/       # CLI output formatting
