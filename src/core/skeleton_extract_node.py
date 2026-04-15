import hashlib
import time
from typing import Dict, List, Set

import nltk

from core.base_classes import Node, NodeType, NodeState
from core.enums import FunctionalGroup
from core.parm import Parm, ParameterType

_DEFAULT_PRESERVE = "DT,IN,CC,TO,PRP,MD"
_DEFAULT_SLOT_FORMAT = "[{tag}]"


class SkeletonExtractNode(Node):
    """POS-tag text and replace content words with tagged slots.

    preserve: Comma-separated POS tags to keep as-is.
              Default: 'DT,IN,CC,TO,PRP,MD' (function words).
    slot_format: Format string for slots. Default '[{tag}]'.
                 Can use '{tag}', '__{tag}__', etc.

    Example:
        Input:  "The old surgeon carefully stitched the wound"
        Output: "The [JJ] [NN] [RB] [VBD] the [NN]"
    """

    GLYPH = '⊠'
    GROUP = FunctionalGroup.TEXT
    SINGLE_INPUT = True
    SINGLE_OUTPUT = True

    def __init__(self, name: str, path: str, node_type: NodeType):
        super().__init__(name, path, [0.0, 0.0], node_type)
        self._input_hash = None
        self._param_hash = None

        self._parms.update({
            "preserve": Parm("preserve", ParameterType.STRING, self),
            "slot_format": Parm("slot_format", ParameterType.STRING, self),
        })
        self._parms["preserve"].set(_DEFAULT_PRESERVE)
        self._parms["slot_format"].set(_DEFAULT_SLOT_FORMAT)

    def _parse_preserve_tags(self, preserve_str: str) -> Set[str]:
        return {tag.strip() for tag in preserve_str.split(",") if tag.strip()}

    def _process_string(self, s: str, preserve_tags: Set[str], slot_format: str) -> str:
        try:
            tokens = nltk.word_tokenize(s)
            tagged = nltk.pos_tag(tokens)
        except Exception as e:
            return f"[SkeletonExtract error: {e}]"

        result = []
        for word, tag in tagged:
            if tag in preserve_tags or not word.isalpha():
                result.append(word)
            else:
                result.append(slot_format.format(tag=tag))

        # Detokenise — fix space before punctuation
        text = " ".join(result)
        for punct in (".", ",", "!", "?", ";", ":", ")", "]", "'s"):
            text = text.replace(" " + punct, punct)
        text = text.replace("( ", "(").replace("[ ", "[")
        return text

    def _internal_cook(self, force: bool = False) -> None:
        self.set_state(NodeState.COOKING)
        self._cook_count += 1
        start_time = time.time()

        preserve_str = self._parms["preserve"].eval()
        slot_format = self._parms["slot_format"].eval()
        preserve_tags = self._parse_preserve_tags(preserve_str)

        input_data: List[str] = []
        if self.inputs():
            raw = self.inputs()[0].output_node().eval(requesting_node=self)
            input_data = [str(x) for x in raw] if isinstance(raw, list) else []

        self._output = [self._process_string(s, preserve_tags, slot_format) for s in input_data]

        self._param_hash = self._calculate_hash(preserve_str + slot_format)
        self._input_hash = self._calculate_hash(str(input_data))
        self.set_state(NodeState.UNCHANGED)
        self._last_cook_time = (time.time() - start_time) * 1000

    def needs_to_cook(self) -> bool:
        if super().needs_to_cook():
            return True
        try:
            preserve_str = self._parms["preserve"].raw_value()
            slot_format = self._parms["slot_format"].raw_value()
            new_param_hash = self._calculate_hash(str(preserve_str) + str(slot_format))
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
        return {0: "Skeleton"}

    def input_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}

    def output_data_types(self) -> Dict[int, str]:
        return {0: "List[str]"}
