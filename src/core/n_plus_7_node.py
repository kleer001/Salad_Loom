import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType

# NLTK imports — downloaded on first run via install.sh or NLTK download step
import nltk

_NOUN_TAGS = {"NN", "NNS", "NNP", "NNPS"}
_VERB_TAGS = {"VB", "VBD", "VBG", "VBN", "VBP", "VBZ"}
_ADJ_TAGS = {"JJ", "JJR", "JJS"}

_DEFAULT_DICT = Path(__file__).parent.parent.parent / "data" / "dictionaries" / "english_common.txt"


class NPlus7Node(Node):
    """Replace words with the Nth word after them in a dictionary (Oulipo N+7 technique).

    offset: How many entries to skip in the sorted dictionary. Default 7.
    target_pos: Which parts of speech to replace — 'nouns', 'verbs', 'adjectives', 'all'.
    dictionary: Path to a sorted word list (one word per line). Defaults to bundled list.
    """

    GLYPH = '+7'
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = True
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None
        self._dictionary: Optional[List[str]] = None
        self._dictionary_path: Optional[str] = None

        self._parms.update({
            "offset": Parm("offset", ParameterType.INT, self),
            "target_pos": Parm("target_pos", ParameterType.STRING, self),
            "dictionary": Parm("dictionary", ParameterType.STRING, self),
        })
        self._parms["offset"].set(7)
        self._parms["target_pos"].set("nouns")
        self._parms["dictionary"].set("")

    def _load_dictionary(self, path_str: str) -> List[str]:
        if path_str:
            p = Path(path_str)
        else:
            p = _DEFAULT_DICT
        if not p.exists():
            return []
        with open(p, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]

    def _get_dictionary(self, path_str: str) -> List[str]:
        if self._dictionary is None or self._dictionary_path != path_str:
            self._dictionary = self._load_dictionary(path_str)
            self._dictionary_path = path_str
        return self._dictionary

    def _find_shifted_word(self, word: str, dictionary: List[str], offset: int) -> str:
        lower = word.lower()
        # Binary search for the word or insertion point
        lo, hi = 0, len(dictionary)
        while lo < hi:
            mid = (lo + hi) // 2
            if dictionary[mid] < lower:
                lo = mid + 1
            else:
                hi = mid
        idx = lo
        new_idx = idx + offset
        if new_idx < len(dictionary):
            replacement = dictionary[new_idx]
            # Preserve original capitalisation
            if word[0].isupper():
                return replacement.capitalize()
            return replacement
        return word  # no replacement available — leave unchanged

    def _target_tags(self, target_pos: str):
        t = target_pos.strip().lower()
        if t == "nouns":
            return _NOUN_TAGS
        if t == "verbs":
            return _VERB_TAGS
        if t == "adjectives":
            return _ADJ_TAGS
        return _NOUN_TAGS | _VERB_TAGS | _ADJ_TAGS  # 'all'

    def _process_string(self, s: str, dictionary: List[str], offset: int, target_tags) -> str:
        try:
            tokens = nltk.word_tokenize(s)
            tagged = nltk.pos_tag(tokens)
        except Exception as e:
            return f"[N+7 error: {e}]"

        result = []
        for word, tag in tagged:
            if tag in target_tags and word.isalpha():
                result.append(self._find_shifted_word(word, dictionary, offset))
            else:
                result.append(word)

        # Detokenise — simple join, fix spaces before punctuation
        text = " ".join(result)
        for punct in (".", ",", "!", "?", ";", ":", ")", "]", "'s"):
            text = text.replace(" " + punct, punct)
        text = text.replace("( ", "(").replace("[ ", "[")
        return text

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        offset = self._parms["offset"].eval()
        target_pos = self._parms["target_pos"].eval()
        dict_path = self._parms["dictionary"].eval()

        input_data: List[str] = []
        if self.inputs():
            raw = self.inputs()[0].output_node().eval(requesting_node=self)
            input_data = [str(x) for x in raw] if isinstance(raw, list) else []

        dictionary = self._get_dictionary(dict_path)
        if not dictionary:
            self._output = ["[N+7 error] Dictionary not found or empty"]
            self.set_state(NodeState.UNCHANGED)
            self._last_cook_time = (time.time() - start_time) * 1000
            return

        target_tags = self._target_tags(target_pos)
        self._output = [self._process_string(s, dictionary, offset, target_tags) for s in input_data]

        self._param_hash = self._calculate_hash(str(offset) + target_pos + dict_path)
        self._input_hash = self._calculate_hash(str(input_data))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            offset = self._parms["offset"].raw_value()
            target_pos = self._parms["target_pos"].raw_value()
            dict_path = self._parms["dictionary"].raw_value()
            new_param_hash = self._calculate_hash(str(offset) + str(target_pos) + str(dict_path))
            input_data = self.inputs()[0].output_node().get_output() if self.inputs() else []
            new_input_hash = self._calculate_hash(str(input_data))
            return new_input_hash != self._input_hash or new_param_hash != self._param_hash
        except Exception:
            return True

    def _calculate_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def input_names(self) -> Dict[int, str]:
        return {0: "Input Text"}

    def output_names(self) -> Dict[int, str]:
        return {0: "N+7 Text"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
