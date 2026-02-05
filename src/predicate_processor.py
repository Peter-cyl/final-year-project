"""
Predicate Processor Module
Generates structured predicate catalog and handles predicate-to-description mapping.

This module centralizes predicate handling as specified in the BSPR Component Specification,
providing a consistent interface for predicate verbalization across the system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from pddl_parser import PDDLParser, Domain, Predicate, Action


# Import conditionally to avoid circular imports
try:
    from domain_config import DomainProfile
except ImportError:
    DomainProfile = None


@dataclass
class PredicateEntry:
    """
    Structured entry for a predicate in the catalog.

    Contains all information needed for verbalization:
    - Name and parameters
    - Natural language description
    - Usage context (where it appears in actions)
    """
    name: str
    parameters: List[str]           # Parameter names like ["?t", "?l"]
    parameter_types: List[str]      # Corresponding types like ["truck", "location"]
    raw_comment: Optional[str]      # Original PDDL comment
    natural_description: str        # Generated natural language description
    usage_contexts: List[str] = field(default_factory=list)  # ["precondition:drive", "effect:load"]


@dataclass
class ActionPredicateUsage:
    """Tracks how predicates are used within an action."""
    action_name: str
    preconditions: List[str]  # Predicate names used in preconditions
    effects_positive: List[str]  # Predicates added by effects
    effects_negative: List[str]  # Predicates removed by effects


class PredicateCatalog:
    """
    Structured catalog of all predicates in a domain with their descriptions.

    Provides:
    - Automatic description generation from PDDL comments
    - Domain profile integration for custom descriptions
    - Usage context tracking (which actions use which predicates)
    - Parameter binding and substitution
    """

    def __init__(self, domain: Domain, profile: Optional['DomainProfile'] = None):
        """
        Initialize predicate catalog from a domain.

        Args:
            domain: Parsed PDDL domain
            profile: Optional domain profile for custom descriptions
        """
        self.domain = domain
        self.profile = profile
        self.entries: Dict[str, PredicateEntry] = {}
        self.action_usage: Dict[str, ActionPredicateUsage] = {}

        self._build_catalog()
        self._analyze_usage()

    def _build_catalog(self):
        """Build the predicate catalog from domain predicates."""
        for pred in self.domain.predicates:
            # Infer parameter types from domain type definitions
            param_types = self._infer_parameter_types(pred)

            # Generate natural description
            natural_desc = self._generate_description(pred, param_types)

            self.entries[pred.name] = PredicateEntry(
                name=pred.name,
                parameters=pred.parameters,
                parameter_types=param_types,
                raw_comment=pred.comment,
                natural_description=natural_desc,
                usage_contexts=[]
            )

    def _infer_parameter_types(self, pred: Predicate) -> List[str]:
        """
        Infer parameter types from domain type definitions.

        Uses heuristics based on parameter names and domain types.
        """
        types = []
        domain_types = set(self.domain.types.keys())

        for param in pred.parameters:
            # Remove ? prefix
            param_name = param.lstrip('?')
            inferred_type = "object"

            # Check if parameter name matches or contains a type name
            for dtype in domain_types:
                if dtype in param_name or param_name in dtype:
                    inferred_type = dtype
                    break

            # Common naming conventions
            if param_name.startswith('t') and 'truck' in domain_types:
                inferred_type = 'truck'
            elif param_name.startswith('l') and 'location' in domain_types:
                inferred_type = 'location'
            elif param_name.startswith('d') and 'driver' in domain_types:
                inferred_type = 'driver'
            elif param_name.startswith('p') and 'prod' in domain_types:
                inferred_type = 'prod'
            elif param_name.startswith('r') and 'rover' in domain_types:
                inferred_type = 'rover'
            elif param_name.startswith('w') and 'waypoint' in domain_types:
                inferred_type = 'waypoint'

            types.append(inferred_type)

        return types

    def _generate_description(self, pred: Predicate, param_types: List[str]) -> str:
        """
        Generate natural language description for a predicate.

        Priority:
        1. Profile override (if provided)
        2. PDDL comment (if present)
        3. Auto-generated from name
        """
        # Priority 1: Profile override
        if self.profile and pred.name in self.profile.predicate_descriptions:
            return self.profile.predicate_descriptions[pred.name]

        # Priority 2: PDDL comment
        if pred.comment:
            return pred.comment

        # Priority 3: Generate from name
        return self._default_description(pred.name, pred.parameters, param_types)

    def _default_description(self, name: str, params: List[str],
                            types: List[str]) -> str:
        """Generate default description from predicate name and params."""
        readable_name = name.replace("_", " ").replace("-", " ")

        if not params:
            return readable_name

        # Build description based on common patterns
        param_refs = [f"{{{i}}}" for i in range(len(params))]

        if name in ("at", "in"):
            return f"{param_refs[0]} is {readable_name} {param_refs[1]}"
        elif name.startswith("can_") or name.startswith("can-"):
            action = readable_name.replace("can ", "")
            return f"{param_refs[0]} can {action}"
        elif name.startswith("is_") or name.startswith("is-"):
            state = readable_name.replace("is ", "")
            return f"{param_refs[0]} is {state}"
        elif name.startswith("has_") or name.startswith("has-"):
            thing = readable_name.replace("has ", "")
            if len(params) > 1:
                return f"{param_refs[0]} has {thing} {param_refs[1]}"
            return f"{param_refs[0]} has {thing}"
        elif name.endswith("ed"):
            # Past participle: "boarded", "refrigerated", "calibrated"
            if len(params) == 1:
                return f"{param_refs[0]} is {readable_name}"
            elif len(params) == 2:
                return f"{param_refs[0]} is {readable_name} on {param_refs[1]}"
            return f"{param_refs[0]} is {readable_name}"
        elif name.startswith("connected"):
            if len(params) >= 2:
                return f"{param_refs[0]} is {readable_name} to {param_refs[1]}"
        elif name.startswith("have_") or name.startswith("have-"):
            thing = readable_name.replace("have ", "")
            return f"{param_refs[0]} has {thing}"

        # Default: "[pred] holds for [params]"
        if len(params) == 1:
            return f"{param_refs[0]} is {readable_name}"
        elif len(params) == 2:
            return f"{readable_name} holds for {param_refs[0]} and {param_refs[1]}"
        else:
            return f"{readable_name} holds for {', '.join(param_refs)}"

    def _analyze_usage(self):
        """Analyze how predicates are used in actions."""
        for action in self.domain.actions:
            precond_preds = [p.name for p in action.preconditions]
            effect_pos = []
            effect_neg = []

            for eff in action.effects:
                if eff.comment and "not" in eff.comment.lower():
                    effect_neg.append(eff.name)
                else:
                    effect_pos.append(eff.name)

            self.action_usage[action.name] = ActionPredicateUsage(
                action_name=action.name,
                preconditions=precond_preds,
                effects_positive=effect_pos,
                effects_negative=effect_neg
            )

            # Update predicate entries with usage context
            for pred_name in precond_preds:
                if pred_name in self.entries:
                    self.entries[pred_name].usage_contexts.append(
                        f"precondition:{action.name}"
                    )

            for pred_name in effect_pos + effect_neg:
                if pred_name in self.entries:
                    self.entries[pred_name].usage_contexts.append(
                        f"effect:{action.name}"
                    )

    def get_entry(self, pred_name: str) -> Optional[PredicateEntry]:
        """Get catalog entry for a predicate."""
        return self.entries.get(pred_name)

    def get_description(self, pred_name: str,
                       bindings: Optional[Dict[str, str]] = None) -> str:
        """
        Get natural language description with optional parameter substitution.

        Args:
            pred_name: Name of the predicate
            bindings: Optional {param: value} or {index: value} bindings

        Returns:
            Natural language description with substituted values
        """
        entry = self.entries.get(pred_name)
        if not entry:
            return pred_name.replace("_", " ")

        desc = entry.natural_description

        if bindings:
            # Handle both param name and index-based bindings
            for key, value in bindings.items():
                # Get readable value from profile if available
                readable = value
                if self.profile:
                    readable = self.profile.get_readable_value(value)

                # Try param name substitution (e.g., ?t -> T1)
                if isinstance(key, str) and key.startswith('?'):
                    desc = desc.replace(key, readable)

                # Try index-based substitution (e.g., {0} -> T1)
                if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
                    desc = desc.replace(f"{{{key}}}", readable)

        # Clean up any remaining placeholders
        import re
        desc = re.sub(r'\{(\d+)\}', lambda m: entry.parameters[int(m.group(1))]
                      if int(m.group(1)) < len(entry.parameters)
                      else m.group(0), desc)

        return desc

    def get_description_for_ground(self, pred_name: str,
                                   arguments: List[str]) -> str:
        """
        Get description for a ground predicate with specific arguments.

        Args:
            pred_name: Predicate name
            arguments: Ground argument values

        Returns:
            Natural language description
        """
        bindings = {str(i): arg for i, arg in enumerate(arguments)}
        return self.get_description(pred_name, bindings)

    def get_predicates_for_action(self, action_name: str,
                                  role: str = "all") -> List[str]:
        """
        Get predicates used by an action.

        Args:
            action_name: Name of the action
            role: "precondition", "effect", or "all"

        Returns:
            List of predicate names
        """
        usage = self.action_usage.get(action_name)
        if not usage:
            return []

        if role == "precondition":
            return usage.preconditions
        elif role == "effect":
            return usage.effects_positive + usage.effects_negative
        else:
            return list(set(
                usage.preconditions +
                usage.effects_positive +
                usage.effects_negative
            ))

    def get_actions_using_predicate(self, pred_name: str,
                                   role: str = "all") -> List[str]:
        """
        Get actions that use a predicate.

        Args:
            pred_name: Name of the predicate
            role: "precondition", "effect", or "all"

        Returns:
            List of action names
        """
        actions = []
        for action_name, usage in self.action_usage.items():
            if role == "precondition" and pred_name in usage.preconditions:
                actions.append(action_name)
            elif role == "effect" and pred_name in (usage.effects_positive + usage.effects_negative):
                actions.append(action_name)
            elif role == "all" and pred_name in (usage.preconditions + usage.effects_positive + usage.effects_negative):
                actions.append(action_name)
        return actions

    def to_summary_dict(self) -> Dict:
        """Export catalog as dictionary for domain summary."""
        return {
            name: {
                "description": entry.natural_description,
                "parameters": list(zip(entry.parameters, entry.parameter_types)),
                "used_in": list(set(entry.usage_contexts)),
                "comment": entry.raw_comment
            }
            for name, entry in self.entries.items()
        }

    def list_predicates(self) -> List[str]:
        """Get list of all predicate names."""
        return list(self.entries.keys())


class PredicateProcessor:
    """
    High-level predicate processor for the NLG system.

    Provides a simplified interface for common predicate operations.
    """

    def __init__(self, parser: PDDLParser, profile: Optional['DomainProfile'] = None):
        """
        Initialize predicate processor.

        Args:
            parser: PDDL parser with parsed domain
            profile: Optional domain profile
        """
        self.parser = parser
        self.domain = parser.domain
        self.profile = profile
        self.catalog = PredicateCatalog(self.domain, profile)

    def verbalize_predicate(self, pred_name: str,
                           arguments: Optional[List[str]] = None) -> str:
        """
        Generate natural language for a predicate.

        Args:
            pred_name: Predicate name
            arguments: Optional ground arguments

        Returns:
            Natural language description
        """
        if arguments:
            return self.catalog.get_description_for_ground(pred_name, arguments)
        return self.catalog.get_description(pred_name)

    def get_predicate_names(self) -> List[str]:
        """Get all predicate names in the domain."""
        return self.catalog.list_predicates()

    def get_predicate_info(self, pred_name: str) -> Optional[PredicateEntry]:
        """Get detailed information about a predicate."""
        return self.catalog.get_entry(pred_name)

    def find_actions_affected_by(self, pred_name: str) -> Dict[str, List[str]]:
        """
        Find actions affected by a predicate abstraction.

        Returns dict with:
        - 'requires': Actions that require this predicate (precondition)
        - 'establishes': Actions that make this predicate true (effect)
        - 'removes': Actions that make this predicate false (effect)
        """
        result = {
            'requires': [],
            'establishes': [],
            'removes': []
        }

        for action_name, usage in self.catalog.action_usage.items():
            if pred_name in usage.preconditions:
                result['requires'].append(action_name)
            if pred_name in usage.effects_positive:
                result['establishes'].append(action_name)
            if pred_name in usage.effects_negative:
                result['removes'].append(action_name)

        return result


# Test code
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')

    # Test with refrigeration domain
    parser = PDDLParser()
    domain = parser.parse_file("domains/refrigerated_delivery_domain.pddl")

    # Create catalog without profile
    catalog = PredicateCatalog(domain)

    print("Predicate Catalog:")
    print("-" * 50)

    for name, entry in catalog.entries.items():
        print(f"\n{name}:")
        print(f"  Parameters: {entry.parameters}")
        print(f"  Types: {entry.parameter_types}")
        print(f"  Description: {entry.natural_description}")
        print(f"  Used in: {entry.usage_contexts[:3]}...")

    print("\n" + "=" * 50)
    print("Testing description with bindings:")

    desc = catalog.get_description_for_ground("at", ["t1", "a"])
    print(f"at(t1, a) -> {desc}")

    # Test with profile
    from domain_config import DomainConfigManager
    manager = DomainConfigManager()
    profile = manager.get_profile("refrigerated_delivery")

    if profile:
        catalog_with_profile = PredicateCatalog(domain, profile)
        desc = catalog_with_profile.get_description_for_ground("refrigerated", ["t1"])
        print(f"refrigerated(t1) with profile -> {desc}")
