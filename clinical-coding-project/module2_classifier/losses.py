"""
Loss functions for the "Long-Tail Rare-Code Failure" problem (Section VI,
Gap 2). Plain BCE optimizes for common codes; focal loss and class-weighted
BCE down-weight easy/common examples so the model keeps learning signal
from rare codes.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    """
    Multi-label focal loss. gamma > 0 down-weights well-classified examples
    (mostly frequent codes); alpha optionally rebalances positive/negative.
    """
    def __init__(self, gamma: float = 2.0, alpha: float = 0.25, reduction: str = "mean"):
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        probs = torch.sigmoid(logits)
        p_t = probs * targets + (1 - probs) * (1 - targets)
        focal_term = (1 - p_t) ** self.gamma
        alpha_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)
        loss = alpha_t * focal_term * bce

        if self.reduction == "mean":
            return loss.mean()
        if self.reduction == "sum":
            return loss.sum()
        return loss


def class_weighted_bce(logits: torch.Tensor, targets: torch.Tensor,
                        pos_weight: torch.Tensor) -> torch.Tensor:
    """
    Standard weighted BCE. pos_weight[c] should be roughly
    (num_negatives_for_c / num_positives_for_c), computed once from the
    training label distribution, so rare codes get a bigger gradient when
    the model misses them.
    """
    return F.binary_cross_entropy_with_logits(logits, targets, pos_weight=pos_weight)
