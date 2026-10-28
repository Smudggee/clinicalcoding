from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")

from module2_classifier.inference import ClinicalInferenceEngine


class _Encoding(dict):
    def to(self, device):
        return self


class _Tokenizer:
    def __call__(self, *args, **kwargs):
        return _Encoding(
            input_ids=torch.zeros((1, 2), dtype=torch.long),
            attention_mask=torch.ones((1, 2), dtype=torch.long),
        )


class _Model:
    def predict_proba(self, input_ids, attention_mask):
        return torch.tensor([[0.91, 0.40, 0.12]])


def test_top_k_does_not_include_candidates_below_threshold():
    engine = ClinicalInferenceEngine.__new__(ClinicalInferenceEngine)
    engine.device = "cpu"
    engine.model = _Model()
    engine.tokenizer = _Tokenizer()
    engine.label_map = {"A41.9": 0, "J18.9": 1, "E11.9": 2}
    engine.id_to_label = {index: code for code, index in engine.label_map.items()}

    result = engine.predict(
        text_or_windows=[SimpleNamespace(text="sepsis evidence", start_token_offset=0, end_token_offset=2)],
        document_id="case-1",
        threshold=0.5,
        top_k=3,
    )

    assert [prediction.code for prediction in result.predictions] == ["A41.9"]
