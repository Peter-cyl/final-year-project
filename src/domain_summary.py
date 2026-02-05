"""
Domain Summary Generator
Generates comprehensive overview of domain capabilities and constraints.

Required by BSPR Output Specification:
- Domain overview
- All predicates with descriptions
- All actions with purposes
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING
import json

from pddl_parser import PDDLParser, Domain, Action, Predicate

if TYPE_CHECKING:
    from domain_config import DomainProfile
    from predicate_processor import PredicateCatalog


@dataclass
class ActionSummary:
    """Summary of a single action."""
    name: str
    purpose: str
    parameters: List[str]           # ["?d: driver", "?t: truck"]
    preconditions_summary: str
    effects_summary: str
    duration_info: Optional[str] = None


@dataclass
class DomainSummary:
    """Complete domain summary."""
    domain_name: str
    description: str
    type_hierarchy: Dict[str, str]  # type -> supertype
    predicates: Dict[str, str]      # name -> description
    actions: List[ActionSummary]
    capabilities: List[str]         # What the domain can model
    constraints: List[str]          # Key constraints/requirements


class DomainSummaryGenerator:
    """
    Generates comprehensive domain summaries.

    Output format matches BSPR Output Specification requirements:
    - Domain overview
    - All predicates with descriptions
    - All actions with purposes
    """

    def __init__(self, parser: PDDLParser,
                 profile: Optional['DomainProfile'] = None):
        """
        Initialize domain summary generator.

        Args:
            parser: PDDLParser with parsed domain
            profile: Optional DomainProfile for enhanced descriptions
        """
        self.parser = parser
        self.domain = parser.domain
        self.profile = profile
        self.catalog = None

        # Auto-load profile if not provided
        if not self.profile and self.domain:
            try:
                from domain_config import DomainConfigManager
                manager = DomainConfigManager()
                self.profile = manager.get_profile(self.domain.name)
            except ImportError:
                pass

        # Create predicate catalog
        try:
            from predicate_processor import PredicateCatalog
            self.catalog = PredicateCatalog(self.domain, self.profile)
        except ImportError:
            pass

    def generate_summary(self) -> DomainSummary:
        """Generate complete domain summary."""
        return DomainSummary(
            domain_name=self.domain.name,
            description=self._generate_description(),
            type_hierarchy=self.domain.types,
            predicates=self._summarize_predicates(),
            actions=self._summarize_actions(),
            capabilities=self._identify_capabilities(),
            constraints=self._identify_constraints()
        )

    def _generate_description(self) -> str:
        """Generate domain description."""
        if self.profile:
            return self.profile.description

        # Generate from domain name
        name = self.domain.name.replace("_", " ").replace("-", " ").title()
        return f"Planning domain: {name}"

    def _summarize_predicates(self) -> Dict[str, str]:
        """Get all predicates with descriptions."""
        predicates = {}

        for pred in self.domain.predicates:
            if self.catalog:
                entry = self.catalog.get_entry(pred.name)
                if entry:
                    predicates[pred.name] = entry.natural_description
                    continue

            # Fallback
            if pred.comment:
                predicates[pred.name] = pred.comment
            else:
                predicates[pred.name] = pred.name.replace("_", " ")

        return predicates

    def _summarize_actions(self) -> List[ActionSummary]:
        """Generate summary for each action."""
        summaries = []

        for action in self.domain.actions:
            # Get action purpose
            purpose = self._get_action_purpose(action)

            # Format parameters
            params = []
            for p in action.parameters:
                params.append(f"?{p.name.lstrip('?')}: {p.type}")

            # Summarize preconditions
            precond_descs = []
            for precond in action.preconditions:
                desc = self._get_predicate_description(precond.name)
                precond_descs.append(desc)

            # Summarize effects
            effect_descs = []
            for effect in action.effects:
                negated = "NOT " if effect.comment and "not" in effect.comment.lower() else ""
                desc = self._get_predicate_description(effect.name)
                effect_descs.append(f"{negated}{desc}")

            summaries.append(ActionSummary(
                name=action.name,
                purpose=purpose,
                parameters=params,
                preconditions_summary="; ".join(precond_descs) if precond_descs else "None",
                effects_summary="; ".join(effect_descs) if effect_descs else "None",
                duration_info=action.duration
            ))

        return summaries

    def _get_action_purpose(self, action: Action) -> str:
        """Get action purpose description."""
        # Check profile first
        if self.profile and action.name in self.profile.action_descriptions:
            return self.profile.action_descriptions[action.name]

        # Use comment if available
        if action.comment:
            return action.comment

        # Generate from name
        return action.name.replace("_", " ").title()

    def _get_predicate_description(self, pred_name: str) -> str:
        """Get predicate description."""
        if self.catalog:
            entry = self.catalog.get_entry(pred_name)
            if entry:
                return entry.natural_description

        # Check profile
        if self.profile and pred_name in self.profile.predicate_descriptions:
            return self.profile.predicate_descriptions[pred_name]

        return pred_name.replace("_", " ")

    def _identify_capabilities(self) -> List[str]:
        """Identify what the domain can model."""
        capabilities = []

        # Check for temporal features
        if any(a.duration for a in self.domain.actions):
            capabilities.append("Temporal planning with durative actions")

        # Check for resource management patterns
        predicates_str = " ".join(p.name for p in self.domain.predicates).lower()

        if "full" in predicates_str or "empty" in predicates_str:
            capabilities.append("Container/capacity management")

        if "available" in predicates_str:
            capabilities.append("Resource availability tracking")

        if "at" in predicates_str or "in" in predicates_str:
            capabilities.append("Location and containment tracking")

        if "calibrat" in predicates_str:
            capabilities.append("Equipment calibration")

        if "communicat" in predicates_str:
            capabilities.append("Data communication")

        if "refrigerat" in predicates_str:
            capabilities.append("Temperature-sensitive operations")

        if "can_deliver" in predicates_str or "fresh" in predicates_str:
            capabilities.append("Time-sensitive delivery")

        # Check action patterns
        action_names = " ".join(a.name for a in self.domain.actions).lower()

        if "navigate" in action_names or "drive" in action_names or "move" in action_names:
            capabilities.append("Navigation/movement between locations")

        if "load" in action_names or "unload" in action_names:
            capabilities.append("Loading/unloading operations")

        if "sample" in action_names or "analyze" in action_names:
            capabilities.append("Sample collection and analysis")

        if "image" in action_names or "photograph" in action_names:
            capabilities.append("Image capture")

        return list(set(capabilities))  # Remove duplicates

    def _identify_constraints(self) -> List[str]:
        """Identify key domain constraints."""
        constraints = []

        # Check for timing constraints (TILs mentioned in comments or duration)
        if any(a.duration for a in self.domain.actions):
            constraints.append("Actions have time durations")

        # Check predicates that suggest constraints
        for pred in self.domain.predicates:
            name = pred.name.lower()
            if "can_" in name:
                constraints.append(f"Capability requirement: {pred.name}")
            elif "available" in name:
                constraints.append(f"Availability constraint: {pred.name}")

        return constraints[:5]  # Limit to top 5

    def to_natural_language(self) -> str:
        """Generate human-readable domain summary."""
        summary = self.generate_summary()

        lines = [
            f"# Domain Summary: {summary.domain_name}",
            "",
            "## Description",
            summary.description,
            "",
            "## Type Hierarchy"
        ]

        if summary.type_hierarchy:
            for subtype, supertype in summary.type_hierarchy.items():
                lines.append(f"  - {subtype} (subtype of {supertype})")
        else:
            lines.append("  - No explicit type hierarchy defined")

        lines.extend(["", "## Predicates (State Variables)"])

        for name, desc in summary.predicates.items():
            lines.append(f"  - **{name}**: {desc}")

        lines.extend(["", "## Actions"])

        for action in summary.actions:
            lines.append(f"\n### {action.name}")
            lines.append(f"**Purpose**: {action.purpose}")
            lines.append(f"**Parameters**: {', '.join(action.parameters)}")
            lines.append(f"**Requires**: {action.preconditions_summary}")
            lines.append(f"**Effects**: {action.effects_summary}")
            if action.duration_info:
                lines.append(f"**Duration**: {action.duration_info}")

        if summary.capabilities:
            lines.extend(["", "## Domain Capabilities"])
            for cap in summary.capabilities:
                lines.append(f"  - {cap}")

        if summary.constraints:
            lines.extend(["", "## Key Constraints"])
            for con in summary.constraints:
                lines.append(f"  - {con}")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Export summary as JSON."""
        summary = self.generate_summary()

        data = {
            "domain_name": summary.domain_name,
            "description": summary.description,
            "type_hierarchy": summary.type_hierarchy,
            "predicates": summary.predicates,
            "actions": [
                {
                    "name": a.name,
                    "purpose": a.purpose,
                    "parameters": a.parameters,
                    "preconditions": a.preconditions_summary,
                    "effects": a.effects_summary,
                    "duration": a.duration_info
                }
                for a in summary.actions
            ],
            "capabilities": summary.capabilities,
            "constraints": summary.constraints
        }

        return json.dumps(data, indent=2)


# Test code
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')

    # Parse domain
    parser = PDDLParser()
    domain = parser.parse_file("domains/refrigerated_delivery_domain.pddl")

    # Generate summary
    generator = DomainSummaryGenerator(parser)
    print(generator.to_natural_language())
