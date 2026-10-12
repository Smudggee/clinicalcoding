"""
Evaluation metrics from Section VII, implemented exactly as defined in the
paper so results are directly comparable to the reviewed literature.
"""
from typing import List, Dict
from sklearn.metrics import precision_score, recall_score, f1_score


def micro_macro_f1(y_true, y_pred) -> Dict[str, float]:
    """Eq. (2): F1 = 2PR / (P+R), reported at micro and macro level."""
    return {
        "precision_micro": precision_score(y_true, y_pred, average="micro", zero_division=0),
        "recall_micro": recall_score(y_true, y_pred, average="micro", zero_division=0),
        "f1_micro": f1_score(y_true, y_pred, average="micro", zero_division=0),
        "precision_macro": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
    }


def precision_at_k(ranked_codes: List[str], gold_codes: set, k: int) -> float:
    """Eq. (3): P@K = correct codes among top K / K."""
    if k == 0:
        return 0.0
    top_k = ranked_codes[:k]
    correct = sum(1 for c in top_k if c in gold_codes)
    return correct / k


def hallucination_error_rate(n_invalid: int, n_predicted: int) -> float:
    """Eq. (4): HER = (N_invalid / N_predicted) * 100."""
    if n_predicted == 0:
        return 0.0
    return (n_invalid / n_predicted) * 100


def valid_code_rejection_rate(n_valid_rejected: int, n_valid_reference: int) -> float:
    """Eq. (5): VRR = (N_valid_codes_rejected / N_valid_reference_codes) * 100."""
    if n_valid_reference == 0:
        return 0.0
    return (n_valid_rejected / n_valid_reference) * 100


def stratify_by_frequency(codes: List[str], code_counts: Dict[str, int],
                           common_threshold: int = 100, rare_threshold: int = 10) -> Dict[str, List[str]]:
    """
    Section VII-C: bucket codes into common / medium / rare by training-set
    frequency, so metrics can be reported per-bucket rather than as one
    aggregate that hides rare-code failure.
    """
    buckets = {"common": [], "medium": [], "rare": []}
    for code in codes:
        count = code_counts.get(code, 0)
        if count >= common_threshold:
            buckets["common"].append(code)
        elif count >= rare_threshold:
            buckets["medium"].append(code)
        else:
            buckets["rare"].append(code)
    return buckets
