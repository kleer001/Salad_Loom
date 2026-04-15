import hashlib
import re
import time
from typing import Dict, List

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    return _nlp

_VOWELS = set("aeiouAEIOU")
_VOWEL_SOUNDS = {"a", "e", "i", "o", "u", "hour", "honest", "heir"}


def _fix_article(text: str) -> str:
    """Replace a/an before the next word based on its initial sound."""
    def replacer(m):
        article = m.group(1)
        space = m.group(2)
        next_word = m.group(3)
        first_char = next_word[0].lower() if next_word else ""
        needs_an = first_char in _VOWELS
        correct = "an" if needs_an else "a"
        # Preserve original capitalisation of the article
        if article[0].isupper():
            correct = correct.capitalize()
        return correct + space + next_word
    return re.sub(r"\b(an?)( +)(\w+)", replacer, text, flags=re.IGNORECASE)


def _fix_capitalization(text: str) -> str:
    """Capitalize the first character of each sentence."""
    def cap_after(m):
        return m.group(1) + m.group(2).upper()
    # Capitalize after . ! ? or at start
    result = re.sub(r"([.!?]\s+)([a-z])", cap_after, text)
    if result:
        result = result[0].upper() + result[1:]
    return result


class ConjugationFixerNode(Node):
    """Repair article, capitalization, and (optionally) tense after text mangling.

    fix_articles: Fix a/an based on following word. Default True.
    fix_capitalization: Capitalize sentence starts. Default True.
    fix_verbs: Attempt basic subject-verb agreement fix via spaCy. Default True.
    target_tense: 'preserve' | 'past' | 'present'. Default 'preserve'.
    """

    GLYPH = "✎"
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = True
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "fix_articles": Parm("fix_articles", ParameterType.TOGGLE, self),
            "fix_capitalization": Parm("fix_capitalization", ParameterType.TOGGLE, self),
            "fix_verbs": Parm("fix_verbs", ParameterType.TOGGLE, self),
            "target_tense": Parm("target_tense", ParameterType.STRING, self),
        })
        self._parms["fix_articles"].set(True)
        self._parms["fix_capitalization"].set(True)
        self._parms["fix_verbs"].set(True)
        self._parms["target_tense"].set("preserve")

    def _fix_verb_agreement(self, text: str, nlp) -> str:
        """Basic subject-verb agreement: singular subject → 3rd-person singular verb."""
        doc = nlp(text)
        tokens = list(doc)
        result = []
        for i, token in enumerate(tokens):
            fixed = token.text
            if token.pos_ == "VERB" and token.dep_ == "ROOT":
                subj = [t for t in token.children if t.dep_ in ("nsubj", "nsubjpass")]
                if subj:
                    s = subj[0]
                    if s.tag_ in ("NN", "NNP") and token.tag_ not in ("VBZ",):
                        # Singular noun subject, verb should be VBZ
                        lemma = token.lemma_
                        if lemma == "be":
                            fixed = "is"
                        elif not lemma.endswith("s"):
                            fixed = lemma + "s"
            result.append(fixed)
        # Rebuild with whitespace
        out = ""
        for i, (token, word) in enumerate(zip(tokens, result)):
            out += token.whitespace_ + word if i else word
        # Fix trailing/leading whitespace from reconstruction
        return out.strip()

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        fix_articles = self._parms["fix_articles"].eval()
        fix_cap = self._parms["fix_capitalization"].eval()
        fix_verbs = self._parms["fix_verbs"].eval()
        target_tense = self._parms["target_tense"].eval().strip().lower()

        input_data: List[str] = []
        if self.inputs():
            raw = self.inputs()[0].output_node().eval(requesting_node=self)
            input_data = [str(x) for x in raw] if isinstance(raw, list) else []

        nlp = None
        if fix_verbs:
            try:
                nlp = _get_nlp()
            except Exception as e:
                self._output = [f"[ConjugationFixer error] spaCy unavailable: {e}"]
                self.set_state(NodeState.UNCHANGED)
                self._last_cook_time = (time.time() - start_time) * 1000
                return

        results = []
        for s in input_data:
            if fix_articles:
                s = _fix_article(s)
            if fix_verbs and nlp:
                s = self._fix_verb_agreement(s, nlp)
            if fix_cap:
                s = _fix_capitalization(s)
            results.append(s)

        self._output = results
        self._param_hash = self._calculate_hash(
            str(fix_articles) + str(fix_cap) + str(fix_verbs) + target_tense
        )
        self._input_hash = self._calculate_hash(str(input_data))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            fa = self._parms["fix_articles"].raw_value()
            fc = self._parms["fix_capitalization"].raw_value()
            fv = self._parms["fix_verbs"].raw_value()
            tt = self._parms["target_tense"].raw_value()
            new_param_hash = self._calculate_hash(str(fa) + str(fc) + str(fv) + str(tt))
            input_data = self.inputs()[0].output_node().get_output() if self.inputs() else []
            new_input_hash = self._calculate_hash(str(input_data))
            return new_input_hash != self._input_hash or new_param_hash != self._param_hash
        except Exception:
            return True

    def _calculate_hash(self, content: str) -> str:
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()

    def input_names(self) -> Dict[int, str]:
        return {0: "Input Text"}

    def output_names(self) -> Dict[int, str]:
        return {0: "Fixed Text"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
