from __future__ import annotations

import os
import re
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils.ai_summary import generate_sales_summary
from utils.email_service import send_sales_summary
from utils.file_parser import dataframe_to_text, parse_sales_file


load_dotenv()

app = FastAPI(
    title="Sales Insight Automator API",
    description=(
        "Upload a CSV or Excel sales file and automatically generate an "
        "executive-ready sales summary using Google Gemini, then email it via Resend."
    ),
    version="0.1.0",
)

# Basic CORS configuration for SPA frontends (Vercel / localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in real production as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# Simple in-memory rate limiting
# ----------------------------

RATE_LIMIT_REQUESTS = 20
RATE_LIMIT_WINDOW_SECONDS = 60

_request_log: Dict[str, Deque[float]] = defaultdict(deque)


def rate_limiter(request: Request) -> None:
    """
    Very simple IP-based rate limiter.
    Limits each client IP to RATE_LIMIT_REQUESTS per RATE_LIMIT_WINDOW_SECONDS.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS

    events = _request_log[client_ip]

    # Drop old timestamps
    while events and events[0] < window_start:
        events.popleft()

    if len(events) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down and try again shortly.",
        )

    events.append(now)


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email: str) -> str:
    if not email or not EMAIL_REGEX.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address.",
        )
    return email


class AnalyzeResponse(BaseModel):
    email: str
    summary: str
    message: str


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze sales file and email executive summary",
    tags=["Analysis"],
)
async def analyze_sales_file(
    request: Request,
    email: str = Form(..., description="Recipient email for the summary report."),
    file: UploadFile = File(..., description="Sales data file (.csv or .xlsx)."),
    _: None = Depends(rate_limiter),
) -> AnalyzeResponse:
    """
    Core workflow:
    - validate email and file
    - parse into DataFrame
    - convert to text table
    - generate AI summary with Gemini
    - send email via Resend
    - return the summary in the API response
    """
    validate_email(email)

    df = await parse_sales_file(file)
    table_text = dataframe_to_text(df)

    summary = generate_sales_summary(table_text)
    send_sales_summary(email, summary)

    return AnalyzeResponse(
        email=email,
        summary=summary,
        message="Sales summary generated and emailed successfully.",
    )


@app.get("/health", tags=["Health"])
def health_check() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:  # pragma: no cover - centralized error formatting
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    return JSONResponse(
        {
            "message": "Sales Insight Automator backend.",
            "docs_url": "/docs",
        }
    )

