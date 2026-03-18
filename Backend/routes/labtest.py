import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from services.Labtest_match import match_labtests

router = APIRouter(prefix="/labtest", tags=["Lab Test"])


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


@router.post("/lab_match")
async def match_lab_tests(
    lab_file:    UploadFile = File(..., description="Lab tests CSV"),
    master_file: UploadFile = File(..., description="Master lab test list CSV"),
):
    lab_df    = read_csv_file(lab_file)
    master_df = read_csv_file(master_file)

    validate_columns(lab_df,    ["lab_test_id", "lab_test_name"], lab_file.filename)
    validate_columns(master_df, ["master_test_id", "master_test_name"], master_file.filename)

    result_df, summary = match_labtests(lab_df, master_df)

    buffer = io.StringIO()
    buffer.write(f"# Total: {summary['total']} | Matched: {summary['matched']} | Unmatched: {summary['unmatched']} | Threshold: {summary['threshold']}%\n")
    result_df.to_csv(buffer, index=False)
    buffer.seek(0)

    return StreamingResponse(
        content=buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=matched_lab_tests.csv"
        }
    )