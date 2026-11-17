"""Unit and integration tests for Expose Three MCP Primitives workshop server."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock

import pytest

from main import check_availability, equipment_catalog, maintenance_prompt, mcp
from utils.catalog import CATALOGUE, MAINTENANCE_TEMPLATE, availability_payload, catalogue_payload
from utils.host_agent import GroqEquipmentHost


# ===========================================================================
# Unit Tests: TODO 1 - equipment_catalog (Resource)
# ===========================================================================

class TestEquipmentCatalogResource:
    """Tests for equipment_catalog resource implementation and discovery."""

    def test_direct_call_returns_string(self):
        result = equipment_catalog()
        assert isinstance(result, str)

    def test_direct_call_parses_as_valid_json(self):
        result = equipment_catalog()
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 3

    def test_direct_call_matches_catalogue_payload(self):
        result = equipment_catalog()
        parsed = json.loads(result)
        expected = catalogue_payload()
        assert parsed == expected

    def test_direct_call_sort_keys_deterministic(self):
        result = equipment_catalog()
        expected = json.dumps(catalogue_payload(), sort_keys=True)
        assert result == expected

        # Verify key ordering in serialized items
        for item in json.loads(result):
            keys = list(item.keys())
            assert keys == sorted(keys)

    def test_catalogue_contains_expected_equipment(self):
        result = equipment_catalog()
        parsed = json.loads(result)
        items_by_id = {item["equipment_id"]: item for item in parsed}

        assert "drill-01" in items_by_id
        assert items_by_id["drill-01"]["name"] == "Cordless Drill"
        assert items_by_id["drill-01"]["available"] is True

        assert "meter-02" in items_by_id
        assert items_by_id["meter-02"]["name"] == "Digital Multimeter"
        assert items_by_id["meter-02"]["available"] is False

        assert "camera-03" in items_by_id
        assert items_by_id["camera-03"]["name"] == "Thermal Camera"
        assert items_by_id["camera-03"]["available"] is True

    def test_catalogue_immutability_on_repeated_calls(self):
        first_call = equipment_catalog()
        second_call = equipment_catalog()
        assert first_call == second_call

        # Mutate parsed structure locally
        mutated = json.loads(first_call)
        mutated.clear()
        assert len(mutated) == 0

        # Verify subsequent call is unaffected
        third_call = equipment_catalog()
        assert third_call == first_call

    def test_fastmcp_resource_discovery(self):
        resources = asyncio.run(mcp.list_resources())
        resource_map = {str(res.uri): res for res in resources}
        assert "equipment://catalog" in resource_map
        catalog_resource = resource_map["equipment://catalog"]
        assert catalog_resource.name == "equipment_catalog"

    def test_fastmcp_read_resource(self):
        resource_content = asyncio.run(mcp.read_resource("equipment://catalog"))
        assert len(resource_content.contents) == 1
        content_text = resource_content.contents[0].content
        expected = json.dumps(catalogue_payload(), sort_keys=True)
        assert content_text == expected


# ===========================================================================
# Unit Tests: TODO 2 - check_availability (Tool)
# ===========================================================================

class TestCheckAvailabilityTool:
    """Tests for check_availability tool implementation and discovery."""

    def test_known_available_equipment(self):
        result = check_availability("drill-01")
        assert result == {
            "found": True,
            "equipment_id": "drill-01",
            "available": True,
        }

    def test_known_unavailable_equipment(self):
        result = check_availability("meter-02")
        assert result == {
            "found": True,
            "equipment_id": "meter-02",
            "available": False,
        }

    def test_known_thermal_camera(self):
        result = check_availability("camera-03")
        assert result == {
            "found": True,
            "equipment_id": "camera-03",
            "available": True,
        }

    def test_unknown_equipment_id(self):
        result = check_availability("lathe-99")
        assert result == {
            "found": False,
            "equipment_id": "lathe-99",
            "error": "equipment_not_found",
        }

    def test_empty_string_equipment_id(self):
        result = check_availability("")
        assert result == {
            "found": False,
            "equipment_id": "",
            "error": "equipment_not_found",
        }

    def test_nonexistent_formatted_id(self):
        result = check_availability("drill-02")
        assert result == {
            "found": False,
            "equipment_id": "drill-02",
            "error": "equipment_not_found",
        }

    def test_matches_helper_directly(self):
        for item in CATALOGUE:
            assert check_availability(item.equipment_id) == availability_payload(item.equipment_id)
        assert check_availability("nonexistent") == availability_payload("nonexistent")

    def test_fastmcp_tool_discovery(self):
        tools = asyncio.run(mcp.list_tools())
        tool_names = [t.name for t in tools]
        assert "check_availability" in tool_names

    def test_fastmcp_tool_parameters_schema(self):
        tool = asyncio.run(mcp.get_tool("check_availability"))
        assert tool.name == "check_availability"
        schema = tool.parameters
        assert "properties" in schema
        assert "equipment_id" in schema["properties"]
        assert schema["properties"]["equipment_id"]["type"] == "string"
        assert "equipment_id" in schema.get("required", [])

    def test_fastmcp_call_tool_known(self):
        result = asyncio.run(mcp.call_tool("check_availability", {"equipment_id": "drill-01"}))
        assert not result.is_error
        assert result.structured_content == {
            "found": True,
            "equipment_id": "drill-01",
            "available": True,
        }

    def test_fastmcp_call_tool_unknown(self):
        result = asyncio.run(mcp.call_tool("check_availability", {"equipment_id": "ghost-00"}))
        assert not result.is_error
        assert result.structured_content == {
            "found": False,
            "equipment_id": "ghost-00",
            "error": "equipment_not_found",
        }


# ===========================================================================
# Unit Tests: TODO 3 - maintenance_prompt (Prompt)
# ===========================================================================

class TestMaintenancePrompt:
    """Tests for maintenance_prompt prompt implementation and discovery."""

    def test_renders_template_with_equipment_id(self):
        result = maintenance_prompt("drill-01")
        expected = MAINTENANCE_TEMPLATE.format(equipment_id="drill-01")
        assert result == expected
        assert "drill-01" in result
        assert "Create a maintenance request for equipment drill-01." in result

    def test_renders_template_with_unknown_id(self):
        result = maintenance_prompt("crane-55")
        expected = MAINTENANCE_TEMPLATE.format(equipment_id="crane-55")
        assert result == expected
        assert "crane-55" in result

    def test_renders_template_with_special_characters(self):
        result = maintenance_prompt("rig#42/unit-B")
        expected = MAINTENANCE_TEMPLATE.format(equipment_id="rig#42/unit-B")
        assert result == expected
        assert "rig#42/unit-B" in result

    def test_fastmcp_prompt_discovery(self):
        prompts = asyncio.run(mcp.list_prompts())
        prompt_names = [p.name for p in prompts]
        assert "maintenance_prompt" in prompt_names

    def test_fastmcp_prompt_arguments_schema(self):
        prompt = asyncio.run(mcp.get_prompt("maintenance_prompt"))
        assert prompt.name == "maintenance_prompt"
        arg_names = [arg.name for arg in prompt.arguments]
        assert "equipment_id" in arg_names
        equipment_arg = next(arg for arg in prompt.arguments if arg.name == "equipment_id")
        assert equipment_arg.required is True

    def test_fastmcp_render_prompt(self):
        rendered = asyncio.run(mcp.render_prompt("maintenance_prompt", {"equipment_id": "meter-02"}))
        assert len(rendered.messages) == 1
        msg = rendered.messages[0]
        expected_text = MAINTENANCE_TEMPLATE.format(equipment_id="meter-02")
        assert msg.content.text == expected_text


# ===========================================================================
# Unit Tests: GroqHost Integration Shell & Edge Cases
# ===========================================================================

class TestGroqEquipmentHostAndExtras:
    """Tests for host agent initialization and edge cases."""

    def test_groq_host_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(ValueError, match="GROQ_API_KEY is required"):
            GroqEquipmentHost(api_key=None)

    def test_groq_host_answer_formatting(self, monkeypatch):
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "The equipment drill-01 is available."
        mock_client.chat.completions.create.return_value.choices = [mock_choice]

        host = GroqEquipmentHost(api_key="gsk-test-fake-key")
        host.client = mock_client

        ans = host.answer("Can I borrow drill-01?", "{'found': True, 'available': True}")
        assert ans == "The equipment drill-01 is available."
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["messages"][0] == {"role": "user", "content": "Can I borrow drill-01?"}
        assert call_kwargs["messages"][1] == {
            "role": "system",
            "content": "Local MCP result: {'found': True, 'available': True}",
        }

    def test_global_catalogue_is_frozen(self):
        # Verify the underlying tuples and dataclasses cannot be mutated directly
        with pytest.raises(AttributeError):
            CATALOGUE[0].available = False  # type: ignore[misc]

    def test_server_metadata(self):
        assert mcp.name == "Equipment Workshop"

    def test_multiple_sequential_resource_and_tool_calls(self):
        # Verify repeated execution across all three primitives maintains stability
        for _ in range(5):
            cat_json = equipment_catalog()
            assert "drill-01" in cat_json
            drill_status = check_availability("drill-01")
            assert drill_status["found"] is True
            prompt = maintenance_prompt("drill-01")
            assert "equipment drill-01" in prompt
