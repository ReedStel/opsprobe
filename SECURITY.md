# Security policy

## Supported versions

OpsProbe is currently pre-1.0. Security fixes are applied to the latest release on the `main` branch.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability that could expose workstation data. Use GitHub's private vulnerability reporting feature for this repository instead.

Include the affected command, a minimal reproduction and the type of data or system at risk. Do not attach real credentials, private diagnostic reports or customer information.

## Data handling

OpsProbe runs locally, sends no telemetry and writes reports only when an output path is supplied. Its redaction is best-effort. Users should inspect every exported report before sharing it.
