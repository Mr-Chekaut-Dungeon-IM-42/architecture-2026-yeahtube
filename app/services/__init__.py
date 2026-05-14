"""Compatibility shim.

The project adopted a strict 4-layer structure:

Presentation -> Application -> Domain <- Infrastructure

Use-cases now live in `app.application`.
This package remains to avoid breaking older imports.
"""
