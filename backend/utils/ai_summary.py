from __future__ import annotations

import os
from typing import Optional

import google.generativeai as genai
from fastapi import HTTPException, status


GEMINI_MODEL_NAME = "gemini-1.5-pro"


def _get_client() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gemini API key is not configured on the server.",
        )
    genai.configure(api_key=api_key)


def build_sales_prompt(table_text: str) -> str:
    """
    Construct a focused prompt for the sales dataset.
    """
    return (
        "You are a senior revenue and sales strategy analyst.\n\n"
        "Analyze the following sales dataset and produce a concise, executive-ready summary.\n\n"
        "Your report MUST include:\n"
        "- revenue insights and overall trends\n"
        "- top performing product category\n"
        "- regional performance highlights (strong and weak regions)\n"
        "- any cancellations, anomalies, or risk indicators\n"
        "- 2–4 clear business recommendations\n\n"
        "Write in a professional tone suitable for a VP of Sales.\n"
        "Use short paragraphs and bullet points where appropriate.\n\n"
        f"Sales Data Table:\n{table_text}\n\n"
        "Return only the business report, no preamble or closing remarks."
    )


def generate_sales_summary(table_text: str) -> str:
    """
    Call Google Gemini to generate an executive sales summary.
    """
    _get_client()

    prompt = build_sales_prompt(table_text)

    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to contact Gemini API: {exc}",
        ) from exc

    if not response or not getattr(response, "text", None):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini API returned an empty response.",
        )

    return response.text.strip()

