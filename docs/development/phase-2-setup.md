# Phase 2: Repository and environment setup

## What this phase is for

This phase prepares the project's home folder and coding tools. It does not build shopping features. Those begin in Phase 3. The goal is that a developer can open the repository, understand where future files belong, and run the basic checks.

## Step 1: Choose supported language versions

- **Python 3.15.2:** the current stable release, installed for this project. Project metadata still permits Python 3.12 and newer so we can use a compatible supported version if a library has not caught up yet.
- **Node.js 24:** the project uses Node for TypeScript, React, and Playwright. Node 24 is an LTS release line.

The `.python-version` and `.nvmrc` files make these choices visible to version managers. The computer initially had Python 3.9.6, which was too old. Python 3.15.2 is now installed in the user's version-managed Python directory. Node 24.21 already matches the chosen Node line.

## Step 2: Understand the top-level folders

- `apps/api` will hold the Python service.
- `apps/web` will hold the React screens.
- `automation/api`, `automation/ui`, `automation/ai`, and `automation/performance` separate the different test types.
- `data/knowledge_base` will hold sample help documents for the chatbot.
- `docs` stores architecture and developer guides.
- `tests` currently checks the repository setup itself.

Empty future folders contain `.gitkeep`. Git does not store empty folders, so this tiny placeholder records where the next phase will add files.

## Step 3: Keep secrets out of Git

`.env.example` shows the names of settings the app will need later, with an empty AI key. Copy it to `.env` for private local values. `.gitignore` tells Git to ignore `.env`, Python virtual environments, caches, JavaScript dependencies, and generated test results. It explicitly keeps `.env.example` tracked.

## Step 4: Set up Python tools

`requirements-dev.txt` lists tools for development: Pytest runs checks and Ruff finds common Python mistakes and formatting issues. `pyproject.toml` records Python compatibility and the shared settings for those tools. Runtime application libraries will be added in Phase 3, when there is an API to build.

Run:

```bash
make setup-python
```

This creates `.venv`, upgrades pip inside it, and installs the development tools. The `.venv` folder is local and ignored by Git.

## Step 5: Run the basic quality checks

```bash
make lint
make format-check
make test
```

- `make lint` checks Python code for common mistakes and import ordering.
- `make format-check` checks formatting without changing files.
- `make test` runs the setup checks with Pytest.

At the start, these checks cover the repository scaffold. Later phases will add tests for backend rules, API behavior, browser journeys, and AI quality.

## Files created in this phase

| File | Why it exists |
|---|---|
| `.gitignore` | Prevents local tools, generated files, and private settings from being added to Git. |
| `.env.example` | Shows future setting names without containing a secret. |
| `.python-version`, `.nvmrc` | Record the intended Python and Node versions. |
| `requirements-dev.txt` | Lists Python lint and test tools. |
| `pyproject.toml` | Holds Python project metadata and shared Ruff/Pytest configuration. |
| `Makefile` | Gives short, repeatable commands for setup and checks. |
| `README.md` | Explains the project and the commands to get started. |
| `tests/test_project_setup.py` | Checks that the planned folders exist and no real AI key is in the sample config. |

## Expected outcome

The repository has its planned folder structure, safe example configuration, language version notes, Python quality-tool settings, and a small setup test suite. No storefront, backend endpoints, or database tables exist yet.
