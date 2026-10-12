"""
Format/validity checks against the authorized ICD-10-CM release
(Section VI-F Module 3, Section VIII).

Load a real code list (e.g. the CMS ICD-10-CM order file) into
valid_codes.txt, one code per line, before using this in production. The
sample file here has a handful of illustrative codes only.
"""
import os
import re

CODE_PATTERN = re.compile(r"^[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?$")

_DEFAULT_CODE_LIST = os.path.join(os.path.dirname(__file__), "valid_codes_sample.txt")


class ICDOntology:
    def __init__(self, code_list_path: str = _DEFAULT_CODE_LIST):
        self.valid_codes = self._load_codes(code_list_path)

    @staticmethod
    def _load_codes(path: str) -> set:
        if not os.path.exists(path):
            return set()
        with open(path) as f:
            return {line.strip() for line in f if line.strip()}

    def is_syntactically_valid(self, code: str) -> bool:
        """Type-I hallucination check: does the string even look like an ICD-10-CM code?"""
        return bool(CODE_PATTERN.match(code))

    def is_in_current_release(self, code: str) -> bool:
        """Is this code actually in the authorized release we loaded?"""
        if not self.valid_codes:
            # No ontology loaded yet -- don't silently pass everything.
            raise RuntimeError(
                "No ICD code list loaded. Populate valid_codes_sample.txt "
                "or pass a real code_list_path to ICDOntology()."
            )
        return code in self.valid_codes
