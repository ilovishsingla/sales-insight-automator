from __future__ import annotations

import io
from typing import Literal

import pandas as pd
from fastapi import HTTPException, UploadFile, status

ALLOWED_EXTENSIONS: tuple[str, ...] = (".csv", ".xlsx")
MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB


def _get_extension(filename: str) -> str:
    filename_lower = filename.lower()
    for ext in ALLOWED_EXTENSIONS:
        if filename_lower.endswith(ext):
            return ext
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported file type. Only .csv and .xlsx are allowed.",
    )


async def parse_sales_file(upload_file: UploadFile) -> pd.DataFrame:
    """
    Validate and parse the uploaded sales file into a pandas DataFrame.
    Enforces file type and size constraints.
    """
    if not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename.",
        )

    ext = _get_extension(upload_file.filename)

    # Read file bytes and enforce max size
    raw_bytes = await upload_file.read()
    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 5MB.",
        )

    try:
        if ext == ".csv":
            buffer = io.StringIO(raw_bytes.decode("utf-8", errors="ignore"))
            df = pd.read_csv(buffer)
        else:  # .xlsx
            buffer = io.BytesIO(raw_bytes)
            df = pd.read_excel(buffer)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to parse file: {exc}",
        ) from exc

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parsed dataset is empty.",
        )

    return df


def dataframe_to_text(df: pd.DataFrame, max_rows: int = 50) -> str:
    """
    Convert a pandas DataFrame into a readable text table for LLM consumption.
    Limits the number of rows to keep prompts compact while preserving fidelity.
    """
    if df.empty:
        return "No data rows."

    trimmed_df = df.head(max_rows)
    # Use Markdown-style table; widely understood by LLMs.
    table_text = trimmed_df.to_markdown(index=False)
    if len(df) > max_rows:
        table_text += f"\n\n(Note: showing first {max_rows} of {len(df)} rows.)"
    return table_text

