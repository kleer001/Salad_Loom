# CLAUDE.md - Salad Loom

## Project Identity

**Salad Loom** is a fork of Text_Loom repurposed as a modular absurdist text synthesizer.
Tagline: *"Procedural nonsense, one node at a time."*
Mascot: A cartoon head of lettuce wearing glasses. Emoji: 🥬🧵

This project spec lives in `SALAD_LOOM_SPEC.md` (Phases 0–3) and `SALAD_LOOM_SPEC_EXTENDED.md` (Phases 4–6).

## Architecture

- **Node discovery:** Automatic. All `src/core/*_node.py` files are registered as node types at import time via `enums.py`. No manual registration needed.
- **Data model:** Everything is `List[str]`. No new data types in the connection system.
- **Node pattern:** Subclass `Node` from `core.base_classes`. Implement `_internal_cook()`, `input_names()`, `output_names()`, `input_data_types()`, `output_data_types()`.
- **Parameters:** `Parm(name, ParameterType.STRING|INT|TOGGLE|FLOAT, self)` in `__init__`, read via `self._parms["name"].eval()`.
- **Interfaces:** TUI (Textual), GUI (React/TypeScript), API (FastAPI), REPL, Batch — all launched from `./salad_loom`.

## What NOT to Touch

- Node engine (`node.py`, `node_connection.py`, `node_environment.py`, `base_classes.py`)
- TUI framework internals (only modeline branding is changed)
- GUI framework internals (only title and file descriptions are changed)
- API server internals
- Looper, Query, or any existing node logic

## Role & Philosophy

- **Role:** Senior Software Developer
- **Core Tenets:** DRY, SOLID, YAGNI, KISS
- **Communication Style:** Concise and minimal. Focus on code, not chatter.
- **Planning Protocol:** For complex requests, provide a bulleted outline/plan before writing code.

## Architecture & Structure

- **Paradigm:** Object-oriented structure with functional internals.
- **Modularity:** Separate implementation, execution, and test files.
- **`src/core` Protection:** Do NOT fix bugs or refactor code in `src/core`. Report and halt if a bug is found there. New nodes are additions, not modifications.

## Testing

- **Framework:** pytest
- **Location:** `src/tests/`
- **Scope:** Unit tests for all new nodes. Use pytest fixtures for setup/teardown.

## Code Style

- **Type hints:** Mandatory. Explicit return types.
- **Naming:** `snake_case` functions/variables, `PascalCase` classes. Self-documenting names.
- **Comments:** Docstrings at class/method level only. No inline comments.
- **Formatter:** Black

## Dependencies

- All randomness must support deterministic seeding (seed=-1 means truly random).
- No external API calls in any node — everything runs locally/offline.
- Graceful failure: on unexpected input, output an error string in the list rather than raising.
- New dependencies: `nltk>=3.8`, `markovify>=0.9` (Phase 1); `spacy` (Phase 5).
