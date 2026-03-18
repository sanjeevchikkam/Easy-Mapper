import re
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ── Same model, already cached from pharmacy matching
model = SentenceTransformer("all-MiniLM-L6-v2")


def normalize_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── Lab test specific abbreviations
ABBREV_MAP = {
    r"\bcbc\b":   "complete blood count",
    r"\blft\b":   "liver function test",
    r"\brft\b":   "renal function test",
    r"\bkft\b":   "kidney function test",
    r"\btsh\b":   "thyroid stimulating hormone",
    r"\bft3\b":   "free triiodothyronine",
    r"\bft4\b":   "free thyroxine",
    r"\bhba1c\b": "glycated hemoglobin",
    r"\becg\b":   "electrocardiogram",
    r"\busg\b":   "ultrasound",
    r"\bmri\b":   "magnetic resonance imaging",
    r"\bct\b":    "computed tomography",
    r"\burine re\b": "urine routine examination",
    r"\bbs\b":    "blood sugar",
    r"\bfbs\b":   "fasting blood sugar",
    r"\bppbs\b":  "postprandial blood sugar",
    r"\brbs\b":   "random blood sugar",
    r"\besr\b":   "erythrocyte sedimentation rate",
    r"\bcrp\b":   "c reactive protein",
    r"\bvitd\b":  "vitamin d",
    r"\bvitb12\b":"vitamin b12",
}

def expand_abbreviations(text: str) -> str:
    for pattern, replacement in ABBREV_MAP.items():
        text = re.sub(pattern, replacement, text)
    return text


def preprocess(text: str) -> str:
    return expand_abbreviations(normalize_text(text))


MATCH_THRESHOLD = 70.0

def match_labtests(lab_df: pd.DataFrame, master_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:

    lab    = lab_df.copy()
    master = master_df.copy()

    lab["normalized_name"]    = lab["lab_test_name"].apply(preprocess)
    master["normalized_name"] = master["master_test_name"].apply(preprocess)

    lab_embeddings = model.encode(
        lab["normalized_name"].tolist(),
        show_progress_bar=False,
        batch_size=64
    )
    master_embeddings = model.encode(
        master["normalized_name"].tolist(),
        show_progress_bar=False,
        batch_size=64
    )

    similarity_matrix  = cosine_similarity(lab_embeddings, master_embeddings)
    best_match_indices = similarity_matrix.argmax(axis=1)
    best_scores        = similarity_matrix.max(axis=1)

    lab["master_test_id"]   = master.iloc[best_match_indices]["master_test_id"].values
    lab["matched_name"]     = master.iloc[best_match_indices]["master_test_name"].values
    lab["score"]            = (best_scores * 100).round(2)

    # ── Below threshold → unmatched
    below_threshold = lab["score"] < MATCH_THRESHOLD
    lab.loc[below_threshold, "master_test_id"] = None
    lab.loc[below_threshold, "matched_name"]   = "NOT MATCHED"

    result = lab[[
        "lab_test_id",
        "lab_test_name",
        "master_test_id",
        "matched_name",
        "score"
    ]]

    total     = len(result)
    matched   = int((result["matched_name"] != "NOT MATCHED").sum())
    unmatched = total - matched

    summary = {
        "total":     total,
        "matched":   matched,
        "unmatched": unmatched,
        "threshold": MATCH_THRESHOLD
    }

    return result, summary