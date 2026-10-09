# Historical scripts

These scripts are archived because they are no longer called by the active GitHub Actions workflows. They are preserved for reference, **not** intended for routine execution.

- `add_kane_contrarian_once.py`: one-off market insertion.
- `fix_prediction_expand.py`: legacy HTML mutation.
- `patch_market_lock_display.py`: legacy HTML mutation.
- `patch_prediction_categories.py`: legacy HTML mutation.

Do not reintroduce HTML-mutating scripts into the hourly updater. The live workflow should modify `data/predictions.json` only.
