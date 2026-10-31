# Contributing

1. Create a focused branch from `main`.
2. Install the development dependencies with `python -m pip install -e ".[dev]"`.
3. Add or update tests for every behavioural change.
4. Run `pytest`, `ruff check .`, `ruff format --check .`, `mypy src/procurepilot` and Bandit.
5. Explain the problem, decision and verification in the pull request.

Never commit credentials, production policies or real procurement data.

