"""Permission classes.

Default is IsAuthenticated (set in REST_FRAMEWORK). Public endpoints override with AllowAny
EXPLICITLY - every such override is on the checklist in LLD §10. Forget one and the public map
breaks or reporter PII leaks.
"""

from rest_framework.permissions import BasePermission

from core.domain.value_objects import Role


class IsStaffOrAdmin(BasePermission):
    message = "Staff or admin access required."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            getattr(user, "is_authenticated", False)
            and getattr(user, "role", None) in (Role.STAFF, Role.ADMIN)
        )


class IsAdmin(BasePermission):
    message = "Admin access required."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            getattr(user, "is_authenticated", False) and getattr(user, "role", None) is Role.ADMIN
        )
