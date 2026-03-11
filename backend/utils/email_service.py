from __future__ import annotations

import os
from fastapi import HTTPException, status
import resend


EMAIL_SUBJECT_DEFAULT = "Q1 Sales Insight Summary"


def _configure_client() -> None:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resend API key is not configured on the server.",
        )

    resend.api_key = api_key


def _get_from_email() -> str:
    from_email = os.getenv("RESEND_FROM_EMAIL")
    if not from_email:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RESEND_FROM_EMAIL is not configured on the server.",
        )

    return from_email


def _build_html_body(summary: str) -> str:
    formatted_summary = summary.replace("\n", "<br/>")

    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.5;">
        <h2>Q1 Sales Insight Summary</h2>
        <p>Below is your AI-generated executive summary based on the uploaded sales data.</p>
        <hr />
        <div>
          {formatted_summary}
        </div>
        <hr />
        <p style="font-size: 12px; color: #666;">
          This summary was generated automatically by the Sales Insight Automator.
        </p>
      </body>
    </html>
    """


def send_sales_summary(recipient_email: str, summary: str) -> None:
    """
    Send the AI-generated summary via Resend.
    """
    _configure_client()
    from_email = _get_from_email()

    try:
        resend.Emails.send(
            {
                "from": from_email,
                "to": [recipient_email],
                "subject": EMAIL_SUBJECT_DEFAULT,
                "html": _build_html_body(summary),
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to send email via Resend: {exc}",
        ) from exc