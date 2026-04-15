# Salad Loom Help

## Quick Start

```bash
./salad_loom -t          # Terminal UI
./salad_loom -g          # Web GUI (requires Node.js)
./salad_loom -r          # Python REPL
./salad_loom -b -f examples/recipes/n_plus_7.json   # Batch mode
```

## Node Reference

See [NODES.md](NODES.md) for a quick-reference table of all 35 nodes.

See [node_guide.md](node_guide.md) for detailed documentation with examples.

## Recipes

Pre-built workflows live in `examples/recipes/`. Load them with:

```bash
./salad_loom -b -f examples/recipes/<name>.json
```

| Recipe | What it does |
|--------|-------------|
| `n_plus_7.json` | Oulipo N+7 noun substitution on a corpus |
| `cut_up.json` | Burroughs-style cut-up from two sources |
| `skeleton_transplant.json` | Extract structure from one text, fill from another |
| `markov_mashup.json` | Train Markov chain and generate new sentences |
| `exquisite_corpse.json` | Automated exquisite corpse from multiple corpora |
| `iterative_decay.json` | Looped decay via repeated N+7 passes |
| `semantic_decay.json` | Drift word meanings then filter by coherence |
| `tracery_salad.json` | Context-free grammar expansion |
| `deep_transplant.json` | Dependency-parse skeleton + cross-corpus fill |
| `fold_in_mashup.json` | Fold-in two corpora with phrase stuttering |
| `the_full_salad.json` | Full pipeline: Markov → N+7 → drift → gate |

## API

Start the API server:

```bash
./salad_loom -a
```

Interactive docs at `http://localhost:8000/api/v1/docs`.

See [api/quick_reference.md](api/quick_reference.md) for curl examples.

## MCP Server

Salad Loom exposes an MCP server so AI assistants can build workflows programmatically.

See [MCP_INTEGRATION.md](MCP_INTEGRATION.md) and [mcp_server.md](mcp_server.md).

## Dependencies

| Package | Used by |
|---------|---------|
| `nltk` | N+7, Skeleton nodes, Phonetic Filter |
| `markovify` | Markov Train/Generate |
| `spacy` + `en_core_web_sm` | Dependency Parse, Conjugation Fixer |
| `gensim` + GloVe model | Semantic Drift, Coherence Gate |

## Getting Help

- Open an issue: https://github.com/kleer001/Salad_Loom/issues
- Read the spec: `SALAD_LOOM_SPEC.md` and `SALAD_LOOM_SPEC_EXTENDED.md`
