"""Security module exports."""

from .constitution import Constitution, ConstitutionViolation, ViolationSeverity, constitution

try:
    from .auth import JWTAuth, RoleChecker, get_current_user, jwt_auth, require_admin, require_user
except ModuleNotFoundError as exc:
    if exc.name != "jwt":
        raise

    JWTAuth = None  # type: ignore[assignment]
    RoleChecker = None  # type: ignore[assignment]
    jwt_auth = None  # type: ignore[assignment]

    def _jwt_dependency_missing(*args, **kwargs):
        raise RuntimeError("PyJWT is required for auth helpers. Install 'pyjwt' to enable them.")

    get_current_user = _jwt_dependency_missing  # type: ignore[assignment]
    require_admin = _jwt_dependency_missing  # type: ignore[assignment]
    require_user = _jwt_dependency_missing  # type: ignore[assignment]

__all__ = [
    "JWTAuth",
    "RoleChecker",
    "get_current_user",
    "jwt_auth",
    "require_admin",
    "require_user",
    "Constitution",
    "ConstitutionViolation",
    "ViolationSeverity",
    "constitution",
]
