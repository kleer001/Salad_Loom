# Salad Loom — Project Spec

## What This Is

A fork of [Text_Loom](https://github.com/kleer001/Text_Loom) repurposed as a **modular absurdist text synthesizer**. Text Loom is a node-based text processing tool with TUI, GUI, REPL, API, and batch interfaces. Salad Loom extends it with nodes specifically designed for word salad, surrealist text generation, and procedural nonsense.

Mascot: A cartoon head of lettuce wearing glasses. Project tagline: **"Procedural nonsense, one node at a time."**

---

## Phase 0 — Fork & Rebrand

### Steps

1. Fork `kleer001/Text_Loom` to `Salad_Loom`
2. Rename all references from "Text Loom" to "Salad Loom" across:
   - `README.md`
   - `setup.py` (package name, description)
   - `start.py`
   - The TUI title bar / modeline (look for the 📝🧵 emoji, replace with 🥬🧵)
   - GUI window title
   - Any docs in `/docs/`
3. Update `CLAUDE.md` with this spec (replace existing content)
4. Do NOT change any node logic, engine internals, or test infrastructure in Phase 0
5. Verify all five interfaces still launch: `./salad_loom -r`, `-t`, `-g`, `-a`, `-b`
6. Run existing tests: `pytest`

### File Renames

```
text_loom → salad_loom  (the CLI entry point)
```

Keep the `/src/` directory structure identical. The internal module names can stay as-is for now — renaming deep internals is a Phase 3 concern.

---

## Phase 1 — New Nodes (Core Word Salad Engine)

All new nodes live in the existing node directory alongside Text Loom's originals. Every node follows Text Loom's existing node class pattern. Study the existing nodes (Text, Split, Section, Merge, Query, Looper, Null, FileIn, FileOut, MakeList) before writing any new ones.

### Data Model

Text Loom's core principle: **everything is a list of strings.** Do not introduce new data types. All new nodes accept `List[str]` and output `List[str]`. Configuration goes in node parameters, not in the data stream.

### New Node Specifications

#### 1. Shuffle Node

**Purpose:** Randomly reorder items in the input list.  
**Parameters:**
- `seed` (int, optional): Random seed for reproducibility. -1 = truly random.
- `mode` (enum): `words` | `sentences` | `items`
  - `words`: Split each string into words, shuffle words, rejoin
  - `sentences`: Split each string into sentences, shuffle sentences, rejoin  
  - `items`: Shuffle the list items themselves (default)

**Input:** List of strings  
**Output:** List of strings (shuffled)  
**Implementation:** `random.shuffle()` with optional seed. For `words` mode, split on whitespace. For `sentences` mode, split on `.!?` followed by whitespace.

#### 2. Interleave Node

**Purpose:** Weave two input lists together alternately.  
**Parameters:**
- `mode` (enum): `items` | `words` | `sentences`
  - `items`: A1, B1, A2, B2, ... (default)
  - `words`: Interleave words from paired strings
  - `sentences`: Interleave sentences from paired strings
- `ratio` (string): Pattern like "2:1" meaning take 2 from A, 1 from B. Default "1:1".

**Inputs:** Two input connections (use Text Loom's existing multi-input mechanism)  
**Output:** Single merged list  
**Implementation:** `itertools.chain` with stepping, or manual zip. Handle unequal lengths by cycling the shorter list.

#### 3. N+7 Node (Dictionary Shift)

**Purpose:** Replace words with the Nth word after them in a dictionary.  
**Parameters:**
- `offset` (int): How many entries to skip. Default 7.
- `target_pos` (enum): `nouns` | `verbs` | `adjectives` | `all`. Default `nouns`.
- `dictionary` (string): Path to dictionary file. Default: bundled dictionary.

**Input:** List of strings  
**Output:** List of strings with words replaced  
**Implementation:**
1. Tokenize input
2. POS-tag using NLTK (`nltk.pos_tag`) to identify target words
3. For each target word, find it in the sorted dictionary, advance N positions, substitute
4. Rejoin

**Dependencies:** `nltk` (add to requirements.txt). Download `averaged_perceptron_tagger` and `punkt` on first run.

**Bundled dictionary:** Ship a sorted English word list at `data/dictionaries/english_common.txt` (one word per line, ~10K words from NLTK's words corpus or similar public domain source).

#### 4. Markov Train Node

**Purpose:** Build a Markov chain model from input text.  
**Parameters:**
- `state_size` (int): Number of words in the prefix. Default 2. Range 1-4.
- `retain_newlines` (bool): Whether to treat newlines as tokens. Default False.

**Input:** List of strings (training corpus)  
**Output:** List containing a single string — the JSON-serialized model  
**Implementation:** Use `markovify` library. `markovify.Text(corpus, state_size=N)`. Serialize with `model.to_json()`.

**Dependencies:** `markovify` (add to requirements.txt)

#### 5. Markov Generate Node

**Purpose:** Generate text from a trained Markov model.  
**Parameters:**
- `count` (int): Number of sentences to generate. Default 10.
- `max_chars` (int): Max characters per sentence. Default 280. 0 = no limit.
- `tries` (int): Attempts per sentence before giving up. Default 100.
- `seed` (int): Random seed. -1 = truly random.

**Input:** List containing a single string — the JSON-serialized model (from Markov Train)  
**Output:** List of generated sentences  
**Implementation:** `markovify.Text.from_json()`, then `model.make_sentence()` in a loop.

#### 6. Skeleton Extract Node

**Purpose:** POS-tag text and replace content words with tagged slots, preserving function words.  
**Parameters:**
- `preserve` (string): Comma-separated POS tags to keep as-is. Default `"DT,IN,CC,TO,PRP,MD"` (determiners, prepositions, conjunctions, "to", pronouns, modals).
- `slot_format` (string): Format for slots. Default `"[{tag}]"`. Can use `"{tag}"`, `"__{tag}__"`, etc.

**Input:** List of strings  
**Output:** List of strings with content words replaced by `[TAG]` markers  
**Implementation:**
1. Tokenize with NLTK
2. POS-tag
3. For each word: if its tag is in `preserve`, keep the word; otherwise replace with `slot_format.format(tag=tag)`
4. Rejoin

**Example:**  
Input: `"The old surgeon carefully stitched the wound"`  
Output: `"The [JJ] [NN] [RB] [VBD] the [NN]"`

#### 7. Skeleton Fill Node

**Purpose:** Fill tagged slots in a skeleton with words from a word pool.  
**Parameters:**
- `mode` (enum): `random` | `sequential` | `weighted`
  - `random`: Pick randomly from matching words (default)
  - `sequential`: Use words in order, cycling
  - `weighted`: Prefer less-common words (inverse frequency)
- `seed` (int): Random seed. -1 = truly random.
- `allow_repeats` (bool): Whether the same word can fill multiple slots. Default True.

**Inputs:** Two inputs:
1. Skeleton strings (containing `[TAG]` markers)
2. Word pool strings (format: `"word/TAG"` per line, or plain words with auto-tagging)

**Output:** List of filled strings  
**Implementation:**
1. Parse word pool into `{tag: [words]}` dictionary
2. For each `[TAG]` in skeleton, pick from the matching tag bucket
3. Handle missing tags gracefully (leave slot or use a fallback)

---

## Phase 2 — Bundled Resources

### Dictionaries

Place in `data/dictionaries/`:

- `english_common.txt` — ~10K common English words, sorted alphabetically, one per line. Source: NLTK words corpus filtered to common usage.

### Sample Corpora

Place in `data/corpora/`:

- `cookbook.txt` — Public domain cookbook text (~5K words). Source: Project Gutenberg, e.g., "The Boston Cooking-School Cook Book" by Fannie Farmer.
- `marine_biology.txt` — Public domain marine biology text (~5K words). Source: Project Gutenberg or NOAA public documents.
- `legal.txt` — Public domain legal text (~5K words). Source: US Constitution + Bill of Rights + a public domain legal manual.
- `romance.txt` — Public domain romance/poetry (~5K words). Source: Project Gutenberg, e.g., collected Keats or Shelley.

### Recipe Workflows

Place in `examples/recipes/`:

Pre-built workflow JSON files demonstrating classic techniques:

- `cut_up.json` — Two FileIn nodes → Shuffle (words mode) → Merge → output. Classic Burroughs.
- `n_plus_7.json` — FileIn → N+7 node (offset 7, nouns only) → output.
- `skeleton_transplant.json` — FileIn (cookbook) → Skeleton Extract → skeleton path. FileIn (marine biology) → Section (nouns/verbs only) → word pool path. Both into Skeleton Fill → output.
- `markov_mashup.json` — Two FileIn nodes (different corpora) → Merge → Markov Train → Markov Generate → output.
- `exquisite_corpse.json` — Three FileIn nodes (different corpora) → three Section nodes (nouns, verbs, adjectives respectively) → Skeleton Fill with a hand-written skeleton template → output.
- `iterative_decay.json` — FileIn → Looper (5 iterations) → Shuffle (words, partial) → output. Text "decays" over passes.

---

## Phase 3 — Polish

### README

Rewrite README.md to reflect Salad Loom's identity:
- Lead with the mascot image and tagline
- Explain what word salad generation is (one paragraph)
- Show a "Hello World" example: load a cookbook, run N+7, get absurd output
- List all node types (original Text Loom nodes + new Salad Loom nodes)
- Link to recipe workflows
- Keep the installation instructions from Text Loom, updated for the new repo name
- Keep the comparison table but reframe: Salad Loom vs other text generation tools (Tracery, RiTa, markovify CLI, etc.)

### Internal Renames

- Rename Python package from `text_loom` to `salad_loom` if feasible without breaking the node system
- Update all internal imports
- Run full test suite after rename

### New Tests

Add tests in the existing test directory for each new node:
- `test_shuffle.py` — Verify deterministic output with seed, verify all items preserved
- `test_interleave.py` — Verify alternation pattern, verify ratio mode, verify unequal length handling
- `test_n_plus_7.py` — Verify known substitution with small dictionary, verify POS filtering
- `test_markov_train.py` — Verify model serializes/deserializes, verify state_size parameter
- `test_markov_generate.py` — Verify output count, verify deterministic with seed
- `test_skeleton_extract.py` — Verify known sentence produces expected skeleton
- `test_skeleton_fill.py` — Verify all slots filled, verify POS matching, verify no-match fallback

---

## Architecture Notes

### How Text Loom Nodes Work (study before coding)

Each node is a Python class. Key things to understand:

1. **Node registration** — Look at how existing nodes register themselves. New nodes must follow the same pattern.
2. **Input/output connections** — Nodes declare inputs and outputs. Data flows as `List[str]`.
3. **Parameters** — Each node has a parameter set (key-value pairs) editable in the TUI/GUI.
4. **Cook method** — The `cook()` or `evaluate()` method is called when the node executes. This is where your logic goes.
5. **State tracking** — Nodes track cooked/uncooked state. Only re-cook when inputs change.

**Before writing any node, read the source for at least Text Node and Split Node end-to-end.** They are the simplest and most representative.

### Dependencies to Add

Add to `requirements.txt`:
```
nltk>=3.8
markovify>=0.9
```

Add an NLTK data download step to `install.sh` or to the first-run logic:
```python
import nltk
nltk.download('averaged_perceptron_tagger_eng', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('words', quiet=True)
```

### What NOT to Change

- Do not modify the node engine, graph execution, or cook system
- Do not modify the TUI framework (Textual-based)
- Do not modify the GUI framework (React/TypeScript)
- Do not modify the API server (FastAPI)
- Do not modify the Looper, Query, or any existing node logic
- Do not add new data types to the connection system — everything stays `List[str]`

---

## Execution Order

```
Phase 0 → Phase 1 (nodes 1-3) → test → Phase 1 (nodes 4-5) → test → Phase 1 (nodes 6-7) → test → Phase 2 → Phase 3
```

Ship incrementally. Each node should work independently before wiring them together in recipe workflows.

---

## Coding Conventions

- Follow existing Text Loom code style (Black formatter, type hints where present)
- Docstrings on every new class and public method
- No external API calls in any new node (everything runs locally/offline)
- All randomness must support deterministic seeding
- Graceful failure: if a node gets unexpected input, output an error string in the list rather than crashing
