
"""
ICD-10-CM code format and release validation.

The sample code list is for development/testing only.
Production use must load a verified, versioned ICD-10-CM code list.
"""
import os
import re

CODE_PATTERN = re.compile(
    r"^[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?$"
)

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_CODE_LIST = os.path.join(
    MODULE_DIR, "valid_codes_sample.txt"
)


class ICDOntology:
    def __init__(self, code_list_path=None, authoritative=False):
        self.code_list_path = code_list_path or _DEFAULT_CODE_LIST
        self.authoritative = authoritative
        self.valid_codes = self._load_codes(self.code_list_path)

    @staticmethod
    def _load_codes(path: str) -> set:
        if not path or not os.path.isfile(path):
            return set()

        with open(path, encoding="utf-8") as file:
            return {
                line.strip().upper()
                for line in file
                if line.strip() and not line.lstrip().startswith("#")
            }

    def is_syntactically_valid(self, code: str) -> bool:
        if not isinstance(code, str):
            return False
        return bool(CODE_PATTERN.fullmatch(code.strip().upper()))

    def is_in_current_release(self, code: str) -> bool:
        if not self.valid_codes:
            raise RuntimeError("ICD code list is missing or empty.")

        if not self.authoritative:
            raise RuntimeError(
                "Only a sample ICD code list is loaded; "
                "official release validation is unavailable."
            )

        return code.strip().upper() in self.valid_codes
