# Contributing

Small, reviewable changes are preferred.

1. Create a branch from `main`.
2. Install the development extras with `python -m pip install -e ".[dev]"`.
3. Run `python -m ruff check src tests`.
4. Run `python -m unittest discover -s tests -v`.
5. Explain any new data collection in the pull request and update `explain-data`.

New diagnostics should remain bounded, cross-platform where practical and safe to run on a workstation. Avoid shell commands, broad port ranges and collection of file contents or credentials.
