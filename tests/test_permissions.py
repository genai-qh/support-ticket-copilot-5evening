# tests/test_permissions.py
from app.tools import get_ticket, search_runbooks


def test_cross_tenant_get_ticket_denied():
    """Ticket 42 belongs to tenant 1. A caller from tenant 2 must be denied."""
    result = get_ticket(42, tenant_id=2)
    assert result.get("error") == "denied", f"expected denied, got {result}"


def test_valid_tenant_get_ticket_succeeds():
    """Ticket 42 belongs to tenant 1. A tenant-1 caller should succeed."""
    result = get_ticket(42, tenant_id=1)
    assert "error" not in result, f"expected success, got {result}"
    assert result["ticket_id"] == 42


def test_cross_tenant_search_returns_no_results():
    """Searching from a nonexistent tenant returns an empty corpus."""
    result = search_runbooks("cannot sign in", tenant_id=999)
    assert result["count"] == 0, f"expected 0, got {result['count']}"


def test_missing_ticket_returns_not_found():
    """A ticket ID outside the range returns a structured not-found."""
    result = get_ticket(999999, tenant_id=1)
    assert result.get("error") == "not_found", f"expected not_found, got {result}"


def test_malformed_ticket_id_returns_invalid_argument():
    """A non-integer ticket_id is rejected."""
    result = get_ticket("42", tenant_id=1)  # type: ignore
    assert result.get("error") == "invalid_argument", f"expected invalid_argument, got {result}"