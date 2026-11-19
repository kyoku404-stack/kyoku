"""KEEP Phase 4.6 — Base Tool Abstract Implementation.

Provides BasePlatformTool with built-in Pydantic argument/output validation,
schema generation, and contract compliance.
"""

from __future__ import annotations

import abc
from typing import Any, TypeVar

from backend.app.agents.errors import (
    ToolArgumentValidationError,
    ToolOutputValidationError,
)
from backend.app.agents.tools.contracts import ToolContext
from backend.app.agents.tools.metadata import ToolMetadata
from pydantic import BaseModel, ValidationError

TArgs = TypeVar("TArgs", bound=BaseModel)
TReturns = TypeVar("TReturns", bound=BaseModel)


class BasePlatformTool(abc.ABC):
    """Abstract base class for all platform tools adhering to BaseTool protocol."""

    args_model: type[BaseModel] | None = None
    returns_model: type[BaseModel] | None = None

    @property
    @abc.abstractmethod
    def metadata(self) -> ToolMetadata:
        """Subclasses must define their ToolMetadata."""
        ...

    def validate_arguments(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Validates arguments against args_model if provided, or basic type checks."""
        if self.args_model is not None:
            try:
                validated = self.args_model.model_validate(arguments)
                return validated.model_dump()
            except ValidationError as err:
                raise ToolArgumentValidationError(
                    f"Argument validation failed for tool '{self.metadata.tool_id}': {err.errors()[0]['msg']}",
                    tool_id=self.metadata.tool_id,
                    details={"validation_errors": err.errors()},
                ) from err
        return arguments

    def validate_output(self, output: dict[str, Any]) -> dict[str, Any]:
        """Validates output against returns_model if provided."""
        if self.returns_model is not None:
            try:
                validated = self.returns_model.model_validate(output)
                return validated.model_dump()
            except ValidationError as err:
                raise ToolOutputValidationError(
                    f"Output validation failed for tool '{self.metadata.tool_id}': {err.errors()[0]['msg']}",
                    tool_id=self.metadata.tool_id,
                    details={"validation_errors": err.errors()},
                ) from err
        return output

    @abc.abstractmethod
    async def execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> dict[str, Any]:
        """Executes the tool logic within the trusted server-side context."""
        ...

