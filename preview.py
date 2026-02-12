import os
import random

from dataset import DATA_PATH, load_processed, load_ticket_dataset


def main():
    ds = load_processed() if os.path.exists(DATA_PATH) else load_ticket_dataset()
    indices = random.sample(range(len(ds)), min(3, len(ds)))
    for i in indices:
        row = ds[i]
        print("=" * 60)
        print(f"ROW {i} (ticket_id={row['ticket_id']})")
        for field in ("subject", "body", "answer"):
            orig = row[field]
            cleaned = row[f"{field}_cleaned"]
            stripped = row[f"{field}_stripped"]
            print(f"\n--- {field.upper()} ---")
            print(f"ORIGINAL ({len(orig)} chars):\n{orig[:500]}{'...' if len(orig) > 500 else ''}")
            print(f"\nCLEANED ({len(cleaned)} chars):\n{cleaned[:500]}{'...' if len(cleaned) > 500 else ''}")
            print(f"\nSTRIPPED ({len(stripped)} chars):\n{stripped[:500]}{'...' if len(stripped) > 500 else ''}")
        print()


if __name__ == "__main__":
    main()
