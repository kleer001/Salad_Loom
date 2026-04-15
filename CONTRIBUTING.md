# Contributing to Salad Loom

We appreciate your interest in making Salad Loom better! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

Be respectful, constructive, and collaborative. We're all here to build something useful.

## How Can I Contribute?

### Reporting Bugs

**Before submitting:**
- Check existing [issues](https://github.com/kleer001/Salad_Loom/issues)
- Verify the bug exists in the latest version

**When reporting:**
- Use a clear, descriptive title
- Include steps to reproduce
- Describe expected vs actual behavior
- Note your environment (OS, Python version)

### Suggesting Features

Open an issue with the `enhancement` label. Describe:
- The problem you're solving
- Your proposed solution
- Any alternatives you've considered

### Code Contributions

See [Development Workflow](#development-workflow) below.

## Development Workflow

### Initial Setup

```bash
git clone https://github.com/YOUR_USERNAME/Salad_Loom
cd Salad_Loom
python3 -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -e ".[dev]"
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Download NLP models required by several nodes
python -m spacy download en_core_web_sm
python3 -c "import nltk; [nltk.download(p) for p in ['averaged_perceptron_tagger_eng','punkt_tab','words','cmudict']]"
```

### Running Tests

```bash
pytest                    # Run all tests
pytest src/tests/test_specific.py  # Run specific test file
pytest -v                # Verbose output
```

## Coding Standards

Salad Loom follows strict engineering principles to maintain code quality and consistency.

### Core Principles

- **DRY** (Don't Repeat Yourself) - Avoid code duplication
- **SOLID** principles - Write maintainable, extensible code
- **YAGNI** (You Aren't Gonna Need It) - Don't build for hypothetical futures
- **KISS** (Keep It Simple, Stupid) - Simplicity over complexity

### Architecture

- **Paradigm**: Object-oriented structure with functional internals
  - Use classes for logical grouping and configuration encapsulation
  - Methods should be stateless where practical—pass dependencies explicitly
  - Acceptable stateful patterns: caching, connection pooling, configuration
  - Prefer pure functions for business logic and transformations
- **Modularity**: Output code in modular structure (separate implementation, execution, and test files)
- **Versions**: Use modern syntax unless overridden by `requirements.txt` or `package.json`

### Python Standards

- **Type hints required** for all function signatures
  - Define explicit interfaces/types for all inputs
  - Provide explicit return type hints
- **PEP 8** style compliance
- **Descriptive names** - Variable and function names must be verbose and self-documenting
- **No inline comments** - Strictly forbidden within function/method bodies
- **Docstrings** - Permitted only at module/class/object level
- **Standard library first** - Prioritize built-in features; avoid 3rd party dependencies unless utility is overwhelming
- **Synchronous by default** - Use async/await only when strictly necessary (I/O bound operations)

### Testing Requirements

- **Framework**: pytest
- **Scope**: Unit tests for all non-trivial functions/methods
- **Structure**: Separate test files (e.g., `test_module.py`) in `src/tests/`
- **Fixtures**: Use pytest fixtures for setup/teardown
- **Coverage**: Focus on edge cases and error paths, not just happy paths

### Adding New Nodes

New nodes are auto-discovered — no registration required. To add one:

1. Create `src/core/my_node_name_node.py`
2. Define a class named `MyNodeNameNode` (CamelCase of the filename parts)
3. Subclass `Node` from `core.base_classes`
4. Implement `_internal_cook()`, `input_names()`, `output_names()`, `input_data_types()`, `output_data_types()`
5. Set `GLYPH`, `GROUP` (from `FunctionalGroup`), `SINGLE_INPUT`, `SINGLE_OUTPUT`
6. Add unit tests in `src/tests/test_my_node_name.py`

### Code Organization

- **`src/core` Protection**: The `src/core` directory contains foundational code
  - **Bug Fixes**: Do NOT implement bug fixes or refactor code within `src/core` without discussion
  - **Improvements**: Propose clean-up or refactoring for `src/core`, but do NOT implement without explicit maintainer approval
  - Focus on working around `src/core` via composition or extension
- **Root Directory**: Keep clean and public-facing
  - Tests go into `src/tests/`
  - No loose scripts, specific tests, or helper functions
  - Only essential files: main directories, install files, README.md, LICENSE, essential dotfiles

### Avoid Over-Engineering

- Only make changes that are directly requested or clearly necessary
- Don't add features, refactor, or make "improvements" beyond what was asked
- Don't add error handling for scenarios that can't happen
- Don't create helpers or abstractions for one-time operations
- Don't design for hypothetical future requirements
- Three similar lines of code is better than a premature abstraction

## Submitting Changes

### Pull Request Process

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/descriptive-name`
3. **Make changes** following coding standards
4. **Write tests** for new functionality
5. **Run tests**: `pytest` (must pass)
6. **Commit**: Clear, descriptive messages
7. **Push**: `git push origin feature/descriptive-name`
8. **Open PR** with detailed description

### PR Guidelines

- Link related issues
- Describe what changed and why
- Include screenshots for UI changes
- Keep changes focused and atomic
- Ensure code is linter-compliant and error-free

### Review Process

- Maintainers will review within 1-2 weeks
- Address feedback in new commits
- Once approved, maintainers will merge

## Questions or Need Help?

- Open a [discussion](https://github.com/kleer001/Salad_Loom/discussions)
- Comment on related issues
- Reach out in your PR

---

**License**: By contributing, you agree that your contributions will be licensed under the MIT License.
