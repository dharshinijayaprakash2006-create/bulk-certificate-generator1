import re
from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_RECIPIENTS = 1000


class JobCreate(BaseModel):
    event_name: str = Field(min_length=1, max_length=200)
    issue_date: date
    # Loose dicts on purpose: each recipient is validated individually,
    # so one bad recipient does not reject the whole request.
    recipients: List[Dict[str, Any]] = Field(min_length=1, max_length=MAX_RECIPIENTS)


def validate_recipient(r: Dict[str, Any]) -> Optional[str]:
    """Return an error message, or None if the recipient is valid."""
    name = r.get("name")
    if not isinstance(name, str) or not name.strip():
        return "name is required and must be a non-empty string"
    if len(name.strip()) > 100:
        return "name must be at most 100 characters"
    email = r.get("email")
    if email is not None and (not isinstance(email, str) or not EMAIL_RE.match(email)):
        return "email is not a valid email address"
    return None