"""
Natural Language Generator Module
Generates human-readable explanations from planning abstractions.

Takes:
- Abstraction specification (what was removed/changed)
- Parsed PDDL domain with comments
- Parameter bindings (optional)

Produces:
- Natural language explanation
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from pddl_parser import PDDLParser, Action, Predicate, Parameter


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
    """
    
    def __init__(self, parser: PDDLParser):
        self.parser = parser
        self.domain = parser.domain
        
        # Templates for different abstraction types
        self.templates = {
            "predicate": "If we did not require that {precondition_desc} in order to {action_desc}, then we could:",
            "duration": "If {action_desc} took {new_duration} instead of {old_duration}, then we could:",
            "til": "If {fact_desc} did not become {state} at time {time}, then we could:",
        }
        
        # Location name mappings (can be customized per domain)
        self.location_names = {
            "a": "Depot",
            "b": "Butcher", 
            "c": "Grocer",
        }
        
        # Object name mappings - use simple names that work in sentences
        self.object_names = {
            "t1": "T1",
            "t2": "T2",
            "d1": "D1",
            "m": "the meat",
            "ce": "the cereal",
        }
        
        # Type-aware mappings for better substitution
        self.type_labels = {
            "truck": "truck",
            "driver": "driver",
            "location": "",
            "prod": "",
            "meat": "",
            "cereal": "",
        }
    
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
        
        # Find the precondition that was abstracted
        precondition_comment = None
        for precond in action.preconditions:
            if precond.name == abstraction.predicate_name:
                precondition_comment = precond.comment
                break
        
        # If no comment found, generate a default one
        if not precondition_comment:
            precondition_comment = self._default_predicate_description(
                abstraction.predicate_name, 
                abstraction.parameters
            )
        
        # Get action description from comment
        action_desc = action.comment if action.comment else action.name
        
        # Apply parameter bindings if provided
        if parameter_bindings:
            precondition_comment = self._substitute_parameters(precondition_comment, parameter_bindings)
            action_desc = self._substitute_parameters(action_desc, parameter_bindings)
        
        # Build the explanation
        explanation = self.templates["predicate"].format(
            precondition_desc=precondition_comment,
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
        
        action_desc = action.comment if action.comment else action.name
        
        if parameter_bindings:
            action_desc = self._substitute_parameters(action_desc, parameter_bindings)
        
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
        """Replace parameter variables with their bound values."""
        result = text
        for var, value in bindings.items():
            # Get human-readable name if available
            readable_value = self.object_names.get(value, value)
            result = result.replace(var, readable_value)
        return result
    
    def _verbalize_plan(self, plan: List[PlanStep]) -> str:
        """Convert a plan to natural language."""
        lines = []
        for step in plan:
            action = self.parser.get_action_by_name(step.action_name)
            
            if action and action.comment:
                # Use the comment as template
                desc = action.comment
                
                # Substitute parameters
                for i, param in enumerate(action.parameters):
                    if i < len(step.parameters):
                        ground_value = step.parameters[i]
                        readable_value = self.object_names.get(
                            ground_value, 
                            self.location_names.get(ground_value, ground_value)
                        )
                        desc = desc.replace(param.name, readable_value)
            else:
                # Fallback: just use action name and parameters
                desc = f"{step.action_name} {' '.join(step.parameters)}"
            
            # Format the line
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
            return f"{action_name}({', '.join(ground_params)})"
        
        if action.comment:
            desc = action.comment
            
            # Substitute parameters
            for i, param in enumerate(action.parameters):
                if i < len(ground_params):
                    ground_value = ground_params[i]
                    readable_value = self.object_names.get(
                        ground_value,
                        self.location_names.get(ground_value, ground_value)
                    )
                    desc = desc.replace(param.name, readable_value)
            
            return desc
        else:
            return f"{action_name}({', '.join(ground_params)})"


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
