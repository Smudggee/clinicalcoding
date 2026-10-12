from evaluation.metrics import (
    micro_macro_f1, precision_at_k, hallucination_error_rate,
    valid_code_rejection_rate, stratify_by_frequency,
)


def test_precision_at_k():
    ranked = ["A41.9", "E11.9", "I10", "J18.9"]
    gold = {"A41.9", "J18.9"}
    assert precision_at_k(ranked, gold, k=2) == 0.5
    assert precision_at_k(ranked, gold, k=4) == 0.5


def test_hallucination_error_rate():
    assert hallucination_error_rate(n_invalid=2, n_predicted=20) == 10.0
    assert hallucination_error_rate(n_invalid=0, n_predicted=0) == 0.0


def test_valid_code_rejection_rate():
    assert valid_code_rejection_rate(n_valid_rejected=1, n_valid_reference=10) == 10.0


def test_stratify_by_frequency():
    counts = {"common1": 500, "medium1": 50, "rare1": 3}
    buckets = stratify_by_frequency(
        ["common1", "medium1", "rare1"], counts,
        common_threshold=100, rare_threshold=10,
    )
    assert buckets["common"] == ["common1"]
    assert buckets["medium"] == ["medium1"]
    assert buckets["rare"] == ["rare1"]


def test_micro_macro_f1_shapes():
    y_true = [[1, 0], [0, 1]]
    y_pred = [[1, 0], [0, 1]]
    result = micro_macro_f1(y_true, y_pred)
    assert result["f1_micro"] == 1.0
    assert result["f1_macro"] == 1.0
