"""
PDDL Parser using AIPlan4EU Unified Planning Library
Extracts a "map" of all actions, predicates, and their associated comments.

This fulfills the supervisor requirement:
"Write a Python script (using AIPlan4EU) to parse the refrigerated_delivery.pddl 
and extract a 'map' of all actions, predicates, and their associated comments."
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# AIPlan4EU imports
try:
    from unified_planning.io import PDDLReader
    from unified_planning.shortcuts import *
    AIPLAN4EU_AVAILABLE = True
except ImportError:
    AIPLAN4EU_AVAILABLE = False
    print("Warning: unified-planning not installed. Run: pip install unified-planning")


@dataclass
class PredicateInfo:
    """Information about a predicate including its comment"""
    name: str
    parameters: List[Tuple[str, str]]  # [(param_name, type), ...]
    comment: Optional[str] = None


@dataclass
class ActionInfo:
    """Information about an action including its comment"""
    name: str
    parameters: List[Tuple[str, str]]  # [(param_name, type), ...]
    preconditions: List[str]  # List of predicate names used in preconditions
    effects: List[str]  # List of predicate names used in effects
    comment: Optional[str] = None
    precondition_comments: Dict[str, str] = field(default_factory=dict)  # pred_name -> comment


@dataclass 
class DomainMap:
    """
    Complete map of a PDDL domain with all actions, predicates, and comments.
    This is the "map" the supervisor requested.
    """
    domain_name: str
    predicates: Dict[str, PredicateInfo]  # predicate_name -> PredicateInfo
    actions: Dict[str, ActionInfo]  # action_name -> ActionInfo
    types: Dict[str, str]  # type -> supertype
    
    def __str__(self):
        output = []
        output.append(f"Domain: {self.domain_name}")
        output.append(f"\nPredicates ({len(self.predicates)}):")
        for name, pred in self.predicates.items():
            output.append(f"  - {name}: {pred.comment or 'No comment'}")
        output.append(f"\nActions ({len(self.actions)}):")
        for name, action in self.actions.items():
            output.append(f"  - {name}: {action.comment or 'No comment'}")
        return "\n".join(output)


class AIPlan4EUParser:
    """
    Parser that uses AIPlan4EU unified-planning library to parse PDDL,
    then extracts comments from the raw file.
    """
    
    def __init__(self):
        self.domain_map = None
        self.raw_content = None
    
    def parse(self, domain_file: str, problem_file: Optional[str] = None) -> DomainMap:
        """
        Parse a PDDL domain file and extract the complete map.
        
        Args:
            domain_file: Path to the domain PDDL file
            problem_file: Optional path to problem file
            
        Returns:
            DomainMap with all actions, predicates, and comments
        """
        # Read raw content for comment extraction
        with open(domain_file, 'r') as f:
            self.raw_content = f.read()
        
        # Use AIPlan4EU to parse the PDDL structure
        if AIPLAN4EU_AVAILABLE:
            reader = PDDLReader()
            if problem_file:
                problem = reader.parse_problem(domain_file, problem_file)
                domain_name = problem.name
                # Extract from problem
                predicates = self._extract_predicates_aiplan(problem)
                actions = self._extract_actions_aiplan(problem)
                types = self._extract_types_aiplan(problem)
            else:
                # Parse domain only
                result = reader.parse_problem(domain_file)
                domain_name = str(result.name) if hasattr(result, 'name') else "unknown"
                predicates = self._extract_predicates_aiplan(result)
                actions = self._extract_actions_aiplan(result)
                types = self._extract_types_aiplan(result)
        else:
            # Fallback to regex parsing if AIPlan4EU not available
            domain_name = self._extract_domain_name_regex()
            predicates = self._extract_predicates_regex()
            actions = self._extract_actions_regex()
            types = self._extract_types_regex()
        
        # Extract comments from raw content and add to structures
        self._add_comments_to_predicates(predicates)
        self._add_comments_to_actions(actions)
        
        self.domain_map = DomainMap(
            domain_name=domain_name,
            predicates=predicates,
            actions=actions,
            types=types
        )
        
        return self.domain_map
    
    def _extract_predicates_aiplan(self, problem) -> Dict[str, PredicateInfo]:
        """Extract predicates using AIPlan4EU"""
        predicates = {}
        
        # Get fluents (predicates) from the problem
        for fluent in problem.fluents:
            params = [(p.name, str(p.type)) for p in fluent.signature]
            predicates[fluent.name] = PredicateInfo(
                name=fluent.name,
                parameters=params,
                comment=None
            )
        
        return predicates
    
    def _extract_actions_aiplan(self, problem) -> Dict[str, ActionInfo]:
        """Extract actions using AIPlan4EU"""
        actions = {}
        
        for action in problem.actions:
            params = [(p.name, str(p.type)) for p in action.parameters]
            
            # Extract precondition predicate names
            precond_names = []
            if hasattr(action, 'preconditions'):
                for precond in action.preconditions:
                    precond_names.extend(self._extract_fluent_names(precond))
            
            # Extract effect predicate names  
            effect_names = []
            if hasattr(action, 'effects'):
                for effect in action.effects:
                    effect_names.extend(self._extract_fluent_names(effect))
            
            actions[action.name] = ActionInfo(
                name=action.name,
                parameters=params,
                preconditions=precond_names,
                effects=effect_names,
                comment=None
            )
        
        return actions
    
    def _extract_fluent_names(self, expression) -> List[str]:
        """Recursively extract fluent names from an expression"""
        names = []
        if hasattr(expression, 'fluent'):
            names.append(expression.fluent().name)
        if hasattr(expression, 'args'):
            for arg in expression.args:
                names.extend(self._extract_fluent_names(arg))
        return names
    
    def _extract_types_aiplan(self, problem) -> Dict[str, str]:
        """Extract type hierarchy using AIPlan4EU"""
        types = {}
        for user_type in problem.user_types:
            parent = user_type.father
            types[user_type.name] = parent.name if parent else "object"
        return types
    
    # ========== REGEX FALLBACK METHODS ==========
    
    def _extract_domain_name_regex(self) -> str:
        match = re.search(r'\(define\s*\(domain\s+(\S+)\)', self.raw_content)
        return match.group(1) if match else "unknown"
    
    def _extract_predicates_regex(self) -> Dict[str, PredicateInfo]:
        predicates = {}
        match = re.search(r'\(:predicates\s*(.*?)\)\s*(?=\(:|\s*$)', self.raw_content, re.DOTALL)
        if match:
            pred_section = match.group(1)
            # Find predicates: (name ?param - type ...)
            for m in re.finditer(r'\((\w+)([^)]*)\)', pred_section):
                name = m.group(1)
                params_str = m.group(2)
                params = self._parse_parameters(params_str)
                predicates[name] = PredicateInfo(name=name, parameters=params)
        return predicates
    
    def _extract_actions_regex(self) -> Dict[str, ActionInfo]:
        actions = {}
        # Find durative-action or action blocks
        pattern = r'\(:durative-action\s+(\w+)(.*?)(?=\(:durative-action|\(:action|\)\s*\)\s*$)'
        for m in re.finditer(pattern, self.raw_content, re.DOTALL):
            name = m.group(1)
            body = m.group(2)
            
            # Extract parameters
            params_match = re.search(r':parameters\s*\(([^)]*)\)', body)
            params = self._parse_parameters(params_match.group(1)) if params_match else []
            
            # Extract precondition predicates
            precond_match = re.search(r':condition\s*\(and(.*?)\)\s*:effect', body, re.DOTALL)
            precond_names = []
            if precond_match:
                precond_names = re.findall(r'\((?:over all|at start|at end)\s*\((\w+)', precond_match.group(1))
            
            actions[name] = ActionInfo(
                name=name,
                parameters=params,
                preconditions=precond_names,
                effects=[],
                comment=None
            )
        return actions
    
    def _extract_types_regex(self) -> Dict[str, str]:
        types = {}
        match = re.search(r'\(:types\s*(.*?)\)', self.raw_content, re.DOTALL)
        if match:
            for line in match.group(1).split('\n'):
                if ' - ' in line:
                    parts = line.strip().split(' - ')
                    if len(parts) == 2:
                        subtypes = parts[0].split()
                        supertype = parts[1].strip()
                        for st in subtypes:
                            if st:
                                types[st] = supertype
        return types
    
    def _parse_parameters(self, params_str: str) -> List[Tuple[str, str]]:
        """Parse parameter string like '?d - driver ?t - truck' into list of tuples"""
        params = []
        if not params_str:
            return params
        
        # Split by ' - ' to get groups
        parts = re.split(r'\s+-\s+', params_str.strip())
        
        current_vars = []
        for i, part in enumerate(parts):
            tokens = part.split()
            if i == 0:
                # First part has only variables
                current_vars = [t for t in tokens if t.startswith('?')]
            else:
                # Type is first token, assign to previous vars
                type_name = tokens[0] if tokens else "object"
                for var in current_vars:
                    params.append((var, type_name))
                # Remaining tokens are new variables
                current_vars = [t for t in tokens[1:] if t.startswith('?')]
        
        return params
    
    # ========== COMMENT EXTRACTION ==========
    
    def _add_comments_to_predicates(self, predicates: Dict[str, PredicateInfo]):
        """Extract comments for predicates from raw PDDL content"""
        for pred_name, pred_info in predicates.items():
            # Look for inline comment after predicate definition
            pattern = rf'\({pred_name}\s+[^)]*\)\s*;\s*([^\n]*)'
            match = re.search(pattern, self.raw_content)
            if match:
                pred_info.comment = match.group(1).strip()
    
    def _add_comments_to_actions(self, actions: Dict[str, ActionInfo]):
        """Extract comments for actions from raw PDDL content"""
        for action_name, action_info in actions.items():
            # Look for comment line before action definition
            pattern = rf';\s*([^\n]+)\n\s*\(:durative-action\s+{action_name}\b'
            match = re.search(pattern, self.raw_content)
            if match:
                action_info.comment = match.group(1).strip()
            
            # Look for precondition comments
            action_pattern = rf'\(:durative-action\s+{action_name}\b(.*?)(?=\(:durative-action|\)\s*\)\s*$)'
            action_match = re.search(action_pattern, self.raw_content, re.DOTALL)
            if action_match:
                action_body = action_match.group(1)
                # Find preconditions with inline comments
                precond_pattern = r'\((?:over all|at start|at end)\s*\((\w+)[^)]*\)\)\s*;\s*([^\n]*)'
                for m in re.finditer(precond_pattern, action_body):
                    pred_name = m.group(1)
                    comment = m.group(2).strip()
                    action_info.precondition_comments[pred_name] = comment


def create_domain_map(domain_file: str, problem_file: Optional[str] = None) -> DomainMap:
    """
    Convenience function to create a domain map.
    
    This is the main entry point for the supervisor's requirement:
    "extract a 'map' of all actions, predicates, and their associated comments"
    """
    parser = AIPlan4EUParser()
    return parser.parse(domain_file, problem_file)


# ========== TEST ==========
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        domain_file = sys.argv[1]
    else:
        domain_file = "domains/refrigerated_delivery_domain.pddl"
    
    print(f"Parsing: {domain_file}")
    print("=" * 60)
    
    domain_map = create_domain_map(domain_file)
    
    print(domain_map)
    print("\n" + "=" * 60)
    print("\nDetailed Predicate Map:")
    for name, pred in domain_map.predicates.items():
        print(f"  {name}:")
        print(f"    Parameters: {pred.parameters}")
        print(f"    Comment: {pred.comment}")
    
    print("\nDetailed Action Map:")
    for name, action in domain_map.actions.items():
        print(f"  {name}:")
        print(f"    Comment: {action.comment}")
        print(f"    Parameters: {action.parameters}")
        print(f"    Preconditions: {action.preconditions}")
        print(f"    Precondition Comments: {action.precondition_comments}")
