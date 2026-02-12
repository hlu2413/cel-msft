import hashlib
import os
import re
import unicodedata

from datasets import load_dataset, load_from_disk

DATA_PATH = "data/processed"
from talon import quotations
from talon.signature.bruteforce import extract_signature

TEXT_FIELDS = frozenset([
    "subject", "body", "answer", "type", "queue", "priority", "language",
    "tag_1", "tag_2", "tag_3", "tag_4", "tag_5", "tag_6", "tag_7", "tag_8",
])
CONTENT_FIELDS = ("subject", "body", "answer")


def _canonicalize(text):
    s = unicodedata.normalize("NFKC", text)
    s = s.encode("utf-8", errors="replace").decode("utf-8")
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in s.split("\n")]
    out, blank_count = [], 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count <= 2:
                out.append("")
        else:
            blank_count = 0
            out.append(line)
    return "\n".join(out).strip()


def _strip_boilerplate(text):
    if not text:
        return ""
    reply = quotations.extract_from_plain(text)
    body, _ = extract_signature(reply)
    return (body or "").strip()


def _process(rows):
    n = len(rows["subject"])
    out = {k: [] for k in rows}
    out["ticket_id"], out["content_hash"], out["null_fields"] = [], [], []
    for f in CONTENT_FIELDS:
        out[f + "_cleaned"], out[f + "_stripped"] = [], []
    for i in range(n):
        parts, nulls = [], []
        for k in rows:
            v = rows[k][i]
            if k in TEXT_FIELDS:
                s = "" if v is None else str(v)
                if v is None:
                    nulls.append(k)
                out[k].append(s)
                if k in CONTENT_FIELDS:
                    parts.append(s)
                    cleaned = _canonicalize(s)
                    out[k + "_cleaned"].append(cleaned)
                    out[k + "_stripped"].append(_strip_boilerplate(cleaned))
            else:
                out[k].append(v)
        out["ticket_id"].append(i)
        out["content_hash"].append(hashlib.sha256("".join(parts).encode()).hexdigest())
        out["null_fields"].append(nulls)
    return out


def load_ticket_dataset(save=True):
    ds = load_dataset("Tobi-Bueck/customer-support-tickets")
    ds = ds["train"].map(_process, batched=True, desc="Standardizing")
    if save:
        os.makedirs(DATA_PATH, exist_ok=True)
        ds.save_to_disk(DATA_PATH)
    return ds


def load_processed(path=DATA_PATH):
    return load_from_disk(path)


if __name__ == "__main__":
    load_ticket_dataset()