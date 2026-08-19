# Paper audit and replication limits

This project critically evaluates An Ning (2023), *A Mean Convection Finite
Difference Method for Solving Black Scholes Model for Option Pricing*,
arXiv:2308.06808.

## Reproducibility limitations

The paper does not provide source code, a random seed, the upper asset-price
boundary, or complete definitions of the flux operators `D` and `Phi`.
Although it introduces a tuning function `theta(S)`, the function `alpha(S)`
inside its definition is described qualitatively rather than specified in a
form that uniquely determines the reported numbers. The paper also alternates
between the labels MCFDM and UCFDM.

Consequently, this repository does **not** claim an exact reconstruction of the
reported MCFDM. It implements standard analytical Black-Scholes, explicit FDM,
Crank-Nicolson, and Monte Carlo methods, then adds a clearly labelled
paper-inspired sensitivity experiment that scales the convection term.

## Numerical inconsistencies investigated

1. In Tables 1 and 2, the reported one-year exact call values agree with the
   standard Black-Scholes formula, while the reported six-month values do not
   agree under the stated parameters.
2. Tables 3 and 4 are labelled as put-option results. However, their reported
   exact values are close to **call** prices using the spot and strike values
   stated in the surrounding narrative, and are far from standard put prices.
3. The paper's reported Crank-Nicolson results could not be reproduced using a
   conventional, well-resolved Crank-Nicolson implementation with the stated
   100 asset steps and 1,000 time steps.
4. Runtime figures depend on hardware, software, implementation detail, and
   random-number generation. This project records fresh local timings but does
   not treat them as directly comparable with Table 5.

These findings are presented as replication observations, not allegations
about the author's intent.
