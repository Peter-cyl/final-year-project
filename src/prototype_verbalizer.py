"""
Prototype Verbalizer
Takes technical input like "predicate-refrigeratedttruck" and generates natural language.

This fulfills the supervisor requirement:
"Create a Python function that takes a hard-coded technical input (e.g., 
'predicate-can_deliverpprod') and uses the parsed map to generate the 
full natural language sentence."

Input format examples:
- "predicate-refrigeratedttruck" -> predicate "refrigerated" with param ?t of type truck
- "predicate-can_deliverpprod" -> predicate "can_deliver" with param ?p of type prod
- "predicate-boardedddriverttruck" -> predicate "boarded" with params ?d:driver, ?t:truck
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from aiplan4eu_parser import DomainMap, create_domain_map


@dataclass
class ParsedInput:
    """Parsed technical input"""
    input_type: str  # "predicate", "duration", "til"
    predicate_name: str
    parameters: List[Tuple[str, str]]  # [(param_name, type), ...]


class PrototypeVerbalizer:
    """
    Verbalizes technical planning inputs into natural language.
    
    Example:
        Input:  "predicate-refrigeratedttruck"
        Output: "If we did not require that the truck is refrigerated in order to 
                 extend the life of the meat, then we could use an alternative plan."
    """
    
    def __init__(self, domain_map: DomainMap):
        self.domain_map = domain_map
        
        # Human-readable names for objects (customize per domain)
        self.object_labels = {
            "truck": "the truck",
            "driver": "the driver", 
            "location": "the location",
            "prod": "the produce",
            "meat": "the meat",
            "cereal": "the cereal",
        }
    
    def parse_technical_input(self, technical_input: str) -> ParsedInput:
        """
        Parse the technical input format.
        
        Format: {type}-{predicate_name}{param1_name}{param1_type}{param2_name}{param2_type}...
        
        Examples:
            "predicate-refrigeratedttruck" 
                -> type="predicate", name="refrigerated", params=[("t", "truck")]
            
            "predicate-can_deliverpprod"
                -> type="predicate", name="can_deliver", params=[("p", "prod")]
            
            "predicate-boardedddriverttruck"
                -> type="predicate", name="boarded", params=[("d", "driver"), ("t", "truck")]
        """
        # Split by first hyphen to get type
        parts = technical_input.split("-", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid input format: {technical_input}")
        
        input_type = parts[0]  # "predicate", "duration", etc.
        rest = parts[1]  # "refrigeratedttruck"
        
        # Find the predicate name by matching against known predicates
        predicate_name = None
        params_str = ""
        
        for pred_name in self.domain_map.predicates.keys():
            if rest.startswith(pred_name):
                predicate_name = pred_name
                params_str = rest[len(pred_name):]
                break
        
        if not predicate_name:
            # Try to infer - assume predicate name is until first lowercase+type pattern
            # This handles cases where predicate isn't in our map
            predicate_name = rest
            params_str = ""
        
        # Parse parameters from remaining string
        # Format: {param_name}{param_type}{param_name}{param_type}...
        parameters = self._parse_param_string(params_str)
        
        return ParsedInput(
            input_type=input_type,
            predicate_name=predicate_name,
            parameters=parameters
        )
    
    def _parse_param_string(self, params_str: str) -> List[Tuple[str, str]]:
        """
        Parse parameter string like "ttruck" or "ddriverttruck" into param list.
        
        Strategy: Match against known types from domain map.
        """
        parameters = []
        remaining = params_str
        
        # Known types from domain
        known_types = list(self.domain_map.types.keys()) + ["object"]
        # Sort by length (longest first) to match correctly
        known_types.sort(key=len, reverse=True)
        
        while remaining:
            matched = False
            # The param name is typically a single letter
            if len(remaining) >= 1:
                param_name = remaining[0]
                rest = remaining[1:]
                
                # Try to match a type
                for type_name in known_types:
                    if rest.startswith(type_name):
                        parameters.append((param_name, type_name))
                        remaining = rest[len(type_name):]
                        matched = True
                        break
                
                if not matched:
                    # No type matched, might be end of string or unknown format
                    break
            else:
                break
        
        return parameters
    
    def verbalize(self, technical_input: str) -> str:
        """
        Main function: Convert technical input to natural language.
        
        Args:
            technical_input: String like "predicate-refrigeratedttruck"
            
        Returns:
            Natural language explanation string
        """
        parsed = self.parse_technical_input(technical_input)
        
        if parsed.input_type == "predicate":
            return self._verbalize_predicate_abstraction(parsed)
        elif parsed.input_type == "duration":
            return self._verbalize_duration_abstraction(parsed)
        elif parsed.input_type == "til":
            return self._verbalize_til_abstraction(parsed)
        else:
            return f"Unknown abstraction type: {parsed.input_type}"
    
    def _verbalize_predicate_abstraction(self, parsed: ParsedInput) -> str:
        """Generate natural language for predicate abstraction."""
        
        # Get predicate info
        pred_info = self.domain_map.predicates.get(parsed.predicate_name)
        
        # Find which action(s) use this predicate as a precondition
        using_actions = []
        for action_name, action_info in self.domain_map.actions.items():
            if parsed.predicate_name in action_info.preconditions:
                using_actions.append(action_info)
        
        # Build predicate description
        if pred_info and pred_info.comment:
            pred_desc = self._substitute_params_in_comment(
                pred_info.comment, 
                pred_info.parameters,
                parsed.parameters
            )
        else:
            pred_desc = self._default_predicate_description(parsed.predicate_name, parsed.parameters)
        
        # Build action description
        if using_actions:
            action = using_actions[0]  # Use first matching action
            if action.comment:
                action_desc = self._substitute_params_in_comment(
                    action.comment,
                    action.parameters,
                    parsed.parameters
                )
            else:
                action_desc = action.name.replace("_", " ")
            
            # Check if action has a specific comment for this precondition
            if parsed.predicate_name in action.precondition_comments:
                pred_desc = self._substitute_params_in_comment(
                    action.precondition_comments[parsed.predicate_name],
                    action.parameters,
                    parsed.parameters
                )
        else:
            action_desc = "perform the action"
        
        # Generate the explanation
        explanation = (
            f"If we did not require that {pred_desc} in order to {action_desc}, "
            f"then we could use an alternative plan."
        )
        
        return explanation
    
    def _verbalize_duration_abstraction(self, parsed: ParsedInput) -> str:
        """Generate natural language for duration abstraction."""
        action_info = self.domain_map.actions.get(parsed.predicate_name)
        if action_info and action_info.comment:
            action_desc = action_info.comment
        else:
            action_desc = parsed.predicate_name.replace("_", " ")
        
        return f"If {action_desc} took 0 minutes, then we could use an alternative plan."
    
    def _verbalize_til_abstraction(self, parsed: ParsedInput) -> str:
        """Generate natural language for timed initial literal abstraction."""
        return f"If the timed condition for {parsed.predicate_name} was different, then we could use an alternative plan."
    
    def _substitute_params_in_comment(self, comment: str, 
                                       formal_params: List[Tuple[str, str]],
                                       actual_params: List[Tuple[str, str]]) -> str:
        """
        Substitute parameter placeholders in comment with readable text.
        
        Example:
            comment: "?t is refrigerated"
            formal_params: [("?t", "truck")]
            actual_params: [("t", "truck")]
            Result: "the truck is refrigerated"
        """
        result = comment
        
        # Build a mapping of param names to their types
        actual_type_map = {letter: ptype for letter, ptype in actual_params}
        
        # Replace each formal parameter
        for formal_param, formal_type in formal_params:
            param_letter = formal_param.lstrip("?")
            
            # Get the type - prefer actual params, fallback to formal
            param_type = actual_type_map.get(param_letter, formal_type)
            readable = self.object_labels.get(param_type, param_type)
            
            # Replace the parameter placeholder
            result = result.replace(formal_param, readable)
        
        # Clean up any double spaces or awkward phrasing
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
    
    def _default_predicate_description(self, pred_name: str, 
                                       params: List[Tuple[str, str]]) -> str:
        """Generate a default description when no comment exists."""
        readable_name = pred_name.replace("_", " ")
        
        if params:
            param_desc = " and ".join([
                self.object_labels.get(ptype, ptype) 
                for _, ptype in params
            ])
            return f"{param_desc} satisfies '{readable_name}'"
        
        return readable_name


def verbalize_technical_input(domain_file: str, technical_input: str) -> str:
    """
    Convenience function to verbalize a technical input.
    
    This is the main entry point for the supervisor's demo requirement:
    "Input: predicate-refrigeratedttruck -> Output: Sentence"
    
    Args:
        domain_file: Path to PDDL domain file
        technical_input: String like "predicate-refrigeratedttruck"
        
    Returns:
        Natural language explanation
    """
    domain_map = create_domain_map(domain_file)
    verbalizer = PrototypeVerbalizer(domain_map)
    return verbalizer.verbalize(technical_input)


# ========== DEMO ==========
if __name__ == "__main__":
    import sys
    import os
    
    # Default domain file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_domain = os.path.join(script_dir, "..", "domains", "refrigerated_delivery_domain.pddl")
    
    domain_file = sys.argv[1] if len(sys.argv) > 1 else default_domain
    
    print("=" * 70)
    print("PlanVerb Prototype Verbalizer Demo")
    print("=" * 70)
    
    # Parse domain
    print(f"\n1. Loading domain: {domain_file}")
    domain_map = create_domain_map(domain_file)
    print(f"   ✓ Loaded {len(domain_map.predicates)} predicates")
    print(f"   ✓ Loaded {len(domain_map.actions)} actions")
    
    # Create verbalizer
    verbalizer = PrototypeVerbalizer(domain_map)
    
    # Test cases - the exact format supervisor wants
    test_inputs = [
        "predicate-refrigeratedttruck",
        "predicate-can_deliverpprod", 
        "predicate-boardedddriverttruck",
        "predicate-inpprodttruck",
        "predicate-atl1locatablel2location",
    ]
    
    print("\n2. Verbalization Results:")
    print("-" * 70)
    
    for technical_input in test_inputs:
        print(f"\n   INPUT:  {technical_input}")
        try:
            result = verbalizer.verbalize(technical_input)
            print(f"   OUTPUT: {result}")
        except Exception as e:
            print(f"   ERROR:  {e}")
    
    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)
