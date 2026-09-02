# Penn Treebank POS Tags — Salad Loom Reference

The canonical preserve list for `SkeletonExtractNode` is defined as `_DEFAULT_PRESERVE`
in `src/core/skeleton_extract_node.py`. Recipe JSON files that override it should use
this list (or a deliberate subset/superset of it).

## Canonical Preserve List

```
DT,IN,CC,TO,PRP,PRP$,MD,WP,WP$,WDT,WRB,RP,EX,UH,CD,NNP,NNPS,PDT,FW,LS,SYM,RB,RBR,RBS,JJR,JJS
```

These are **closed-class / structural** words — they belong to the source text's
scaffold and cannot be meaningfully substituted with domain vocabulary.

## Tag Reference

### Preserved by default (closed-class / structural)

| Tag   | Name                         | Example                    |
|-------|------------------------------|----------------------------|
| DT    | Determiner                   | the, a, an, each           |
| IN    | Preposition / subordinator   | of, in, on, that           |
| CC    | Coordinating conjunction     | and, but, or               |
| TO    | to                           | to                         |
| PRP   | Personal pronoun             | he, she, it, they          |
| PRP$  | Possessive pronoun           | his, her, my, their        |
| MD    | Modal                        | would, could, should, will |
| WP    | Wh-pronoun                   | who, what                  |
| WP$   | Possessive wh-pronoun        | whose                      |
| WDT   | Wh-determiner                | which, that                |
| WRB   | Wh-adverb                    | where, when, how, why      |
| RP    | Particle                     | up, out, off, in           |
| EX    | Existential there            | there (as in "there is")   |
| UH    | Interjection                 | oh, ah, well, hmm          |
| CD    | Cardinal number              | one, 42, three-hundred     |
| NNP   | Proper noun singular         | London, Mary, Thursday     |
| NNPS  | Proper noun plural           | Vikings, Tuesdays          |
| PDT   | Predeterminer                | all, both, half            |
| FW    | Foreign word                 | bon, schadenfreude         |
| LS    | List item marker             | 1., A., first              |
| SYM   | Symbol                       | $, %, @, +                 |
| RB    | Adverb                       | quickly, carefully, not    |
| RBR   | Comparative adverb           | faster, more carefully     |
| RBS   | Superlative adverb           | fastest, most carefully    |
| JJR   | Comparative adjective        | bigger, more tender        |
| JJS   | Superlative adjective        | biggest, most tender       |

### Replaced with slots (open-class / content words)

These are filled by the word pool in `SkeletonFillNode`.

| Tag   | Name                         | Example                    |
|-------|------------------------------|----------------------------|
| NN    | Noun singular                | whale, reduction, surgeon  |
| NNS   | Noun plural                  | whales, reductions         |
| VB    | Verb base form               | swim, braise, run          |
| VBD   | Verb past tense              | swam, braised, ran         |
| VBG   | Verb gerund / present part.  | swimming, braising         |
| VBN   | Verb past participle         | swum, braised, eaten       |
| VBP   | Verb non-3rd-person present  | swim, braise (I swim)      |
| VBZ   | Verb 3rd-person present      | swims, braises, runs       |
| JJ    | Adjective                    | statutory, golden, briny   |

## DRY Note

The canonical value lives in `_DEFAULT_PRESERVE` (one place). Recipe JSON files
always serialize their parameter values explicitly, so duplication across `.json`
files is unavoidable in the current architecture — but all overrides should match
or consciously extend the canonical list above.

Word pool files (`data/corpora/marine_words.txt`, `legal_adjectives.txt`,
`cookbook_words.txt`) must cover **all open-class tags** listed above (NN, NNS,
VB, VBD, VBG, VBN, VBP, VBZ, JJ) to avoid leaving unfilled slot tags in output.
