"""Run the complete numerical replication from the repository root."""

from src.replication import run_full_replication


if __name__ == "__main__":
    outputs = run_full_replication("results")
    print("Replication completed.")
    print(f"Paper-audit rows: {len(outputs['audit'])}")
    print(f"Method-comparison rows: {len(outputs['comparison'])}")
    print(f"Sensitivity rows: {len(outputs['sensitivity'])}")
