# 🥬🧵 Salad Loom

![Salad Loom mascot](docs/images/mascot.png)

> **Procedural nonsense, one node at a time.**

Salad Loom is a modular absurdist text synthesizer built on a node-based graph editor. Wire up sources, transformations, and outputs to produce word salad, surrealist prose, N+7 poetry, Markov mashups, and skeleton transplants — all without writing code.

It ships with five interfaces: TUI, GUI, API, REPL, and batch mode.

---

## Hello World: Cook → Nonsense in 30 seconds

```bash
# One-command install (~1 GB: packages + NLP models)
curl -sSL https://raw.githubusercontent.com/kleer001/Salad_Loom/main/bootstrap.sh | bash

# Load a cookbook, run N+7, watch nouns mutate
./salad_loom -b -f examples/recipes/n_plus_7.json
```

Input: `"Dissolve sugar in hot water and stir until the mixture thickens."`  
Output: `"Dissolve suppression in hot waterfall and stir until the moan thickens."`

---

## What Is Word Salad Generation?

Word salad generation is the art of producing syntactically plausible but semantically unhinged text. It draws on a long lineage of procedural and constrained writing:

- **[Tristan Tzara](https://en.wikipedia.org/wiki/Tristan_Tzara)** (1920) — Dada poet who published instructions for a chance-operation poem: cut words from a newspaper, shake them in a bag, draw them out, copy in order. The original recipe is [here in his own words](https://www.writing.upenn.edu/~afilreis/88v/tzara.html).

- **[Brion Gysin](https://www.briongysin.com/cut-ups/)** (1958) — Painter and writer who accidentally invented the cut-up technique at the Beat Hotel in Paris, slicing pages of text and recombining them. His estate's site has the full story. [William S. Burroughs](https://www.ubu.com/papers/burroughs_gysin.html) adopted the method from Gysin and famously wrote: *"Brion Gysin was the first to create cut-ups."*

- **[William S. Burroughs](https://www.openculture.com/2011/08/william_s_burroughs_on_the_art_of_cutup_writing.html)** — Novelist who popularized the cut-up and developed the fold-in method (folding two pages together to splice text mid-line), first deployed in *The Ticket That Exploded* (1962). [The Cut-Ups (1966)](https://www.youtube.com/watch?v=Uq_hztHJCM4), a film by Burroughs and Antony Balch, applies the technique to cinema.

- **[Oulipo](https://poets.org/text/brief-guide-oulipo)** — "Ouvroir de littérature potentielle" (workshop of potential literature), founded 1960 by Raymond Queneau and François Le Lionnais. Systematized constraint-based writing as a generative art form. **[Jean Lescure](https://www.oulipo.net/oulipiens/JL)**, founding member #7, invented the N+7 (S+7) constraint on February 13, 1961: replace every noun with the seventh noun following it in a chosen dictionary.

- **[Andrei Markov](https://en.wikipedia.org/wiki/Andrey_Markov)** (1906/1913) — Russian mathematician who developed the probability chains bearing his name, and in 1913 applied them to literary text by analyzing vowel/consonant transitions in Pushkin's *Eugene Onegin*. Claude Shannon later extended Markov's math into language modeling, laying the groundwork for stochastic text generation.

Salad Loom puts all of these in a visual node graph so you can combine, chain, and mutate them interactively.

---

## Interfaces

| Flag | Interface | Use case |
|------|-----------|----------|
| `-t` | TUI | Interactive terminal graph editor |
| `-g` | GUI | Visual browser-based graph editor |
| `-r` | REPL | Python shell with full node API |
| `-a` | API | FastAPI server for remote control |
| `-b` | Batch | Non-interactive workflow execution |

```bash
./salad_loom -t                        # Terminal UI
./salad_loom -g                        # GUI (starts backend + browser)
./salad_loom -r                        # REPL
./salad_loom -a -p 8080                # API on port 8080
./salad_loom -b -f my_workflow.json    # Batch mode
```

---

## Node Types

### Original Text Loom Nodes

| Node | Purpose |
|------|---------|
| **Text** | Inject literal strings or expressions |
| **Split** | Slice or randomly sample from a list |
| **Merge** | Combine multiple lists into one |
| **Section** | Extract lines matching a pattern |
| **FileIn** | Read a text file into the graph |
| **FileOut** | Write graph output to a file |
| **Looper** | Iterate a subgraph N times |
| **Query** | Send text to an LLM and get a response |
| **Null / InputNull / OutputNull** | Passthrough / boundary nodes |
| **MakeList** | Construct lists from parameters |
| **Chunk** | Split text into overlapping chunks |
| **Count** | Count words, characters, or frequency |
| **Folder** | Read all files in a directory |
| **JSON** | Extract values from JSON strings |
| **StringTransform** | Apply string operations |
| **Search** | Search text with regex |

### Salad Loom Nodes

| Node | Purpose |
|------|---------|
| **Shuffle** | Reorder list items, words, or sentences randomly |
| **Interleave** | Weave two lists together with configurable ratio |
| **N+7** | Replace nouns/verbs/adjectives with the Nth dictionary entry after them |
| **MarkovTrain** | Build a Markov chain model from a corpus |
| **MarkovGenerate** | Generate sentences from a trained Markov model |
| **SkeletonExtract** | POS-tag text and replace content words with `[TAG]` slots |
| **SkeletonFill** | Fill `[TAG]` slots from a word pool by part of speech |

---

## Recipe Workflows

Pre-built workflows in `examples/recipes/`:

| File | Technique | Description |
|------|-----------|-------------|
| `cut_up.json` | Burroughs cut-up | Shuffle words from two corpora and merge |
| `n_plus_7.json` | Oulipo N+7 | Replace every noun 7 entries forward in the dictionary |
| `skeleton_transplant.json` | Skeleton transplant | Extract sentence structure from one corpus, fill with words from another |
| `markov_mashup.json` | Markov chain | Train on two corpora merged, generate new sentences |
| `exquisite_corpse.json` | Exquisite corpse | Fill hand-written templates with words from three corpora |
| `iterative_decay.json` | Iterative decay | Loop a corpus through a shuffle, degrading it over passes |

```bash
./salad_loom -b -f examples/recipes/cut_up.json
./salad_loom -t -f examples/recipes/markov_mashup.json
```

---

## Bundled Resources

### Dictionaries (`data/dictionaries/`)
- `english_common.txt` — 10,000 common English words, sorted alphabetically. Used by the N+7 node.

### Sample Corpora (`data/corpora/`)
- `cookbook.txt` — Fannie Farmer's Boston Cooking-School Cook Book (PD)
- `marine_biology.txt` — Natural history of the sea (PD sources)
- `legal.txt` — US Constitution, Bill of Rights, Federalist Papers (PD)
- `romance.txt` — Keats and Shelley (PD)

---

## Installation

```bash
git clone https://github.com/kleer001/Salad_Loom
cd Salad_Loom
./install.sh          # creates venv, installs deps, downloads NLTK data
./salad_loom -t       # launch TUI
```

**Requirements:** Python 3.8+, Node.js (GUI only)

**Dependencies:** `textual`, `fastapi`, `uvicorn`, `nltk`, `markovify`, `litellm`, `mcp`

---

## Salad Loom vs Other Tools

| Feature | Salad Loom | Tracery | RiTa | markovify CLI |
|---------|-----------|---------|------|---------------|
| Visual node graph | ✅ | ❌ | ❌ | ❌ |
| N+7 substitution | ✅ | ❌ | ❌ | ❌ |
| Markov chains | ✅ | ❌ | ✅ | ✅ |
| POS-aware skeleton | ✅ | ❌ | ✅ | ❌ |
| Cut-up / fold-in | ✅ | ❌ | ❌ | ❌ |
| Grammar expansion | ✅ | ✅ | ✅ | ❌ |
| LLM integration | ✅ | ❌ | ❌ | ❌ |
| TUI interface | ✅ | ❌ | ❌ | ❌ |
| REST API | ✅ | ❌ | ❌ | ❌ |
| Runs fully offline | ✅ | ✅ | ✅ | ✅ |

---

## Development

```bash
pytest src/tests/          # run all tests
./salad_loom -t            # TUI for interactive testing
```

All new nodes live in `src/core/`. Adding a node is as simple as creating `src/core/mynode_node.py` — it is auto-discovered at startup.

---

## License

MIT — see `LICENSE`.

Originally forked from [Text Loom](https://github.com/kleer001/Text_Loom).
