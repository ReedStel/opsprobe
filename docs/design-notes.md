# Design notes

OpsProbe is intentionally smaller than a remote monitoring agent. It runs when a technician asks it to, performs a bounded set of checks and exits. That boundary keeps the project understandable and makes the generated report easier to review before it leaves a machine.

## Why the standard library?

The diagnostic path has no runtime dependencies. A support tool is most useful when it can be installed on a plain Python environment without resolving a large dependency tree. Development tooling remains optional.

## Why not call `ping`, `ipconfig` or `ifconfig`?

Shelling out would make the first version brittle across Windows, macOS and Linux. It also creates avoidable input-handling risk. OpsProbe uses Python's socket, SSL, filesystem and platform APIs instead.

## Why one target and one port?

This is a triage tool, not a scanner. The default online profile resolves one user-selected host, opens TCP 443 and performs one verified HTTPS request. Host validation rejects URLs, paths and embedded ports.

## Privacy model

The collector omits machine identifiers by default. Exporters then apply a second best-effort redaction pass for home paths, usernames, hostnames, email addresses, IP addresses, MAC addresses and credentials embedded in URLs.

Redaction can never be treated as a guarantee. The CLI says so, and generated reports include the same warning.

## Exit codes

- `0`: checks passed, or only warnings were produced
- `1`: at least one check failed; warnings also return `1` with `--strict`
- `2`: invalid CLI input

That makes the tool usable by a person at a desk and by a lightweight script without pretending it is a monitoring platform.
