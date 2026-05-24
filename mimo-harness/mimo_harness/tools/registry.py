"""Tool registry - unified tool definition and dispatch.

Implements Ch3 patterns:
- Tool protocol with concurrency-safe/unsafe markers (fail-closed defaults)
- Input validation before execution
- Tool result budget management (truncation)
- Execution with permission gate integration
"""

import json
from dataclasses import dataclass, field
from typing import Callable, Optional
from ..permissions import Permission, PermissionGate


# Ch3: fail-closed defaults — tools must explicitly declare safety
@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict
    handler: Callable[[dict], str]
    permission: Permission = Permission.READ
    is_read_only: bool = False       # Ch3: read-only marker
    is_destructive: bool = False     # Ch3: destructive marker
    is_concurrency_safe: bool = False  # Ch3: can run in parallel


class ToolRegistry:
    """Central tool registry with validation and dispatch.

    Follows Ch3 patterns:
    - fail-closed: unknown tools rejected
    - input validation before execution
    - result budget: truncate large outputs
    """

    # Ch3: tool result budget — prevent context overflow
    MAX_RESULT_LENGTH = 10000

    def __init__(self):
        self._tools: dict[str, ToolDef] = {}

    def register(self, tool: ToolDef):
        self._tools[tool.name] = tool

    def register_many(self, tools: list[ToolDef]):
        for t in tools:
            self.register(t)

    def get(self, name: str) -> Optional[ToolDef]:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        """Generate OpenAI-compatible tool schema for API calls."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
            }
            for t in self._tools.values()
        ]

    def list_names(self) -> list[str]:
        return list(self._tools.keys())

    def list_all(self) -> list[ToolDef]:
        return list(self._tools.values())

    def list_read_only(self) -> list[ToolDef]:
        """Ch3: get all read-only tools for plan mode filtering."""
        return [t for t in self._tools.values() if t.is_read_only]

    def list_concurrency_safe(self) -> list[ToolDef]:
        """Ch3: get tools safe for parallel execution."""
        return [t for t in self._tools.values() if t.is_concurrency_safe]

    def _validate_params(self, tool: ToolDef, params: dict) -> Optional[str]:
        """Stage 1: Validate input parameters against tool schema.

        Returns error message if invalid, None if valid.
        """
        required = tool.parameters.get("required", [])
        properties = tool.parameters.get("properties", {})

        # Check required parameters
        for req in required:
            if req not in params:
                return f"Missing required parameter: {req}"

        # Check parameter types (basic validation)
        for key, value in params.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    return f"Parameter '{key}' must be a string"
                # Check boolean BEFORE integer (isinstance(True, int) is True)
                if expected_type == "boolean" and not isinstance(value, bool):
                    return f"Parameter '{key}' must be a boolean"
                if expected_type == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
                    return f"Parameter '{key}' must be an integer"
                if expected_type == "number" and not isinstance(value, (int, float)):
                    return f"Parameter '{key}' must be a number"

        return None

    def execute(self, name: str, params: dict, perms: PermissionGate) -> str:
        """Execute a tool with full 4-stage pipeline (Ch4).

        Stages:
        1. validateInput — parameter validation
        2. checkPermissions — permission gate
        3. handler execution
        4. result budget management
        """
        # Ch3: fail-closed — unknown tools rejected
        tool = self._tools.get(name)
        if not tool:
            return json.dumps({"error": f"Unknown tool: {name}"})

        # Stage 1: Input validation
        validation_error = self._validate_params(tool, params)
        if validation_error:
            return json.dumps({"error": f"Validation failed: {validation_error}"})

        # Stage 2: Permission check
        action_desc = f"{name}({json.dumps(params, ensure_ascii=False)[:100]})"
        if not perms.check(tool.permission, action_desc):
            return json.dumps({"error": f"Permission denied for '{name}'"})

        # Stage 3: Execute handler
        try:
            result = tool.handler(params)
        except Exception as e:
            return json.dumps({"error": f"Tool '{name}' failed: {str(e)}"})

        # Stage 4: Result budget (Ch3: prevent context overflow)
        if len(result) > self.MAX_RESULT_LENGTH:
            result = (
                result[:self.MAX_RESULT_LENGTH]
                + "\n... [truncated to prevent context overflow]"
            )
        return result
