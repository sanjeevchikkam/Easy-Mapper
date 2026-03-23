import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from services.pharmacy_match import match_medicines

router = APIRouter(prefix="/pharmacy", tags=["Pharmacy"])


def read_csv_file(upload: UploadFile) -> pd.DataFrame:
    try:
        contents = upload.file.read()
        df = pd.read_csv(io.BytesIO(contents))
        return df
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV '{upload.filename}': {str(e)}")


def validate_columns(df: pd.DataFrame, required: list, filename: str):
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"'{filename}' is missing columns: {missing}"
        )


@router.post("/pharmacy_match") 
async def match_pharmacy_medicines(
    pharmacy_file: UploadFile = File(..., description="Pharmacy inventory CSV"),
    master_file:   UploadFile = File(..., description="Master medicine list CSV"),
):
    pharmacy_df = read_csv_file(pharmacy_file)
    master_df   = read_csv_file(master_file)


    validate_columns(pharmacy_df, ["p_inv_id", "pharmacy_medicine_name"], pharmacy_file.filename)
    validate_columns(master_df,   ["master_medicine_id", "master_medicine_name"], master_file.filename)


    result_df, summary = match_medicines(pharmacy_df, master_df)


    buffer = io.StringIO()
    buffer.write(f"# Total: {summary['total']} | Matched: {summary['matched']} | Unmatched: {summary['unmatched']} | Threshold: {summary['threshold']}%\n")
    result_df.to_csv(buffer, index=False)
    buffer.seek(0)

    return StreamingResponse(
        content=buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=matched_pharmacy_inventory.csv"
        }
    )