"""
Natural Language Generator Module
Generates human-readable explanations from planning abstractions.

Takes:
- Abstraction specification (what was removed/changed)
- Parsed PDDL domain with comments
- Parameter bindings (optional)
- Domain profile (optional) for multi-domain support

Produces:
- Natural language explanation

Enhanced to support:
- Multi-domain configuration via DomainProfile
- Goal and initial state verbalization
- Effects verbalization
- Integration with PredicateCatalog
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING
from pddl_parser import (
    PDDLParser, Action, Predicate, Parameter,
    Problem, GroundPredicate, InitialState, GoalCondition
)

# Conditional imports to avoid circular dependencies
if TYPE_CHECKING:
    from domain_config import DomainProfile
    from predicate_processor import PredicateCatalog


@dataclass
class Abstraction:
    """Represents an abstraction (what was removed to make the plan work)"""
    abstraction_type: str       # "predicate", "duration", "til"
    predicate_name: str         # e.g., "refrigerated"
    action_name: str            # e.g., "extend_meat_life"
    parameters: Dict[str, str]  # e.g., {"?t": "truck", "?m": "meat"}


@dataclass
class PlanStep:
    """Represents a single step in a plan"""
    time: float
    action_name: str
    parameters: List[str]       # Ground parameters like ["t1", "a", "b"]
    duration: float


class NLGGenerator:
    """
    Generates natural language explanations for planning abstractions.

    Uses templates and comments from annotated PDDL domains to create
    human-readable explanations.

    Now supports multi-domain configuration via DomainProfile.
    """

    def __init__(self, parser: PDDLParser, profile: Optional['DomainProfile'] = None):
        """
        Initialize NLG generator.

        Args:
            parser: PDDLParser with parsed domain
            profile: Optional DomainProfile for domain-specific configuration.
                     If not provided, attempts to auto-load from DomainConfigManager.
        """
        self.parser = parser
        self.domain = parser.domain
        self.profile = profile
        self.catalog = None  # Lazy-loaded PredicateCatalog

        # Try to auto-load profile if not provided
        if not self.profile and self.domain:
            try:
                from domain_config import DomainConfigManager
                manager = DomainConfigManager()
                self.profile = manager.get_profile(self.domain.name)
            except ImportError:
                pass

        # Templates for different abstraction types
        self.templates = {
            "predicate": "If we did not require that {precondition_desc} in order to {action_desc}, then we could:",
            "duration": "If {action_desc} took {new_duration} instead of {old_duration}, then we could:",
            "til": "If {fact_desc} did not become {state} at time {time}, then we could:",
        }

        # Use profile for mappings if available, otherwise use defaults
        if self.profile:
            self.location_names = self.profile.location_names
            self.object_names = self.profile.object_names
            self.type_labels = self.profile.type_labels
            # Override templates if provided in profile
            if self.profile.templates:
                self.templates.update(self.profile.templates)
        else:
            # Default mappings (backwards compatible)
            self.location_names = {
                "a": "Depot",
                "b": "Butcher",
                "c": "Grocer",
            }
            self.object_names = {
                "t1": "T1",
                "t2": "T2",
                "d1": "D1",
                "m": "the meat",
                "ce": "the cereal",
            }
            self.type_labels = {
                "truck": "truck",
                "driver": "driver",
                "location": "",
                "prod": "",
                "meat": "",
                "cereal": "",
            }

    def _get_action_description(self, action: 'Action', bindings: Optional[Dict[str, str]] = None) -> str:
        """
        Get a human-readable description for an action.
        Prefers profile action_descriptions (positional {0},{1} format) over raw PDDL comments.
        """
        action_name = action.name

        # Try profile action_descriptions first (clean, positional format)
        if self.profile and action_name in self.profile.action_descriptions:
            desc_template = self.profile.action_descriptions[action_name]
            # Map positional {0},{1},... to readable values or variable names
            positional_values = []
            for param in action.parameters:
                if bindings and param.name in bindings:
                    positional_values.append(self._get_readable_value(bindings[param.name]))
                else:
                    positional_values.append(param.name)
            try:
                return desc_template.format(*positional_values)
            except (IndexError, KeyError):
                pass  # Fall through to comment-based approach

        # Fallback to PDDL comment with parameter substitution
        if action.comment:
            desc = action.comment
            if bindings:
                desc = self._substitute_parameters(desc, bindings)
            return desc

        # Last resort: action name
        return action_name.replace("_", " ")

    def _get_action_infinitive(self, action: 'Action', bindings: Optional[Dict[str, str]] = None) -> str:
        """
        Get the infinitive form of an action description for 'in order to ...' context.
        E.g. 'drive Truck 1 from Depot to Butcher' instead of 'Driver 1 drives Truck 1 from ...'
        Falls back to _get_action_description if no infinitive is defined.
        """
        action_name = action.name

        # Try profile action_infinitives first
        if self.profile and hasattr(self.profile, 'action_infinitives') and action_name in self.profile.action_infinitives:
            desc_template = self.profile.action_infinitives[action_name]
            positional_values = []
            for param in action.parameters:
                if bindings and param.name in bindings:
                    positional_values.append(self._get_readable_value(bindings[param.name]))
                else:
                    positional_values.append(param.name)
            try:
                return desc_template.format(*positional_values)
            except (IndexError, KeyError):
                pass

        # Fallback to regular description
        return self._get_action_description(action, bindings)

    def _get_precondition_description(self, predicate_name: str, action: 'Action',
                                       bindings: Optional[Dict[str, str]] = None) -> str:
        """
        Get a human-readable description for a precondition.
        Prefers profile predicate_descriptions over raw PDDL comments.
        """
        # Try profile predicate_descriptions first
        if self.profile and predicate_name in self.profile.predicate_descriptions:
            desc_template = self.profile.predicate_descriptions[predicate_name]
            # Find the predicate's parameters from the action's preconditions
            for precond in action.preconditions:
                if precond.name == predicate_name:
                    positional_values = []
                    for param_var in precond.parameters:
                        if bindings and param_var in bindings:
                            positional_values.append(self._get_readable_value(bindings[param_var]))
                        else:
                            positional_values.append(param_var)
                    try:
                        return desc_template.format(*positional_values)
                    except (IndexError, KeyError):
                        break
            return desc_template

        # Fallback to PDDL comment
        for precond in action.preconditions:
            if precond.name == predicate_name and precond.comment:
                desc = precond.comment
                if bindings:
                    desc = self._substitute_parameters(desc, bindings)
                return desc

        # Last resort: generate from predicate name
        return self._default_predicate_description(predicate_name,
                                                    getattr(self, '_last_abstraction_params', {}))

    def _get_catalog(self) -> 'PredicateCatalog':
        """Get or create the predicate catalog (lazy loading)."""
        if self.catalog is None:
            try:
                from predicate_processor import PredicateCatalog
                self.catalog = PredicateCatalog(self.domain, self.profile)
            except ImportError:
                return None
        return self.catalog

    def _get_readable_value(self, value: str) -> str:
        """Get human-readable version of a value."""
        if self.profile:
            return self.profile.get_readable_value(value)
        return self.object_names.get(value,
               self.location_names.get(value, value.upper() if len(value) <= 3 else value))
    
    def parse_abstraction(self, abstraction_str: str) -> Abstraction:
        """
        Parse an abstraction specification string.
        
        Example input: "abstract predicate (refrigerated ?t - truck) from action extend_meat_life"
        """
        import re
        
        # Pattern for predicate abstraction
        pred_pattern = r'abstract predicate \((\w+)([^)]*)\) from action (\w+)'
        match = re.match(pred_pattern, abstraction_str)
        
        if match:
            pred_name = match.group(1)
            params_str = match.group(2)
            action_name = match.group(3)
            
            # Parse parameters
            params = {}
            param_pattern = r'\?(\w+)\s*-\s*(\w+)'
            for p in re.finditer(param_pattern, params_str):
                params[f"?{p.group(1)}"] = p.group(2)
            
            return Abstraction(
                abstraction_type="predicate",
                predicate_name=pred_name,
                action_name=action_name,
                parameters=params
            )
        
        # Pattern for duration abstraction
        dur_pattern = r'abstract duration from action (\w+)'
        match = re.match(dur_pattern, abstraction_str)
        
        if match:
            return Abstraction(
                abstraction_type="duration",
                predicate_name="",
                action_name=match.group(1),
                parameters={}
            )
        
        raise ValueError(f"Could not parse abstraction: {abstraction_str}")
    
    def generate_explanation(self, abstraction: Abstraction, 
                            parameter_bindings: Optional[Dict[str, str]] = None,
                            new_plan: Optional[List[PlanStep]] = None) -> str:
        """
        Generate a natural language explanation for the given abstraction.
        
        Args:
            abstraction: The abstraction specification
            parameter_bindings: Optional mapping of variables to ground values
            new_plan: Optional new plan that results from the abstraction
            
        Returns:
            Human-readable explanation string
        """
        if abstraction.abstraction_type == "predicate":
            return self._generate_predicate_explanation(abstraction, parameter_bindings, new_plan)
        elif abstraction.abstraction_type == "duration":
            return self._generate_duration_explanation(abstraction, parameter_bindings, new_plan)
        elif abstraction.abstraction_type == "til":
            return self._generate_til_explanation(abstraction, parameter_bindings, new_plan)
        else:
            return f"Unknown abstraction type: {abstraction.abstraction_type}"
    
    def _generate_predicate_explanation(self, abstraction: Abstraction,
                                        parameter_bindings: Optional[Dict[str, str]],
                                        new_plan: Optional[List[PlanStep]]) -> str:
        """Generate explanation for predicate abstraction."""
        
        # Get the action
        action = self.parser.get_action_by_name(abstraction.action_name)
        if not action:
            return f"Error: Action {abstraction.action_name} not found"
        
        # Get descriptions using profile-aware methods
        precondition_desc = self._get_precondition_description(
            abstraction.predicate_name, action, parameter_bindings
        )
        # Use infinitive form for "in order to ..." context
        action_desc = self._get_action_infinitive(action, parameter_bindings)
        
        # Build the explanation
        explanation = self.templates["predicate"].format(
            precondition_desc=precondition_desc,
            action_desc=action_desc
        )
        
        # Add the new plan if provided
        if new_plan:
            explanation += "\n\n" + self._verbalize_plan(new_plan)
        
        return explanation
    
    def _generate_duration_explanation(self, abstraction: Abstraction,
                                       parameter_bindings: Optional[Dict[str, str]],
                                       new_plan: Optional[List[PlanStep]]) -> str:
        """Generate explanation for duration abstraction."""
        
        action = self.parser.get_action_by_name(abstraction.action_name)
        if not action:
            return f"Error: Action {abstraction.action_name} not found"
        
        action_desc = self._get_action_description(action, parameter_bindings)
        
        explanation = f"If {action_desc} took 0 minutes, then we could:"
        
        if new_plan:
            explanation += "\n\n" + self._verbalize_plan(new_plan)
        
        return explanation
    
    def _generate_til_explanation(self, abstraction: Abstraction,
                                  parameter_bindings: Optional[Dict[str, str]],
                                  new_plan: Optional[List[PlanStep]]) -> str:
        """Generate explanation for timed initial literal abstraction."""
        
        explanation = f"If it were not the case that {abstraction.predicate_name} became false at the specified time, then we could:"
        
        if new_plan:
            explanation += "\n\n" + self._verbalize_plan(new_plan)
        
        return explanation
    
    def _default_predicate_description(self, pred_name: str, params: Dict[str, str]) -> str:
        """Generate a default description for a predicate without a comment."""
        # Convert underscore names to spaces
        readable_name = pred_name.replace("_", " ")
        
        # Build parameter description
        param_desc = ", ".join([f"{v} {k}" for k, v in params.items()])
        
        return f"{readable_name} ({param_desc})"
    
    def _substitute_parameters(self, text: str, bindings: Dict[str, str]) -> str:
        """
        Replace parameter variables with their bound values,
        with context-aware deduplication to avoid phrases like
        'Driver Driver 1' or 'the meat the meat'.
        """
        import re as _re
        result = text
        for var, value in bindings.items():
            readable_value = self._get_readable_value(value)

            # Find every occurrence of var in the current result
            # and check context before it to avoid redundancy
            while var in result:
                idx = result.index(var)
                prefix = result[:idx]
                suffix = result[idx + len(var):]

                cleaned_value = self._deduplicate_prefix(prefix, readable_value)
                result = prefix + cleaned_value + suffix

        # Clean up any remaining awkward patterns
        result = self._cleanup_text(result)
        return result

    def _deduplicate_prefix(self, prefix: str, readable_value: str) -> str:
        """
        Given the text before a variable and the readable value to insert,
        remove redundant type words. Handles cases like:
          prefix='Driver '     + value='Driver 1'    → 'Driver 1'    (strip 'Driver ' from prefix handled by returning just '1' — actually we keep value and strip prefix)

        Strategy: if the prefix ends with a word/phrase that the readable_value
        starts with (case-insensitive), remove the overlap from the readable_value.
        Also handles 'the X' patterns and 'location' prefix.
        """
        import re as _re

        # Normalise for comparison
        prefix_stripped = prefix.rstrip()
        value_lower = readable_value.lower()

        # Patterns to check (longest first):
        # e.g. prefix ends with "the truck " and value is "Truck 1"
        # e.g. prefix ends with "Driver " and value is "Driver 1"
        # e.g. prefix ends with "the meat " and value is "the meat"
        # e.g. prefix ends with "the produce " and value is "the cereal"
        # e.g. prefix ends with "location " and value is "Depot"

        # Case 1: prefix ends with the exact readable value (e.g. "the meat " + "the meat")
        # Check if the last N words of prefix match the start of readable_value
        prefix_words = prefix_stripped.split()
        value_words = readable_value.split()

        if prefix_words and value_words:
            # Check for full overlap: prefix ends with same words as value starts with
            for overlap_len in range(min(len(prefix_words), len(value_words)), 0, -1):
                prefix_tail = " ".join(prefix_words[-overlap_len:]).lower()
                value_head = " ".join(value_words[:overlap_len]).lower()
                if prefix_tail == value_head:
                    # Remove the overlapping words from the readable value
                    remaining = " ".join(value_words[overlap_len:])
                    if remaining:
                        return remaining
                    else:
                        # The entire value is redundant with prefix — keep value, strip prefix overlap
                        # We need to return the value as-is but remove the overlap from prefix
                        # Since we can't modify prefix here, return value and we'll handle cleanup
                        return readable_value

            # Case 2: prefix ends with "the <type>" and value is "the <specific>"
            # e.g. "the produce " + "the cereal" → just "the cereal" (remove "the produce" from prefix)
            # or "the truck " + "Truck 1" → "Truck 1" (remove "the truck" from prefix)
            if len(prefix_words) >= 2 and prefix_words[-2].lower() == "the":
                type_word = prefix_words[-1].lower()
                value_first = value_words[0].lower()

                # "the truck" + "Truck 1" → value starts with the type word
                if value_first == type_word:
                    return readable_value  # will be cleaned up to remove "the truck" from prefix

                # "the produce" + "the cereal" → different article+noun, keep value
                if value_words[0].lower() == "the":
                    return readable_value  # cleanup will handle prefix

            # Case 3: prefix ends with "location" and value is a proper name
            if prefix_words and prefix_words[-1].lower() == "location":
                return readable_value  # cleanup will strip "location "

        return readable_value

    def _cleanup_text(self, text: str) -> str:
        """
        Post-process text to fix remaining awkward patterns.
        """
        import re as _re

        # Fix "Driver Driver 1" → "Driver 1"
        text = _re.sub(r'\b([Dd]river)\s+\1\s+', r'\1 ', text, flags=_re.IGNORECASE)

        # Fix "the truck Truck 1" → "Truck 1"  (remove "the truck " before "Truck N")
        text = _re.sub(r'\bthe\s+truck\s+(Truck\s+\d+)', r'\1', text, flags=_re.IGNORECASE)

        # Fix "the meat the meat" → "the meat"
        text = _re.sub(r'\b(the\s+\w+)\s+\1\b', r'\1', text, flags=_re.IGNORECASE)

        # Fix "the produce the cereal" → "the cereal"
        # More general: "the <type> the <specific>" → "the <specific>"
        text = _re.sub(r'\bthe\s+(?:produce|product)\s+(the\s+\w+)', r'\1', text, flags=_re.IGNORECASE)

        # Fix "location Depot" → "Depot" (when it reads awkwardly)
        text = _re.sub(r'\blocation\s+([A-Z]\w+)', r'\1', text)

        # Fix double spaces
        text = _re.sub(r'  +', ' ', text)

        # Fix space before punctuation
        text = _re.sub(r'\s+([,.])', r'\1', text)

        return text.strip()
    
    def _verbalize_plan(self, plan: List[PlanStep]) -> str:
        """Convert a plan to natural language."""
        lines = []
        for step in plan:
            action = self.parser.get_action_by_name(step.action_name)

            if action:
                # Build bindings dict
                bindings = {}
                for i, param in enumerate(action.parameters):
                    if i < len(step.parameters):
                        bindings[param.name] = step.parameters[i]
                desc = self._get_action_description(action, bindings)
            else:
                # Fallback: just use action name and parameters
                readable_params = [self._get_readable_value(p) for p in step.parameters]
                desc = f"{step.action_name} {' '.join(readable_params)}"

            # Format the line
            desc = desc[0].upper() + desc[1:] if desc else desc
            duration_str = f"takes {step.duration} minutes" if step.duration else ""
            lines.append(f"{step.time:.2f}: {desc} ({duration_str})")

        return "\n".join(lines)
    
    def verbalize_action(self, action_name: str, ground_params: List[str]) -> str:
        """
        Generate a natural language description of a single action.

        Args:
            action_name: Name of the action (e.g., "drive_truck")
            ground_params: List of ground parameters (e.g., ["d1", "t1", "a", "b"])

        Returns:
            Human-readable description
        """
        action = self.parser.get_action_by_name(action_name)

        if not action:
            readable_params = [self._get_readable_value(p) for p in ground_params]
            return f"{action_name}({', '.join(readable_params)})"

        # Build bindings dict
        bindings = {}
        for i, param in enumerate(action.parameters):
            if i < len(ground_params):
                bindings[param.name] = ground_params[i]
        return self._get_action_description(action, bindings)

    def verbalize_effects(self, action_name: str,
                         ground_params: Optional[List[str]] = None) -> str:
        """
        Generate detailed natural language description of action effects.

        Args:
            action_name: Name of the action
            ground_params: Optional ground parameter values

        Returns:
            Natural language description of what changes
        """
        action = self.parser.get_action_by_name(action_name)
        if not action:
            return f"Effects of {action_name} unknown"

        # Build parameter bindings
        bindings = {}
        if ground_params:
            for i, param in enumerate(action.parameters):
                if i < len(ground_params):
                    bindings[param.name] = ground_params[i]

        effect_descriptions = []

        for effect in action.effects:
            # Determine if effect is positive or negative
            is_negated = effect.comment and "not" in effect.comment.lower()

            # Get predicate description
            catalog = self._get_catalog()
            if catalog:
                pred_desc = catalog.get_description(effect.name, bindings)
            else:
                pred_desc = effect.name.replace("_", " ")
                for var, val in bindings.items():
                    pred_desc = pred_desc.replace(var, self._get_readable_value(val))

            # Format effect description
            if is_negated:
                effect_descriptions.append(f"It will no longer be the case that {pred_desc}")
            else:
                effect_descriptions.append(f"It will become the case that {pred_desc}")

        if not effect_descriptions:
            return f"Action {action_name} has no recorded effects"

        # Combine effects
        if len(effect_descriptions) == 1:
            return effect_descriptions[0]
        else:
            return "The following changes occur:\n" + "\n".join(
                f"  - {desc}" for desc in effect_descriptions
            )

    def verbalize_goal(self, problem: Problem) -> str:
        """
        Verbalize goal conditions from a problem.

        Args:
            problem: Parsed Problem object

        Returns:
            Natural language description of goals
        """
        goal_descs = []

        for goal in problem.goal.goals:
            desc = self._verbalize_ground_predicate(goal.name, goal.arguments)
            goal_descs.append(desc)

        if not goal_descs:
            return "No goals specified"

        if len(goal_descs) == 1:
            return f"The goal is: {goal_descs[0]}"
        else:
            goals = "\n".join(f"  - {d}" for d in goal_descs)
            return f"The goals are:\n{goals}"

    def verbalize_initial_state(self, problem: Problem,
                               max_items: int = 10) -> str:
        """
        Verbalize initial state from a problem.

        Args:
            problem: Parsed Problem object
            max_items: Maximum number of items to include

        Returns:
            Natural language description of initial state
        """
        state_descs = []

        # Verbalize predicates
        for pred in problem.init.predicates[:max_items]:
            desc = self._verbalize_ground_predicate(pred.name, pred.arguments)
            state_descs.append(desc)

        # Note if truncated
        total = len(problem.init.predicates)
        if total > max_items:
            state_descs.append(f"... and {total - max_items} more facts")

        # Add timed literals summary if present
        if problem.init.timed_literals:
            til_count = len(problem.init.timed_literals)
            state_descs.append(f"({til_count} timed event(s) scheduled)")

        if not state_descs:
            return "Initial state is empty"

        return "Initial state:\n" + "\n".join(f"  - {d}" for d in state_descs)

    def _verbalize_ground_predicate(self, pred_name: str,
                                    arguments: List[str]) -> str:
        """
        Verbalize a ground predicate with specific arguments.

        Args:
            pred_name: Predicate name
            arguments: Ground argument values

        Returns:
            Natural language description
        """
        catalog = self._get_catalog()

        if catalog:
            # Use catalog with index-based bindings
            bindings = {str(i): arg for i, arg in enumerate(arguments)}
            return catalog.get_description(pred_name, bindings)

        # Fallback: simple description
        readable_args = [self._get_readable_value(arg) for arg in arguments]
        readable_name = pred_name.replace("_", " ")

        if len(arguments) == 0:
            return readable_name
        elif len(arguments) == 1:
            return f"{readable_args[0]} is {readable_name}"
        elif len(arguments) == 2:
            if pred_name in ("at", "in"):
                return f"{readable_args[0]} is {readable_name} {readable_args[1]}"
            return f"{readable_name}({', '.join(readable_args)})"
        else:
            return f"{readable_name}({', '.join(readable_args)})"

    def verbalize_problem_summary(self, problem: Problem) -> str:
        """
        Generate a complete summary of a problem.

        Args:
            problem: Parsed Problem object

        Returns:
            Natural language summary
        """
        lines = [
            f"Problem: {problem.name}",
            f"Domain: {problem.domain_name}",
            "",
            "Objects:"
        ]

        # List objects by type
        for obj_type, objects in problem.objects.items():
            readable_objs = [self._get_readable_value(o) for o in objects]
            lines.append(f"  - {obj_type}: {', '.join(readable_objs)}")

        lines.append("")
        lines.append(self.verbalize_initial_state(problem, max_items=5))
        lines.append("")
        lines.append(self.verbalize_goal(problem))

        if problem.goal.metric:
            lines.append(f"\nOptimization: {problem.goal.metric}")

        return "\n".join(lines)


def parse_plan_file(filepath: str) -> List[PlanStep]:
    """
    Parse a plan file and return list of PlanSteps.
    
    Plan format expected:
    0.001: (board_truck d1 t2 a) [0.010]
    """
    import re
    
    steps = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            
            # Pattern: TIME: (ACTION PARAMS) [DURATION]
            match = re.match(r'([\d.]+):\s*\((\w+)([^)]*)\)\s*\[([\d.]+)\]', line)
            if match:
                time = float(match.group(1))
                action_name = match.group(2)
                params_str = match.group(3).strip()
                duration = float(match.group(4))
                
                params = params_str.split() if params_str else []
                
                steps.append(PlanStep(
                    time=time,
                    action_name=action_name,
                    parameters=params,
                    duration=duration
                ))
    
    return steps


# Test
if __name__ == "__main__":
    from pddl_parser import PDDLParser
    
    # Parse the domain
    parser = PDDLParser()
    parser.parse_file("../domains/refrigerated_delivery_domain.pddl")
    
    # Create generator
    nlg = NLGGenerator(parser)
    
    # Test abstraction parsing
    abstraction_str = "abstract predicate (refrigerated ?t - truck) from action extend_meat_life"
    abstraction = nlg.parse_abstraction(abstraction_str)
    print(f"Parsed abstraction: {abstraction}")
    
    # Generate explanation
    explanation = nlg.generate_explanation(
        abstraction,
        parameter_bindings={"?t": "t1", "?m": "m"}
    )
    print(f"\nExplanation:\n{explanation}")