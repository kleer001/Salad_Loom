# Salad Loom — Extended Spec (Phases 4–6)

This spec continues from `SALAD_LOOM_SPEC.md` (Phases 0–3). Do not begin these phases until Phases 0–3 are complete and tested.

---

## Phase 4 — Lightweight Nodes (No New Dependencies)

These nodes use only Python stdlib and NLTK (already installed from Phase 1).

### 8. Regex Replace Node

**Purpose:** Find-and-replace using regular expressions. The workhorse for targeted mutations.  
**Parameters:**
- `pattern` (string): Regex pattern to match. Required.
- `replacement` (string): Replacement string. Supports `\1`, `\2` backreferences. Default `""` (deletion).
- `count` (int): Max replacements per string. 0 = all. Default 0.
- `flags` (string): Comma-separated regex flags: `ignorecase`, `multiline`, `dotall`. Default `""`.

**Input:** List of strings  
**Output:** List of strings with substitutions applied  
**Implementation:** `re.sub(pattern, replacement, text, count=count, flags=flags)` per string. Catch `re.error` and output error message string on bad patterns.

#### 9. Fold-In Node

**Purpose:** The Burroughs/Gysin fold-in technique. Takes two texts, splits each in half vertically (by line), then reads across the combined halves.  
**Parameters:**
- `split_point` (float): Where to fold, as fraction of line length. Default 0.5. Range 0.1–0.9.
- `mode` (enum): `characters` | `words`
  - `characters`: Split each line at the character midpoint (default, true to original technique)
  - `words`: Split each line at the word midpoint

**Inputs:** Two input connections  
**Output:** List of strings — each line is left-half of input A + right-half of input B  
**Implementation:**
1. Pair lines from input A and input B (zip, cycling shorter)
2. For each pair, split line A at `split_point`, split line B at `split_point`
3. Output: `left_half_A + " " + right_half_B`

**Example:**  
A: `"The surgeon stitched the wound carefully"`  
B: `"The glacier released ancient sediment slowly"`  
Output: `"The surgeon stitched ancient sediment slowly"`

#### 10. Repetition Injector Node

**Purpose:** Create obsessive, stuttering, looping text. Randomly repeats words or phrases.  
**Parameters:**
- `mode` (enum): `word` | `phrase` | `sentence`
  - `word`: Randomly repeat individual words (default)
  - `phrase`: Repeat 2-4 word chunks
  - `sentence`: Repeat whole sentences
- `density` (float): Probability of any given element being repeated. Default 0.15. Range 0.0–1.0.
- `max_repeats` (int): Maximum times an element can repeat. Default 3. Range 1–10.
- `seed` (int): Random seed. -1 = truly random.

**Input:** List of strings  
**Output:** List of strings with repetitions inserted  
**Implementation:** Tokenize, iterate, roll against `density` for each element, insert `random.randint(1, max_repeats)` copies when triggered.

**Example (word mode, density 0.2):**  
Input: `"The old man crossed the street"`  
Output: `"The old old old man crossed the the street"`

#### 11. Tracery Grammar Node

**Purpose:** Expand a Tracery-style context-free grammar into text.  
**Parameters:**
- `start_symbol` (string): The symbol to begin expansion from. Default `"origin"`.
- `count` (int): Number of expansions to generate. Default 5.
- `seed` (int): Random seed. -1 = truly random.

**Input:** List of strings — the grammar definition in JSON format. Each string is treated as a line of a single JSON object. Lines are joined before parsing.  
**Output:** List of generated strings  
**Implementation:** Write a minimal Tracery expander (~80 lines):
1. Parse JSON: `{"origin": ["#greeting#, #creature#"], "greeting": ["hello", "behold"], "creature": ["hermit crab", "logarithm"]}`
2. Start with `start_symbol`
3. Recursively replace `#symbol#` with random choice from that symbol's array
4. Repeat until no `#symbols#` remain or max depth (20) reached
5. Support modifiers: `.capitalize`, `.a` (a/an), `.s` (pluralize), `.ed` (past tense)

Do NOT use an external Tracery library. The Python implementations are poorly maintained. A self-contained expander is more reliable and lets us add modifiers specific to word salad.

**Grammar format example (provided as input text):**
```json
{
  "origin": ["The #adjective# #creature# #action# the #adjective# #object#."],
  "adjective": ["decaffeinated", "logarithmic", "anxious", "carbonated", "fossilized"],
  "creature": ["hermit crab", "penguin", "mathematician", "turnip"],
  "action": ["stitched", "interrogated", "defenestrated", "baptized"],
  "object": ["sunset", "spreadsheet", "glacier", "sandwich"]
}
```

---

## Phase 5 — Medium-Weight Nodes (spaCy Dependency)

