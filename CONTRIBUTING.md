# Contributing

Hey, thanks for stopping by! Contributions are welcome — whether it's fixing a bug, adding a new extractor or renderer, or improving the docs.

## 🛠 Development Setup

```bash
# Clone the repo
git clone https://github.com/jmars/unified-history-mcp.git
cd unified-history-mcp

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

## 🧪 Running Tests

Tests use [pytest](https://docs.pytest.org/). Run them with:

```bash
pytest
```

With coverage:

```bash
pytest --cov=unified_history_mcp
```

## ✨ Linting & Formatting

There's no strict lint tool enforced yet, but we aim for clean, consistent code. A good starting point is:

```bash
pip install ruff
ruff check src/
```

If you'd like to formalize a lint setup (e.g. ruff config in `pyproject.toml`), that's a welcome contribution too!

## 📏 Code Style

- Follow **[PEP 8](https://peps.python.org/pep-0008/)** for code style.
- **Type hints are required** on all function signatures — including `def` statements, not just abstract methods. This project targets Python 3.10+, so use modern syntax (`list[str]` over `List[str]`, `| None` over `Optional`, etc.).
- Keep functions focused and reasonably sized.
- Write docstrings for public modules, classes, and functions.
- Prefer readability over cleverness.

## 🚀 Submitting Changes

1. **Fork** the repository on GitHub.
2. **Create a branch** for your change (`git checkout -b my-feature`).
3. **Make your changes** — keep commits small and descriptive.
4. **Run tests** to make sure nothing is broken.
5. **Push** to your fork and open a **Pull Request**.
6. In the PR description, explain what you changed and why.

All PRs must pass the existing test suite. Adding tests for new functionality is strongly encouraged.

## 📄 License

This project is licensed under the **MIT License**. By contributing, you agree that your contributions will be licensed under the same MIT terms.
