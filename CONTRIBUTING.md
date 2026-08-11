# Contributing to StockScreenerAI

Thank you for your interest in contributing to StockScreenerAI! This guide explains how to set up the project, make changes, and submit contributions.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/Stock-Market-Prediction-AI-ML.git
   cd Stock-Market-Prediction-AI-ML
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Branching

- Create a new branch for each feature or fix.
- Use descriptive branch names, such as `feature/add-gui-improvements` or `fix/indicator-bug`.

## Development Workflow

1. Make your code changes.
2. Run tests locally:
   ```bash
   python -m pytest -q
   ```
3. Check formatting if applicable and ensure your changes pass.
4. Commit your changes with a clear message:
   ```bash
   git add .
   git commit -m "Add short description of changes"
   ```
5. Push your branch to your fork:
   ```bash
   git push origin your-branch-name
   ```

## Pull Requests

- Open a Pull Request against the `master` branch of the upstream repository.
- Describe the change clearly in the PR title and description.
- Link any related issue if available.
- Keep changes focused and minimal per PR.

## Code Quality

- Prefer clear, readable code.
- Add or update tests for bug fixes and new features.
- Document any new behavior in `README.md` or relevant project files.

## Reporting Issues

If you find a bug or want to request a new feature, open an issue on GitHub with:
- A concise title
- A description of the problem or feature
- Steps to reproduce (for bugs)
- Expected behavior

## Notes

- This project currently uses Python and PyQt6.
- If you are modifying the GUI, verify the desktop app still launches after changes.
