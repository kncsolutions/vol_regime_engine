# Volatility Regime Engine

A quantitative framework for detecting dealer gamma regimes,
cross-asset fragility, and volatility surface shifts.

## Features
- Dealer Gamma Detection
- Flow Amplification Modeling
- Cross-Asset Flip Risk
- Early Crash Warning Signals
- State Transition Modeling

## Understanding Terminology
### Regime_score
$$
Γ=∂^2v/ds^2
$$
Aggregate dealer gamma exposure (GEX):
$$
GEX(S)=∑iΓi(S)⋅OIi⋅ContractSize
$$
$$
GEX(S)=
i
∑
	​

Γ
i
	​

(S)⋅OI
i
	​

⋅ContractSize

Your normalized gamma score likely resembles:

GammaScore=GEX∣GEX∣+λ
GammaScore=
∣GEX∣+λ
GEX
	​


or a z-score of GEX.

## Installation

```bash
git clone https://github.com/kncsolutions/vol_regime_engine.git
cd vol_regime_engine
pip install .