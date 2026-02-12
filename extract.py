import json
import os
import random

from ollama import chat
from pydantic import BaseModel

from dataset import DATA_PATH, load_processed, load_ticket_dataset

MODEL = "qwen2.5:7b"
OUT_PATH = "data/extractions.jsonl"

EXTRACT_PROMPT = """Extract entities from this support ticket. Return JSON only.

SUBJECT: {subject}

BODY: {body}

ANSWER: {answer}

Extract:
- product_or_service: the product or service (single string, empty if unclear)
- issues: short issue labels (e.g., "login problem", "service down")
- error_codes: any error codes mentioned
- procedures: resolution steps from the answer (e.g., "reset password", "clear cache")
- confidence: 0-1 scores for product, issues, procedures (how confident the extraction is)
"""


class Confidence(BaseModel):
    product: float
    issues: float
    procedures: float


class Extracted(BaseModel):
    product_or_service: str
    issues: list[str]
    error_codes: list[str]
    procedures: list[str]
    confidence: Confidence


def extract_one(subject: str, body: str, answer: str, model: str = MODEL) -> Extracted:
    prompt = EXTRACT_PROMPT.format(subject=subject, body=body, answer=answer)
    response = chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format=Extracted.model_json_schema(),
        options={"temperature": 0},
    )
    return Extracted.model_validate_json(response.message.content)


def preview_extraction(n: int = 3, model: str = MODEL) -> None:
    ds = load_processed() if os.path.exists(DATA_PATH) else load_ticket_dataset()
    indices = random.sample(range(len(ds)), min(n, len(ds)))
    for i in indices:
        row = ds[i]
        ext = extract_one(row["subject_stripped"], row["body_stripped"], row["answer_stripped"], model=model)
        print("=" * 70)
        print(f"TICKET {row['ticket_id']}")
        print("ORIGINAL:\nSubject:", row["subject_stripped"], "\nBody:", row["body_stripped"], "\nAnswer:", row["answer_stripped"])
        print("EXTRACTED:", ext.model_dump())
        print()


def extract_all(limit: int | None = None, model: str = MODEL, out_path: str = OUT_PATH) -> None:
    ds = load_processed() if os.path.exists(DATA_PATH) else load_ticket_dataset()
    n = min(limit or len(ds), len(ds))
    dirname = os.path.dirname(out_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(out_path, "w") as f:
        for i in range(n):
            row = ds[i]
            ext = extract_one(row["subject_stripped"], row["body_stripped"], row["answer_stripped"], model=model)
            f.write(json.dumps({"ticket_id": row["ticket_id"], **ext.model_dump()}) + "\n")


if __name__ == "__main__":
    preview_extraction(n=3)