These nodes require `spacy` and its English model. This is a heavier dependency (~50MB) but unlocks significantly deeper linguistic manipulation.

### Dependencies to Add

Add to `requirements.txt`:
```
spacy>=3.5
```

Add to `install.sh` or first-run:
```bash
python -m spacy download en_core_web_sm
```

#### 12. Dependency Parse Node

**Purpose:** Extract full syntactic dependency trees, not just POS tags. Enables deep structural transplants where subject-verb-object relationships are preserved.  
**Parameters:**
- `output_format` (enum): `tree` | `flat` | `skeleton`
  - `tree`: Output dependency tree as indented text (for inspection)
  - `flat`: Output each token as `word/POS/DEP/head_word` (for processing)
  - `skeleton`: Like Skeleton Extract but using dependency roles instead of POS tags. Slots are `[nsubj]`, `[dobj]`, `[amod]`, etc. (default)
- `preserve` (string): Comma-separated dependency labels to keep as literal text. Default `"det,prep,aux,cc,punct,mark"`.

**Input:** List of strings  
**Output:** List of strings in chosen format  
**Implementation:** `spacy.load("en_core_web_sm")`, process each string, format according to `output_format`.

**Example (skeleton mode):**  
Input: `"The tired surgeon carefully stitched the deep wound"`  
Output: `"The [amod] [nsubj] [advmod] [ROOT] the [amod] [dobj]"`

#### 13. Conjugation Fixer Node

**Purpose:** Repair verb agreement, tense consistency, and article correctness after text has been mangled by other nodes. Makes absurd text grammatically smooth.  
**Parameters:**
- `fix_verbs` (bool): Fix subject-verb agreement. Default True.
- `fix_articles` (bool): Fix a/an based on following word's phonetics. Default True.
- `fix_capitalization` (bool): Capitalize sentence starts. Default True.
- `target_tense` (enum): `preserve` | `past` | `present`. Default `preserve`.

**Input:** List of strings  
**Output:** List of strings with grammar repairs  
**Implementation:**
1. Parse with spaCy
2. For `fix_articles`: check if "a" precedes a vowel-sound word → change to "an", and vice versa
3. For `fix_verbs`: identify subject-verb pairs, check number agreement, conjugate using spaCy's lemma + morphology
4. For `fix_capitalization`: capitalize first word after `.!?`

This is intentionally conservative — it fixes mechanical grammar without altering word choices. The absurdity of content is preserved; only the surface grammar is smoothed.

#### 14. Phonetic Filter Node

**Purpose:** Score and filter text by sound properties. Keep sentences with alliteration, assonance, or pleasing rhythm. Reject dull-sounding output.  
**Parameters:**
- `mode` (enum): `alliteration` | `assonance` | `rhythm` | `any`
  - `alliteration`: Score by repeated initial consonants (default)
  - `assonance`: Score by repeated vowel sounds
  - `rhythm`: Score by variation in syllable count per word
  - `any`: Combined score of all three
- `threshold` (float): Minimum score to pass. Default 0.3. Range 0.0–1.0.
- `invert` (bool): If True, keep BELOW threshold (reject pleasing text, keep ugly text). Default False.

**Input:** List of strings  
**Output:** List of strings that pass the filter  
**Implementation:**
1. Use spaCy or NLTK's CMU Pronouncing Dictionary for phoneme lookup
2. For alliteration: count fraction of adjacent words sharing initial consonant
3. For assonance: count fraction of words sharing a stressed vowel phoneme
4. For rhythm: measure standard deviation of syllable counts (higher = more varied = more interesting)
5. Normalize each score 0–1, filter by threshold

---

## Phase 6 — Heavy Nodes (Word Embeddings)

These nodes use word vector models. They enable semantically-aware operations — the difference between random nonsense and *targeted* absurdity.

### Dependencies to Add

Add to `requirements.txt`:
```
gensim>=4.3
```

The `en_core_web_md` or `en_core_web_lg` spaCy models include word vectors, but Gensim gives more control. Use Gensim's `KeyedVectors` to load a small pre-trained model.

### Bundled Model

Ship or auto-download a small word2vec model. Options:
- `glove-wiki-gigaword-50` via Gensim's downloader (~70MB). 50-dimensional, good enough for distance calculations.
- Or: generate a custom small model from the bundled corpora (much smaller, less accurate, but fully offline).

Decision: use Gensim's downloader with a fallback message if offline. Store in `data/models/`.

#### 15. Semantic Drift Node

**Purpose:** Gradually replace words with semantically adjacent ones. Text "melts" from one meaning-domain to another over the course of paragraphs.  
**Parameters:**
- `drift_rate` (float): Fraction of words to replace per pass. Default 0.1. Range 0.0–0.5.
- `drift_distance` (float): How far to drift semantically. 0.0 = nearest synonym, 1.0 = maximally distant. Default 0.3.
- `target_pos` (string): Comma-separated POS tags to drift. Default `"NN,NNS,JJ,VB,VBD,VBG"`.
- `seed` (int): Random seed. -1 = truly random.

