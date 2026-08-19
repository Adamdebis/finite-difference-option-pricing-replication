# Mathematics guide: from fundamentals to the paper

This guide is designed to be studied after the code is running. It assumes only
basic single-variable calculus and introduces each extra idea when needed.

## 1. The financial contract

A European call pays `max(S_T - K, 0)` at expiry. A European put pays
`max(K - S_T, 0)`. Here `S_T` is the asset price at expiry and `K` is the strike.

## 2. A function of price and time

Write the option value as `V(S, t)`. It depends on two inputs: asset price `S`
and time `t`. A partial derivative is an ordinary rate of change while the other
input is temporarily held fixed.

- `dV/dt`: change in option value as time changes.
- `dV/dS`: slope of option value as the asset price changes (Delta).
- `d2V/dS2`: curvature of that slope (Gamma).

## 3. The Black-Scholes PDE

The pricing equation is

`dV/dt + 0.5*sigma^2*S^2*d2V/dS2 + r*S*dV/dS - r*V = 0`.

- The time term tracks movement toward expiry.
- The second-derivative term represents diffusion caused by volatility.
- The first-derivative term is the convection or directional-flow term.
- The final term discounts value at the risk-free rate.

## 4. Finite differences

The computer stores option values at neighbouring asset prices. If the spacing
is `dS`, the central approximations are

`dV/dS approximately (V_right - V_left) / (2*dS)`

and

`d2V/dS2 approximately (V_right - 2*V_centre + V_left) / dS^2`.

Substituting these expressions into the PDE produces weights multiplying the
left, centre, and right grid values. That is the origin of the `a`, `b`, and `c`
arrays in the code.

## 5. Working backward

The payoff is known at expiry but today's option price is unknown. The solver
starts from the payoff and works backward through the time grid until it reaches
today.

## 6. Explicit versus Crank-Nicolson

- Explicit FDM calculates the next layer directly from the previous layer. It
  is intuitive but requires sufficiently small time steps for stability.
- Crank-Nicolson averages the PDE between two time layers. Each step requires a
  tridiagonal linear-system solve, connecting the method to linear algebra.

## 7. Monte Carlo

Monte Carlo simulates many possible terminal prices under the risk-neutral
model, calculates each payoff, discounts the average, and reports sampling
uncertainty. Increasing the number of paths reduces noise but increases runtime.

## 8. The paper's convection adjustment

The paper proposes modifying the `r*S*dV/dS` term using a tuning function
`theta(S)`. Because several operators and the function used to construct theta
are not fully specified, this repository studies transparent fixed multipliers
around `theta = 1` rather than claiming an exact reconstruction.

## 9. What to learn from the differential-equations notes

Prioritise rates of change, Euler's method, initial/boundary conditions, and
stability of numerical steps. Those topics build intuition for the time-stepping
logic. Partial differential equations and finite-difference stencils are the
additional bridge supplied by this guide and the notebooks.
