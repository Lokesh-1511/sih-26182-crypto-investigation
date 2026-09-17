# VASP Attribution Engine Specification

**Module:** `backend/app/attribution/`  
**Owner:** Member 2  
**Document Version:** 1.0.0

---

## 1. Mathematical Scoring Formulation

The VASP Attribution Engine calculates a transparent, multi-factor confidence score $S \in [0, 100]$ for candidate exchanges:

$$S = \min\left(100, \max\left(0, \sum_{i=1}^{5} w_i F_i - P_{\text{uncertainty}}\right)\right)$$

### Factor Breakdown ($F_i$)
1. **$F_{\text{entity}}$ — Known Deposit Match ($w_1 = 30$)**:
   - Explicit match where destination address matches verified deposit wallet infrastructure associated with the VASP.
2. **$F_{\text{sweep}}$ — Repeated Consolidation Sweep ($w_2 = 25$)**:
   - Destination address exhibits automated sweep transactions forwarding balances directly into the VASP's omnibus hot wallet within short intervals ($< 6\text{ hours}$).
3. **$F_{\text{proximity}}$ — Graph Proximity ($w_3 = 20$)**:
   - Scaled inversely with hop distance: $F_{\text{proximity}} = \frac{1}{\text{hop\_distance}}$. Hop 1 = 20 pts, Hop 2 = 15 pts, Hop 3 = 10 pts, Hop 4 = 5 pts.
4. **$F_{\text{volume}}$ — Flow Volume Strength ($w_4 = 15$)**:
   - Proportion of suspect wallet's initial outgoing funds that terminate at this VASP cluster: $\frac{\text{Volume to VASP}}{\text{Total Suspect Outflow}} \times 15$.
5. **$F_{\text{temporal}}$ — Temporal Consistency ($w_5 = 10$)**:
   - Fund flow occurred in sequential, direct forward chronological order with low latency between hops.

### Uncertainty Penalties ($P_{\text{uncertainty}}$)
- **Mixer/Tumbler Traversal**: $-30\text{ pts}$ (severe anonymization penalty).
- **Unverified Bridge Contract**: $-15\text{ pts}$ (cross-chain hop uncertainty).
- **High Fan-out Layering ($\ge 8\text{ hops/branches}$)**: $-10\text{ pts}$.

### Calibrated Confidence Bands
- **HIGH CONFIDENCE**: $S \ge 75\%$
- **MEDIUM CONFIDENCE**: $50\% \le S < 75\%$
- **LOW CONFIDENCE**: $S < 50\%$

---

## 2. Signature Feature: Counterfactual Attribution (Sensitivity Analysis)

To prevent brittle attributions based on a single data point, the engine provides a counterfactual simulation:
- Simulates the exclusion of key evidence factors (e.g. "What if the deposit match was incorrect?").
- Recomputes the score:
  $$\Delta S = S_{\text{original}} - S_{\text{counterfactual}}$$
- If $\Delta S \le 25\text{ pts}$ and the VASP remains #1, the attribution is deemed **ROBUST** across independent signals. If $\Delta S > 40\text{ pts}$ and ranking collapses, the attribution is flagged as **HIGHLY SENSITIVE TO SINGLE SIGNAL**.
