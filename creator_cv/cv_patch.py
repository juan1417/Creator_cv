"""Fusión segura de parches JSON sobre el contexto del CV (entrevista / chat)."""

from __future__ import annotations

import copy
from typing import Any

from creator_cv.context_sync import EXPECTED_TOP_KEYS, validate_context_shape

# Raíces que el chat puede proponer (incl. campos extra del template real).
ALLOWED_PATCH_ROOTS = set(EXPECTED_TOP_KEYS) | {"certificaciones", "fortalezas"}


def _deep_merge_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge_dict(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def apply_cv_context_patch(
    base: dict[str, Any],
    patch: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(patch, dict):
        raise ValueError("El parche debe ser un objeto JSON.")
    out = copy.deepcopy(base)
    for k, v in patch.items():
        if k not in ALLOWED_PATCH_ROOTS:
            continue
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge_dict(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    validate_context_shape(out)
    return out
