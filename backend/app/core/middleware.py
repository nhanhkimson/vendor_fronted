MUTATING = {"POST", "PUT", "PATCH", "DELETE"}

# Filled when strict_audit is on: successful mutating requests that wrote no audit row.
AUDIT_VIOLATIONS: list[str] = []
