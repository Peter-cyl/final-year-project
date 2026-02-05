"""
XAIPFramework Integration Layer
Handles communication with the C++ XAIPFramework GUI system.

Communication modes:
1. File-based: Read from/write to XAIPFramework/common/ folder
2. Direct: Parse framework output format strings

The framework outputs abstraction specifications in a concatenated format:
    "predicate-refrigeratedttruck"
    "predicate-boardedddriverttruck"
    "duration-drive_truck"

This module parses these formats and generates natural language.
"""

import os
import re
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from pathlib import Path


@dataclass
class FrameworkOutput:
    """
    Parsed output from XAIPFramework.

    Represents a parsed abstraction specification from the framework.
    """
    abstraction_type: str           # "predicate", "duration", "til"
    predicate_name: str             # e.g., "refrigerated"
    parameters: List[Tuple[str, str]]  # [(param_letter, type), ...]
    action_context: Optional[str] = None   # Action where abstraction applies
    raw_input: str = ""             # Original input string

    def to_abstraction_string(self) -> str:
        """
        Convert to standard abstraction format for NLGGenerator.

        Returns format like: "abstract predicate (refrigerated ?t - truck) from action extend_meat_life"
        """
        if self.abstraction_type == "predicate":
            # Build parameter string
            params_str = " ".join(
                f"?{p[0]} - {p[1]}" for p in self.parameters
            )
            base = f"abstract predicate ({self.predicate_name} {params_str})"
            if self.action_context:
                return f"{base} from action {self.action_context}"
            return base
        elif self.abstraction_type == "duration":
            return f"abstract duration from action {self.predicate_name}"
        elif self.abstraction_type == "til":
            return f"abstract til {self.predicate_name}"
        return self.raw_input


@dataclass
class IntegrationConfig:
    """Configuration for XAIPFramework integration."""
    common_dir: Optional[Path] = None
    request_file: str = "nlg_request.txt"
    response_file: str = "nlg_response.txt"
    domain_file: str = "domain.pddl"
    problem_file: str = "problem.pddl"
    plan_file: str = "hplan.pddl"
    poll_interval: float = 1.0


