# backend/app/attribution/counterfactual.py
from typing import List
from ..schemas.attribution import VASPAttributionCandidate, CounterfactualResult

class CounterfactualEngine:
    """
    Counterfactual Attribution & Sensitivity Analysis Engine.
    Simulates: What happens to attribution confidence if a major clue is removed?
    """

    @classmethod
    def simulate_ablation(
        cls, candidate: VASPAttributionCandidate
    ) -> List[CounterfactualResult]:
        results: List[CounterfactualResult] = []
        original_score = candidate.confidence_score

        for factor in candidate.factors:
            if factor.factor_type == "POSITIVE" and factor.contribution_points > 0:
                ablated_score = max(0.0, original_score - factor.contribution_points)
                delta = round(original_score - ablated_score, 1)

                if delta <= 15.0:
                    robustness = "ROBUST"
                elif delta <= 28.0:
                    robustness = "MODERATE_DEPENDENCY"
                else:
                    robustness = "HIGH_DEPENDENCY"

                results.append(CounterfactualResult(
                    factor_removed=factor.factor_name,
                    original_score=original_score,
                    new_score=ablated_score,
                    score_delta=delta,
                    robustness_evaluation=robustness
                ))

        return results
