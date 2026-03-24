"""
Module 7 — Auto-Scheduling Service
Determines optimal follow-up dates based on classification risk level.
"""
from datetime import datetime, timedelta
from typing import Optional


# ─── Schedule Rules (risk-based) ────────────────────────────────────────────

SCHEDULE_RULES = {
    "malignant": {
        "interval_months": 1,
        "reason": "High-risk tumor detected. Monthly follow-up required.",
        "urgency": "urgent",
    },
    "indeterminate": {
        "interval_months": 3,
        "reason": "Indeterminate findings. Follow-up in 3 months for reassessment.",
        "urgency": "moderate",
    },
    "benign": {
        "interval_months": 12,
        "reason": "Benign tumor. Annual routine follow-up recommended.",
        "urgency": "routine",
    },
}

INVASION_SCHEDULE_OVERRIDE = {
    "Fast":   {"interval_months": 1,  "urgency": "urgent"},
    "Medium": {"interval_months": 3,  "urgency": "moderate"},
    "Slow":   {"interval_months": 6,  "urgency": "routine"},
}


def compute_schedule(
    classification_label: Optional[str] = None,
    invasion_speed: Optional[str] = None,
    base_date: Optional[datetime] = None,
) -> dict:
    """
    Compute the recommended follow-up date and reason.

    Priority: invasion_speed (if fast/medium) > classification_label.

    Args:
        classification_label: 'benign' | 'malignant' | 'indeterminate'
        invasion_speed:       'Fast' | 'Medium' | 'Slow'
        base_date:            Reference date (default: today)

    Returns:
        dict with scheduled_date, reason, urgency, interval_months
    """
    if base_date is None:
        base_date = datetime.utcnow()

    # Invasion speed can override classification urgency
    override = INVASION_SCHEDULE_OVERRIDE.get(invasion_speed or "")
    rules = SCHEDULE_RULES.get(classification_label or "indeterminate", SCHEDULE_RULES["indeterminate"])

    if override and override["urgency"] == "urgent" and rules["urgency"] != "urgent":
        interval_months = override["interval_months"]
        urgency = override["urgency"]
        reason = f"Fast invasion speed detected. {rules['reason']}"
    else:
        interval_months = rules["interval_months"]
        urgency = rules["urgency"]
        reason = rules["reason"]

    scheduled_date = base_date + timedelta(days=30 * interval_months)

    return {
        "scheduled_date": scheduled_date,
        "interval_months": interval_months,
        "reason": reason,
        "urgency": urgency,
    }


def format_schedule_message(patient_name: str, scheduled_date: datetime, reason: str) -> dict:
    """Format notification messages for SMS and push notifications."""
    date_str = scheduled_date.strftime("%d/%m/%Y")
    sms_body = (
        f"[AI Tumor Platform] Xin chào {patient_name}. "
        f"Lịch tái khám của bạn: {date_str}. "
        f"Lý do: {reason}. "
        f"Vui lòng liên hệ bệnh viện để xác nhận."
    )
    push_title = "Nhắc lịch tái khám"
    push_body = f"Tái khám ngày {date_str}: {reason}"

    return {"sms": sms_body, "push_title": push_title, "push_body": push_body}
