# Explaining the project without pretending to know more than you do

## Thirty-second explanation

I independently implemented analytical Black-Scholes, explicit finite
differences, Crank-Nicolson, and Monte Carlo pricing for European options. I
tested the numerical methods against the analytical benchmark, reproduced the
paper's parameter cases, and audited its tables. The standard finite-difference
methods were accurate, but several reported exact values were inconsistent with
the stated parameters. Because the proposed MCFDM was underspecified, I reported
that limitation and performed a transparent convection sensitivity analysis
instead of forcing a match.

## Questions you must be able to answer

1. What contract is being priced?
2. Why is the analytical Black-Scholes value used as the benchmark?
3. What do asset-price steps and time steps represent?
4. Why does FDM start from the expiry payoff and work backward?
5. How do explicit FDM, Crank-Nicolson, and Monte Carlo differ?
6. What errors or ambiguities did the replication identify?
7. Which assumptions did you add because the paper did not specify them?

Study `MATH_GUIDE.md` and the notebooks until you can answer each question in
your own words. Do not claim that you derived the PDE from first principles.
