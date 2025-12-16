"""
PDDL Parser Module
Parses PDDL domain files and extracts:
- Action definitions
- Predicates
- Comments (for natural language generation)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


@dataclass
class Parameter:
    """Represents a typed parameter like ?t - truck"""
    name: str       # e.g., "?t"
    type: str       # e.g., "truck"


@dataclass
class Predicate:
    """Represents a predicate like (at ?t ?l)"""
    name: str                       # e.g., "at"
    parameters: List[str]           # e.g., ["?t", "?l"]
    comment: Optional[str] = None   # e.g., "?t is at location ?l"


@dataclass 
class Action:
    """Represents a PDDL action with its components and comments"""
    name: str
    comment: Optional[str]                          # Action-level comment
    parameters: List[Parameter] = field(default_factory=list)
    preconditions: List[Predicate] = field(default_factory=list)
    effects: List[Predicate] = field(default_factory=list)
    duration: Optional[str] = None


@dataclass
class Domain:
    """Represents a parsed PDDL domain"""
    name: str
    types: Dict[str, str] = field(default_factory=dict)         # type -> supertype
    predicates: List[Predicate] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)


class PDDLParser:
    """
    Parser for PDDL domain files that extracts structure and comments.
    
    Comments are extracted using the PDDL comment syntax (;)
    and associated with their corresponding elements.
    """
    
    def __init__(self):
        self.domain = None
    
    def parse_file(self, filepath: str) -> Domain:
        """Parse a PDDL domain file and return a Domain object."""
        with open(filepath, 'r') as f:
            content = f.read()
        return self.parse_string(content)
    
    def parse_string(self, content: str) -> Domain:
        """Parse PDDL content from a string."""
        # Extract domain name
        domain_name = self._extract_domain_name(content)
        
        # Extract types
        types = self._extract_types(content)
        
        # Extract predicates with comments
        predicates = self._extract_predicates(content)
        
        # Extract actions with comments
        actions = self._extract_actions(content)
        
        self.domain = Domain(
            name=domain_name,
            types=types,
            predicates=predicates,
            actions=actions
        )
        return self.domain
    
    def _extract_domain_name(self, content: str) -> str:
        """Extract the domain name from (define (domain NAME) ...)"""
        match = re.search(r'\(define\s*\(domain\s+(\S+)\)', content)
        return match.group(1) if match else "unknown"
    
    def _extract_types(self, content: str) -> Dict[str, str]:
        """Extract type hierarchy from (:types ...) block."""
        types = {}
        match = re.search(r'\(:types\s*(.*?)\)', content, re.DOTALL)
        if match:
            types_content = match.group(1)
            # Parse lines like: meat cereal - prod
            for line in types_content.split('\n'):
                line = line.strip()
                if ' - ' in line:
                    parts = line.split(' - ')
                    supertype = parts[-1].strip()
                    subtypes = parts[0].strip().split()
                    for subtype in subtypes:
                        if subtype:
                            types[subtype] = supertype
        return types
    
    def _extract_predicates(self, content: str) -> List[Predicate]:
        """Extract predicates with their associated comments."""
        predicates = []
        match = re.search(r'\(:predicates\s*(.*?)\)\s*(?=\(:|$)', content, re.DOTALL)
        if match:
            pred_content = match.group(1)
            # Find each predicate with optional preceding/inline comment
            pattern = r'(?:;\s*([^\n]*)\n\s*)?\((\w+)([^)]*)\)(?:\s*;\s*([^\n]*))?'
            for m in re.finditer(pattern, pred_content):
                pre_comment = m.group(1)
                pred_name = m.group(2)
                params_str = m.group(3)
                inline_comment = m.group(4)
                
                # Parse parameters
                params = re.findall(r'\?\w+', params_str)
                
                # Use inline comment if available, otherwise pre-comment
                comment = inline_comment or pre_comment
                
                predicates.append(Predicate(
                    name=pred_name,
                    parameters=params,
                    comment=comment.strip() if comment else None
                ))
        return predicates
    
    def _extract_actions(self, content: str) -> List[Action]:
        """Extract actions (durative and regular) with comments."""
        actions = []
        
        # Find all durative-action blocks
        # First, split content by action declarations
        action_blocks = re.split(r'(?=;\s*[A-Z].*\n\s*\(:durative-action)', content)
        
        for block in action_blocks:
            # Pattern to find durative-action with preceding comment
            action_pattern = r';\s*([^\n]+)\n\s*\(:durative-action\s+(\w+)(.*)'
            match = re.search(action_pattern, block, re.DOTALL)
            
            if match:
                comment = match.group(1).strip()
                action_name = match.group(2)
                action_body = match.group(3)
                
                # Extract parameters
                parameters = self._extract_parameters(action_body)
                
                # Extract duration
                duration = self._extract_duration(action_body)
                
                # Extract preconditions with comments
                preconditions = self._extract_preconditions(action_body)
                
                # Extract effects
                effects = self._extract_effects(action_body)
                
                actions.append(Action(
                    name=action_name,
                    comment=comment,
                    parameters=parameters,
                    preconditions=preconditions,
                    effects=effects,
                    duration=duration
                ))
        
        return actions
    
    def _extract_parameters(self, action_body: str) -> List[Parameter]:
        """Extract parameters from :parameters section."""
        parameters = []
        match = re.search(r':parameters\s*\(([^)]*)\)', action_body)
        if match:
            params_str = match.group(1)
            # Parse typed parameters like ?d - driver ?t - truck
            # Split by type declarations
            parts = re.split(r'\s+-\s+', params_str)
            
            current_vars = []
            for i, part in enumerate(parts):
                tokens = part.strip().split()
                if i < len(parts) - 1:
                    # All but last token are variables, last would be type
                    type_name = tokens[-1] if tokens else ""
                    vars_in_part = [t for t in tokens[:-1] if t.startswith('?')] if i > 0 else [t for t in tokens if t.startswith('?')]
                    
                    if i > 0 and current_vars:
                        # Assign previous type
                        prev_type = tokens[0] if tokens else ""
                        for v in current_vars:
                            parameters.append(Parameter(name=v, type=prev_type))
                        current_vars = []
                    
                    current_vars = [t for t in tokens if t.startswith('?')]
                else:
                    # Last part - this is the type for remaining vars
                    type_name = tokens[0] if tokens else ""
                    for v in current_vars:
                        parameters.append(Parameter(name=v, type=type_name))
        
        # Simpler approach - just use regex
        parameters = []
        match = re.search(r':parameters\s*\(([^)]*)\)', action_body)
        if match:
            params_str = match.group(1)
            # Find all ?var - type patterns
            pattern = r'(\?[\w]+)\s*(?:-\s*(\w+))?'
            
            # Better: split by hyphen and track
            segments = re.split(r'\s+-\s+', params_str)
            
            for i in range(len(segments) - 1):
                vars_part = segments[i].split()
                type_part = segments[i + 1].split()[0] if segments[i + 1].split() else ""
                
                for var in vars_part:
                    if var.startswith('?'):
                        parameters.append(Parameter(name=var, type=type_part))
            
            # Handle last segment if it has remaining vars
            if len(segments) == 1:
                # No types specified, just vars
                for var in segments[0].split():
                    if var.startswith('?'):
                        parameters.append(Parameter(name=var, type="object"))
        
        return parameters
    
    def _extract_duration(self, action_body: str) -> Optional[str]:
        """Extract duration expression."""
        match = re.search(r':duration\s*\(=\s*\?duration\s+([^)]+)\)', action_body)
        return match.group(1).strip() if match else None
    
    def _extract_preconditions(self, action_body: str) -> List[Predicate]:
        """Extract preconditions with their inline comments."""
        preconditions = []
        
        # Find the :condition block
        match = re.search(r':condition\s*\(and\s*(.*?)\)\s*:effect', action_body, re.DOTALL)
        if match:
            cond_content = match.group(1)
            
            # Find predicates with optional inline comments
            # Pattern matches things like: (over all (at ?truck ?loc)) ; comment
            pattern = r'\((over all|at start|at end)\s*\((\w+)([^)]*)\)\)(?:\s*;\s*([^\n]*))?'
            
            for m in re.finditer(pattern, cond_content):
                timing = m.group(1)
                pred_name = m.group(2)
                params_str = m.group(3)
                comment = m.group(4)
                
                params = re.findall(r'\?\w+', params_str)
                
                preconditions.append(Predicate(
                    name=pred_name,
                    parameters=params,
                    comment=comment.strip() if comment else None
                ))
        
        return preconditions
    
    def _extract_effects(self, action_body: str) -> List[Predicate]:
        """Extract effects from :effect section."""
        effects = []
        
        match = re.search(r':effect\s*\(and\s*(.*?)\)\s*\)', action_body, re.DOTALL)
        if match:
            effect_content = match.group(1)
            
            # Pattern for effects like (at end (at ?p ?l))
            pattern = r'\((at start|at end)\s*\((not\s*)?\((\w+)([^)]*)\)\)\)'
            
            for m in re.finditer(pattern, effect_content):
                timing = m.group(1)
                negated = m.group(2) is not None
                pred_name = m.group(3)
                params_str = m.group(4)
                
                params = re.findall(r'\?\w+', params_str)
                
                effects.append(Predicate(
                    name=pred_name,
                    parameters=params,
                    comment=f"{'not ' if negated else ''}{pred_name}"
                ))
        
        return effects
    
    def get_action_by_name(self, name: str) -> Optional[Action]:
        """Get an action by its name."""
        if self.domain:
            for action in self.domain.actions:
                if action.name == name:
                    return action
        return None
    
    def get_predicate_by_name(self, name: str) -> Optional[Predicate]:
        """Get a predicate definition by its name."""
        if self.domain:
            for pred in self.domain.predicates:
                if pred.name == name:
                    return pred
        return None


# Simple test
if __name__ == "__main__":
    parser = PDDLParser()
    
    # Test with a simple domain string
    test_domain = """
    (define (domain test)
      (:types truck location)
      (:predicates
        (at ?t - truck ?l - location)  ; ?t is at ?l
      )
      
      ; Drive the truck ?t from ?from to ?to
      (:durative-action drive
        :parameters (?t - truck ?from - location ?to - location)
        :duration (= ?duration 10)
        :condition (and
          (at start (at ?t ?from))  ; ?t is at ?from
        )
        :effect (and
          (at start (not (at ?t ?from)))
          (at end (at ?t ?to))
        )
      )
    )
    """
    
    domain = parser.parse_string(test_domain)
    print(f"Domain: {domain.name}")
    print(f"Types: {domain.types}")
    print(f"Predicates: {domain.predicates}")
    print(f"Actions: {domain.actions}")