**Input:** List of strings  
**Output:** List of strings with drifted vocabulary  
**Implementation:**
1. POS-tag input
2. For each target word, with probability `drift_rate`:
   a. Get word vector
   b. Find N most similar words (Gensim `most_similar`)
   c. Select replacement based on `drift_distance`: low distance = pick from top similar, high distance = pick from bottom of similarity list
   d. Substitute, preserving original capitalization
3. For iterative drift, feed output back through a Looper node

**Example (drift_rate 0.2, drift_distance 0.3, single pass):**  
Input: `"The tired surgeon stitched the wound"`  
Output: `"The weary surgeon sutured the wound"` (first pass — subtle)  
After 5 Looper passes: `"The exhausted tailor mended the fabric"` (drifted far)

#### 16. Coherence Gate Node

**Purpose:** Score text for semantic coherence and filter. Controls the sweet spot between "too sensible" and "too random."  
**Parameters:**
- `min_coherence` (float): Minimum coherence score to pass. Default 0.1.
- `max_coherence` (float): Maximum coherence score to pass. Default 0.7.
- `window` (int): Number of consecutive words to compare. Default 3.

**Input:** List of strings  
**Output:** List of strings that fall within the coherence window  
**Implementation:**
1. For each sentence, compute pairwise cosine similarity between consecutive word vectors (sliding window of size `window`)
2. Average similarity = coherence score (0 = random word soup, 1 = perfectly coherent)
3. Pass strings where `min_coherence <= score <= max_coherence`

The sweet spot for "decaffeinating a hermit crab" style absurdity is roughly 0.15–0.45: enough structure that it reads as English, enough wrongness that it surprises.

---

## Phase 5–6 Recipe Workflows

Add to `examples/recipes/`:

- `semantic_decay.json` — FileIn → Looper (10 iterations) → Semantic Drift (rate 0.1, distance 0.4) → Coherence Gate (0.15–0.5) → output. Watch text melt.
- `tracery_salad.json` — Text node (containing grammar JSON) → Tracery Grammar (count 20) → Shuffle (sentences) → output.
- `deep_transplant.json` — FileIn (legal text) → Dependency Parse (skeleton mode) → skeleton path. FileIn (romance poetry) → Dependency Parse (flat mode) → Regex Replace (extract content words) → word pool path. Both into Skeleton Fill → Conjugation Fixer → Phonetic Filter (alliteration, threshold 0.2) → output.
- `fold_in_mashup.json` — FileIn (cookbook) and FileIn (marine biology) → Fold-In (words mode, split 0.5) → Repetition Injector (phrase mode, density 0.1) → Conjugation Fixer → output.
- `the_full_salad.json` — The maximalist pipeline: FileIn → Skeleton Extract → fill with Markov-generated words → Fold-In with a second corpus → Repetition Injector → Coherence Gate → Conjugation Fixer → Phonetic Filter → output. The everything bagel.

---

## Execution Order

```
Phase 4 (nodes 8-10) → test → Phase 4 (node 11) → test
→ Phase 5 (spaCy install + nodes 12-14) → test
→ Phase 6 (Gensim install + nodes 15-16) → test
→ Phase 5-6 recipe workflows → final integration test
```

---

## Node Count Summary

| Phase | Nodes | Dependencies |
|-------|-------|-------------|
| Phase 0 | 0 (rebrand only) | none |
| Phase 1 | 7 (Shuffle, Interleave, N+7, Markov Train, Markov Generate, Skeleton Extract, Skeleton Fill) | nltk, markovify |
| Phase 4 | 4 (Regex Replace, Fold-In, Repetition Injector, Tracery Grammar) | none new |
| Phase 5 | 3 (Dependency Parse, Conjugation Fixer, Phonetic Filter) | spacy |
| Phase 6 | 2 (Semantic Drift, Coherence Gate) | gensim |
| **Total** | **16 new nodes** | |

Combined with Text Loom's original 10 nodes, Salad Loom ships with **26 node types**.

---

## What's Deliberately Left Out

- **LLM-based nodes** — Text Loom's Query node already handles this. Use it for any task that needs an LLM (creative expansion, style transfer, evaluation). No need to duplicate.
- **Web scraping / live corpus fetching** — Out of scope. Users provide their own text files.
- **Audio/TTS** — Out of scope. Text only.
- **Visual node editor improvements** — Out of scope for this spec. The existing GUI works.
- **Word embedding training** — Use pre-trained models only. Training is too slow for interactive use.
