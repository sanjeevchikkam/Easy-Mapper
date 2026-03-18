import re
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

def normalize_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

ABBREV_MAP = {
    r"\btab\b":  "tablet",
    r"\bcap\b":  "capsule",
    r"\binj\b":  "injection",
    r"\bsyp\b":  "syrup",
    r"\boint\b": "ointment",
}

def expand_abbreviations(text: str) -> str:
    for pattern, replacement in ABBREV_MAP.items():
        text = re.sub(pattern, replacement, text)
    return text

def preprocess(text: str) -> str:
    return expand_abbreviations(normalize_text(text))

MATCH_THRESHOLD = 70.0

def match_medicines(pharmacy_df: pd.DataFrame, master_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:

    pharmacy = pharmacy_df.copy()
    master   = master_df.copy()

    pharmacy["normalized_name"] = pharmacy["pharmacy_medicine_name"].apply(preprocess)
    master["normalized_name"]   = master["master_medicine_name"].apply(preprocess)

    pharmacy_embeddings = model.encode(
        pharmacy["normalized_name"].tolist(),
        show_progress_bar=False,
        batch_size=64
    )
    master_embeddings = model.encode(
        master["normalized_name"].tolist(),
        show_progress_bar=False,
        batch_size=64
    )

    similarity_matrix  = cosine_similarity(pharmacy_embeddings, master_embeddings)
    best_match_indices = similarity_matrix.argmax(axis=1)
    best_scores        = similarity_matrix.max(axis=1)

    pharmacy["master_id"]    = master.iloc[best_match_indices]["master_medicine_id"].values
    pharmacy["matched_name"] = master.iloc[best_match_indices]["master_medicine_name"].values
    pharmacy["score"]        = (best_scores * 100).round(2)

    below_threshold = pharmacy["score"] < MATCH_THRESHOLD
    pharmacy.loc[below_threshold, "master_id"]    = None
    pharmacy.loc[below_threshold, "matched_name"] = "NOT MATCHED"

    result = pharmacy[[
        "p_inv_id",
        "pharmacy_medicine_name",
        "master_id",
        "matched_name",
        "score"
    ]]
    
    total      = len(result)
    matched    = int((result["matched_name"] != "NOT MATCHED").sum())
    unmatched  = total - matched

    summary = {
        "total":     total,
        "matched":   matched,
        "unmatched": unmatched,
        "threshold": MATCH_THRESHOLD
    }

    return result, summary