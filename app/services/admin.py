"""Compatibility shim.

Use-cases moved to `app.application.admin`.

This module stays to avoid breaking older imports (`app.services.admin`).
"""

from app.application.admin import AdminService