class XAIPIntegration:
    """
    Integration layer for XAIPFramework communication.

    Handles:
    - Parsing framework output format (e.g., "predicate-refrigeratedttruck")
    - File-based communication with framework common directory
    - Watch mode for continuous integration
    """

    # Known types for parameter parsing (ordered by length, longest first)
    DEFAULT_TYPES = [
        "location", "locatable", "waypoint", "satellite", "instrument",
        "direction", "objective", "camera", "lander", "store", "mode",
        "driver", "truck", "place", "crew_member", "meal", "day",
        "meat", "cereal", "prod", "rover"
    ]

    def __init__(self, config: Optional[IntegrationConfig] = None,
                 known_types: Optional[List[str]] = None):
        """
        Initialize XAIPFramework integration.

        Args:
            config: Integration configuration
            known_types: Domain-specific types for better parsing
        """
        self.config = config or IntegrationConfig()
        self.known_types = sorted(
            known_types or self.DEFAULT_TYPES,
            key=len,
            reverse=True  # Longest first for greedy matching
        )
        self._known_predicates: List[str] = []

    def set_known_types(self, types: List[str]):
        """
        Set known types from parsed domain for better parsing.

        Args:
            types: List of type names from domain
        """
        all_types = list(set(types + self.DEFAULT_TYPES))
        self.known_types = sorted(all_types, key=len, reverse=True)

    def set_known_predicates(self, predicates: List[str]):
        """
        Set known predicate names for better parsing.

        Args:
            predicates: List of predicate names from domain
        """
        self._known_predicates = sorted(predicates, key=len, reverse=True)

    def parse_framework_input(self, technical_input: str) -> FrameworkOutput:
        """
        Parse XAIPFramework output format.

        Examples:
            "predicate-refrigeratedttruck"
            "predicate-can_deliverpprod"
            "predicate-boardedddriverttruck"
            "duration-drive_truck"
            "til-can_deliver"

        Args:
            technical_input: The framework output string

        Returns:
            Parsed FrameworkOutput object

        Raises:
            ValueError: If input format is invalid
        """
        technical_input = technical_input.strip()

        if "-" not in technical_input:
            raise ValueError(f"Invalid format (no hyphen): {technical_input}")

        # Split by first hyphen only
        parts = technical_input.split("-", 1)
        abstraction_type = parts[0].lower()
        rest = parts[1]

        # Handle different abstraction types
        if abstraction_type == "duration":
            # Duration abstractions: duration-action_name
            return FrameworkOutput(
                abstraction_type="duration",
                predicate_name=rest,
                parameters=[],
                raw_input=technical_input
            )

        if abstraction_type == "til":
            # TIL abstractions: til-predicate_name
            return FrameworkOutput(
                abstraction_type="til",
                predicate_name=rest,
                parameters=[],
                raw_input=technical_input
            )

        # Predicate abstractions: predicate-{name}{params}
        if abstraction_type != "predicate":
            # Unknown type, treat as predicate
            abstraction_type = "predicate"

        # Find predicate name by matching against known predicates
        predicate_name = None
        params_str = ""

        if self._known_predicates:
            for pred_name in self._known_predicates:
                if rest.startswith(pred_name):
                    predicate_name = pred_name
                    params_str = rest[len(pred_name):]
                    break

        if not predicate_name:
            # Heuristic: find where parameters start (first lowercase letter
            # followed by a type name)
            predicate_name, params_str = self._split_predicate_params(rest)

        # Parse parameters from concatenated string
        parameters = self._parse_param_string(params_str)

        return FrameworkOutput(
            abstraction_type=abstraction_type,
            predicate_name=predicate_name,
            parameters=parameters,
            raw_input=technical_input
        )

    def _split_predicate_params(self, rest: str) -> Tuple[str, str]:
        """
        Split combined predicate+params string when predicates are unknown.

        Uses heuristics to find the boundary between predicate name and parameters.
        """
        # Try to find where a parameter starts (single letter + type)
        for i in range(len(rest) - 1, 0, -1):
            potential_params = rest[i:]
            # Check if this could be start of params
            if len(potential_params) >= 2:
                first_char = potential_params[0]
                rest_str = potential_params[1:]
                for type_name in self.known_types:
                    if rest_str.startswith(type_name) or \
                       (rest_str.startswith(first_char) and rest_str[1:].startswith(type_name)):
                        # Found likely param start
                        return rest[:i], rest[i:]

        # No params found, entire string is predicate name
        return rest, ""

    def _parse_param_string(self, params_str: str) -> List[Tuple[str, str]]:
        """
        Parse parameter string like "ttruck" or "ddriverttruck".

        Handles concatenation artifacts where param letter duplicates
        the first letter of type name (e.g., "tt" in "ttruck" = param "t" + type "truck").

        Args:
            params_str: Concatenated parameter string

        Returns:
            List of (param_letter, type_name) tuples
        """
        parameters = []
        remaining = params_str

        while remaining:
            if len(remaining) < 2:
                break

            param_letter = remaining[0]
            rest = remaining[1:]
            matched = False

            # Check for concatenation artifact (e.g., "tt" in "ttruck")
            # This happens when param letter equals first letter of type
            if rest and rest[0] == param_letter:
                for type_name in self.known_types:
                    if type_name.startswith(param_letter) and rest.startswith(type_name):
                        # This is artifact: param "t" + "truck" shows as "ttruck"
                        parameters.append((param_letter, type_name))
                        remaining = rest[len(type_name):]
                        matched = True
                        break

            if not matched:
                # Standard matching: param letter + type name
                for type_name in self.known_types:
                    if rest.startswith(type_name):
                        parameters.append((param_letter, type_name))
                        remaining = rest[len(type_name):]
                        matched = True
                        break

            if not matched:
                # Could not match, skip this character
                remaining = rest
                if not remaining:
                    break

        return parameters

    # ==================== File-based Communication ====================

    def read_request(self) -> Optional[str]:
        """
        Read abstraction request from common folder.

        Returns:
            Request string if file exists, None otherwise
        """
        if not self.config.common_dir:
            return None

        filepath = self.config.common_dir / self.config.request_file
        if filepath.exists():
            return filepath.read_text().strip()
        return None

    def write_response(self, text: str):
        """
        Write verbalization response to common folder.

        Args:
            text: Natural language response

        Raises:
            ValueError: If common_dir not configured
        """
        if not self.config.common_dir:
            raise ValueError("common_dir not configured")

        filepath = self.config.common_dir / self.config.response_file
        filepath.write_text(text)

    def read_domain_file(self) -> Optional[str]:
        """Read domain file from common folder."""
        if not self.config.common_dir:
            return None

        filepath = self.config.common_dir / self.config.domain_file
        if filepath.exists():
            return filepath.read_text()
        return None

    def read_problem_file(self) -> Optional[str]:
        """Read problem file from common folder."""
        if not self.config.common_dir:
            return None

        filepath = self.config.common_dir / self.config.problem_file
        if filepath.exists():
            return filepath.read_text()
        return None

    def read_plan_file(self) -> Optional[str]:
        """Read generated plan from common folder."""
        if not self.config.common_dir:
            return None

        filepath = self.config.common_dir / self.config.plan_file
        if filepath.exists():
            return filepath.read_text()
        return None

    def watch_for_requests(self, callback: Callable[[str], str],
                          stop_event: Optional[Callable[[], bool]] = None):
        """
        Watch common folder for new abstraction requests.

        Continuously monitors the request file and calls the callback
        when new requests arrive.

        Args:
            callback: Function that takes request string and returns response
            stop_event: Optional callable that returns True to stop watching
        """
        if not self.config.common_dir:
            raise ValueError("common_dir not configured for watch mode")

        request_file = self.config.common_dir / self.config.request_file
        response_file = self.config.common_dir / self.config.response_file
        last_mtime = 0

        print(f"Watching for requests in: {request_file}")
        print("Press Ctrl+C to stop...")

        try:
            while True:
                if stop_event and stop_event():
                    break

                if request_file.exists():
                    mtime = request_file.stat().st_mtime
                    if mtime > last_mtime:
                        last_mtime = mtime
                        request = request_file.read_text().strip()

                        if request:
                            print(f"Received request: {request}")

                            # Process request
                            try:
                                response = callback(request)
                                print(f"Generated response ({len(response)} chars)")

                                # Write response
                                response_file.write_text(response)
                            except Exception as e:
                                error_msg = f"Error processing request: {e}"
                                print(error_msg)
                                response_file.write_text(error_msg)

                time.sleep(self.config.poll_interval)

        except KeyboardInterrupt:
            print("\nStopped watching.")

    # ==================== Utility Methods ====================

    def format_parameters_readable(self, parameters: List[Tuple[str, str]],
                                   bindings: Optional[Dict[str, str]] = None) -> str:
        """
        Format parameters as readable string.

        Args:
            parameters: List of (param_letter, type) tuples
            bindings: Optional {param: value} bindings

        Returns:
            Readable parameter string
        """
        parts = []
        for param, ptype in parameters:
            if bindings and param in bindings:
                parts.append(f"{bindings[param]} (the {ptype})")
            else:
                parts.append(f"?{param} (a {ptype})")
        return ", ".join(parts)


# Test code
if __name__ == "__main__":
    integration = XAIPIntegration()

    # Test parsing various formats
    test_inputs = [
        "predicate-refrigeratedttruck",
        "predicate-can_deliverpprod",
        "predicate-boardedddriverttruck",
        "predicate-atl1locatablel2location",
        "duration-drive_truck",
        "til-can_deliver"
    ]

    print("Testing XAIPFramework format parsing:\n")

    for input_str in test_inputs:
        try:
            result = integration.parse_framework_input(input_str)
            print(f"Input: {input_str}")
            print(f"  Type: {result.abstraction_type}")
            print(f"  Predicate: {result.predicate_name}")
            print(f"  Parameters: {result.parameters}")
            print(f"  Abstraction string: {result.to_abstraction_string()}")
            print()
        except Exception as e:
            print(f"Input: {input_str}")
            print(f"  Error: {e}")
            print()
