# GitHub workflow in plain English

## The four words

- **Save** writes the current file on your laptop.
- **Commit** creates a labelled local snapshot of selected changes.
- **Push** uploads your local commits to GitHub.
- **Pull** downloads commits that exist on GitHub but not on your laptop.

A commit is not "strong" or "weak" because of size. A good commit is one
coherent, tested change with a specific description.

## Safe working routine

1. Pull before starting if the repository was changed on GitHub or another device.
2. Work on one understandable change and save it.
3. Run the relevant notebook or tests.
4. Review the changed files in GitHub Desktop.
5. Commit with a specific summary.
6. Push the completed commit to GitHub.

## Suggested commit history for this project

1. `Define replication question and reproducibility rules`
2. `Add analytical Black-Scholes benchmark audit`
3. `Implement explicit and Crank-Nicolson FDM`
4. `Add reproducible Monte Carlo comparison`
5. `Document paper inconsistencies and convection sensitivity`
6. `Add tests, final figures, and project README`

## Before every push

- Confirm notebooks run from top to bottom.
- Run `python -m pytest -q`.
- Check that no passwords, API keys, personal files, or environment folders are selected.
- Keep the reference PDF local; the `.gitignore` excludes `references/*.pdf`.
- Read the diff instead of accepting AI-generated changes automatically.

## When to pull

Pull when you edited the repository on GitHub, used another computer, or worked
with a collaborator. If only you use one laptop and never edit files on the
GitHub website, there may be nothing new to pull.
