"""Health check.

Public, unauthenticated, unthrottled — for load balancers, uptime monitors, and free-tier
hosts that sleep idle services (the legacy app had a keep-alive for exactly this). Reports a
liveness ping and a cheap database round-trip.
"""

from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request):
        db_ok = True
        try:
            with connection.cursor() as c:
                c.execute("SELECT 1")
                c.fetchone()
        except Exception:
            db_ok = False
        status_code = 200 if db_ok else 503
        return Response({"status": "ok" if db_ok else "degraded", "database": db_ok},
                        status=status_code)
