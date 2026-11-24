"""Helpers for validating API responses against the live OpenAPI contract."""

from __future__ import annotations

from typing import Any

import requests
from automation.api.clients.shop_api import ShopApiClient
from jsonschema import Draft202012Validator, FormatChecker


def _expand_local_refs(schema: Any, document: dict[str, Any], seen: tuple[str, ...] = ()) -> Any:
    """Inline local OpenAPI schema references to keep validation self-contained."""
    if isinstance(schema, list):
        return [_expand_local_refs(item, document, seen) for item in schema]
    if not isinstance(schema, dict):
        return schema

    reference = schema.get("$ref")
    if reference:
        if not reference.startswith("#/") or reference in seen:
            raise ValueError(f"Unsupported or circular OpenAPI schema reference: {reference}")
        target: Any = document
        for segment in reference[2:].split("/"):
            target = target[segment.replace("~1", "/").replace("~0", "~")]
        expanded = _expand_local_refs(target, document, (*seen, reference))
        siblings = {key: value for key, value in schema.items() if key != "$ref"}
        if siblings:
            return {"allOf": [expanded, _expand_local_refs(siblings, document, seen)]}
        return expanded
    return {key: _expand_local_refs(value, document, seen) for key, value in schema.items()}


def validate_openapi_response(
    client: ShopApiClient,
    response: requests.Response,
    *,
    path: str,
    method: str,
) -> None:
    """Validate JSON response data using the matching schema from /openapi.json."""
    openapi_response = client.get("/openapi.json")
    openapi_response.raise_for_status()
    specification: dict[str, Any] = openapi_response.json()

    response_spec = specification["paths"][path][method.lower()]["responses"][
        str(response.status_code)
    ]
    schema = _expand_local_refs(
        response_spec["content"]["application/json"]["schema"], specification
    )
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    validator.validate(response.json())
