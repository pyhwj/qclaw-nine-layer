---
name: skill-python-project
description: "Python project scaffolding with pyproject.toml, linting, and packaging patterns from psf/black, astral-sh/ruff, python-poetry/poetry."
---

# Python Project Scaffold

Distilled from [psf/black](https://github.com/psf/black) + [astral-sh/ruff](https://github.com/astral-sh/ruff) + [python-poetry/poetry](https://github.com/python-poetry/poetry). Initialize professional Python projects in one shot.

## Project Template

```
my-project/
├── pyproject.toml
├── src/my_project/__init__.py
├── tests/test_basic.py
├── .gitignore
├── .pre-commit-config.yaml
└── README.md
```

## pyproject.toml (full template)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["pydantic>=2.0", "httpx>=0.27"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-cov", "ruff>=0.6", "mypy>=1.0"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM", "C4"]

[tool.ruff.format]
quote-style = "double"

[tool.mypy]
strict = true
python_version = "3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

## .gitignore (minimal)

```
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
.env
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

## .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
```

## Init Script

```bash
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
pre-commit install
git init && git add -A && git commit -m "init: project scaffold"
```

## Quality Commands

```bash
ruff check .          # lint
ruff format .         # format
mypy src/             # type check
pytest -v --cov=src   # test + coverage
```