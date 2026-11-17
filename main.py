"""Expose Three MCP Primitives.

A workshop exposes a local equipment catalogue to MCP-compatible hosts.
Complete only equipment_catalog, check_availability, and maintenance_prompt.

The FastMCP server, immutable catalogue, response helpers, message template,
stdio launch code, and Groq-compatible host example are supplied. Pytest invokes
the server in process, so it requires no API key, subprocess, or network access.

Required behavior:
- equipment_catalog is the equipment://catalog Resource and returns the complete
  read-only catalogue as JSON using catalogue_payload().
- check_availability is a typed Tool with equipment_id: str. Return the exact
  availability_payload result for known and unknown IDs.
- maintenance_prompt is a parameterized Prompt with equipment_id: str. Return
  MAINTENANCE_TEMPLATE formatted with the requested ID.
- Calls must not mutate the supplied catalogue.

Not required: MCP transport implementation, subprocess management, an agent,
authentication, external integrations, real model calls during evaluation, or
deployment.
"""

from __future__ import annotations

import json

from fastmcp import FastMCP

from utils.catalog import MAINTENANCE_TEMPLATE, catalogue_payload, availability_payload


mcp = FastMCP("Equipment Workshop")


@mcp.resource("equipment://catalog")
def equipment_catalog() -> str:
    # TODO 1: Keep this function registered at equipment://catalog. Return
    # json.dumps(catalogue_payload(), sort_keys=True) so hosts receive the full,
    # deterministic catalogue without mutating the supplied data.
    return json.dumps(catalogue_payload(), sort_keys=True)


@mcp.tool
def check_availability(equipment_id: str) -> dict:
    # TODO 2: Keep the typed equipment_id: str parameter and return exactly
    # availability_payload(equipment_id) for both known and unknown IDs.
    return availability_payload(equipment_id)


@mcp.prompt
def maintenance_prompt(equipment_id: str) -> str:
    # TODO 3: Keep the typed equipment_id: str parameter and return
    # MAINTENANCE_TEMPLATE.format(equipment_id=equipment_id).
    return MAINTENANCE_TEMPLATE.format(equipment_id=equipment_id)


if __name__ == "__main__":
    mcp.run()
