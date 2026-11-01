# Runbook

1. Create and activate a Python virtual environment.
2. Install `requirements.txt`.
3. Run `python scripts/generate_data.py --seed 20261022`.
4. Inspect CSV exports under `data/csv/`.
5. Inspect labelled exceptions in `data/ground_truth/ground_truth.csv`.
6. Start API with `uvicorn app.main:app --reload`.
7. Test APIs at `/docs`.
8. Run `pytest -q`.
9. Re-run generator with the same seed and compare `data/source_manifest.json`.
