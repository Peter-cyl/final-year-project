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


@dataclass
class GroundPredicate:
    """Represents a ground predicate instance like (at t1 a)"""
    name: str                       # e.g., "at"
    arguments: List[str]            # e.g., ["t1", "a"]
    negated: bool = False           # True if this is (not (pred ...))


@dataclass
class TimedLiteral:
    """Represents a timed initial literal like (at 22 (not (can_deliver m)))"""
    time: float
    predicate: GroundPredicate


@dataclass
class FunctionValue:
    """Represents a function assignment like (= (time_to_drive a b) 20)"""
    name: str                       # e.g., "time_to_drive"
    arguments: List[str]            # e.g., ["a", "b"]
    value: float                    # e.g., 20.0


@dataclass
class InitialState:
    """Represents the initial state from (:init ...) section"""
    predicates: List[GroundPredicate] = field(default_factory=list)
    functions: List[FunctionValue] = field(default_factory=list)
    timed_literals: List[TimedLiteral] = field(default_factory=list)


@dataclass
class GoalCondition:
    """Represents goal conditions from (:goal ...) section"""
    goals: List[GroundPredicate] = field(default_factory=list)
    metric: Optional[str] = None    # e.g., "minimize (total-time)"


@dataclass
class Problem:
    """Represents a parsed PDDL problem"""
    name: str
    domain_name: str
    objects: Dict[str, List[str]] = field(default_factory=dict)  # type -> [object_names]
    init: InitialState = field(default_factory=InitialState)
    goal: GoalCondition = field(default_factory=GoalCondition)


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
            pattern = r'(?:;\s*([^\n]*)\n\s*)?\(([\w-]+)([^)]*)\)(?:\s*;\s*([^\n]*))?'
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
        action_blocks = re.split(r'(?=;\s*[A-Za-z].*\n\s*\(:durative-action)', content)
        
        for block in action_blocks:
            # Pattern to find durative-action with preceding comment
            action_pattern = r';\s*([^\n]+)\n\s*\(:durative-action\s+([\w-]+)(.*)'
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
            pattern = r'\((over all|at start|at end)\s*\(([\w-]+)([^)]*)\)\)(?:\s*;\s*([^\n]*))?'
            
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
            pattern = r'\((at start|at end)\s*\((not\s*)?\(([\w-]+)([^)]*)\)\)\)'
            
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

    # ==================== Problem Parsing ====================

    def parse_problem_file(self, filepath: str) -> Problem:
        """Parse a PDDL problem file and return a Problem object."""
        with open(filepath, 'r') as f:
            content = f.read()
        return self.parse_problem_string(content)

    def parse_problem_string(self, content: str) -> Problem:
        """Parse PDDL problem content from a string."""
        # Extract problem name
        problem_name = self._extract_problem_name(content)

        # Extract domain reference
        domain_name = self._extract_problem_domain(content)

        # Extract objects
        objects = self._extract_objects(content)

        # Extract initial state
        init = self._extract_init(content)

        # Extract goal conditions
        goal = self._extract_goal(content)

        return Problem(
            name=problem_name,
            domain_name=domain_name,
            objects=objects,
            init=init,
            goal=goal
        )

    def _extract_problem_name(self, content: str) -> str:
        """Extract the problem name from (define (problem NAME) ...)"""
        match = re.search(r'\(define\s*\(problem\s+(\S+)\)', content)
        return match.group(1) if match else "unknown"

    def _extract_problem_domain(self, content: str) -> str:
        """Extract the domain reference from (:domain NAME)"""
        match = re.search(r'\(:domain\s+(\S+)\)', content)
        return match.group(1) if match else "unknown"

    def _extract_objects(self, content: str) -> Dict[str, List[str]]:
        """Extract objects from (:objects ...) section."""
        objects = {}
        match = re.search(r'\(:objects\s*(.*?)\)', content, re.DOTALL)
        if match:
            objects_content = match.group(1)
            # Parse lines like: t1 t2 - truck
            for line in objects_content.split('\n'):
                line = line.strip()
                if ' - ' in line:
                    parts = line.split(' - ')
                    obj_type = parts[-1].strip()
                    obj_names = parts[0].strip().split()

                    if obj_type not in objects:
                        objects[obj_type] = []
                    objects[obj_type].extend([n for n in obj_names if n])
        return objects

    def _extract_init(self, content: str) -> InitialState:
        """Extract initial state from (:init ...) section."""
        predicates = []
        functions = []
        timed_literals = []

        # Find the :init block - handle both cases (with and without :goal after)
        match = re.search(r'\(:init\s*(.*?)\)\s*(?=\(:goal|\(:metric|$)', content, re.DOTALL)
        if match:
            init_content = match.group(1)

            # Parse timed initial literals first: (at 22 (not (can_deliver m)))
            til_pattern = r'\(at\s+([\d.]+)\s+\((not\s+)?\((\w+)([^)]*)\)\)\)'
            for m in re.finditer(til_pattern, init_content):
                time = float(m.group(1))
                negated = m.group(2) is not None
                pred_name = m.group(3)
                args = m.group(4).strip().split()

                timed_literals.append(TimedLiteral(
                    time=time,
                    predicate=GroundPredicate(
                        name=pred_name,
                        arguments=args,
                        negated=negated
                    )
                ))

            # Parse function assignments: (= (time_to_drive a b) 20)
            func_pattern = r'\(=\s*\((\w+)([^)]*)\)\s*([\d.]+)\)'
            for m in re.finditer(func_pattern, init_content):
                func_name = m.group(1)
                args = m.group(2).strip().split()
                value = float(m.group(3))

                functions.append(FunctionValue(
                    name=func_name,
                    arguments=args,
                    value=value
                ))

            # Parse regular predicates: (at t1 a), (refrigerated t2)
            # Use a simpler approach - find all predicates and filter
            simple_pred_pattern = r'\((\w+)([^()]*)\)'
            for m in re.finditer(simple_pred_pattern, init_content):
                pred_name = m.group(1)
                args_str = m.group(2).strip()

                # Skip function assignments (=)
                if pred_name == '=':
                    continue
                # Skip 'not' wrapper
                if pred_name == 'not':
                    continue
                # Skip timed literals: (at NUMBER ...)
                if pred_name == 'at' and args_str and re.match(r'^[\d.]+\s', args_str):
                    continue
                # Skip inner predicates of function assignments
                if any(f.name == pred_name and f.arguments == args_str.split() for f in functions):
                    continue

                args = args_str.split() if args_str else []

                # Avoid duplicates from timed literals
                is_til_pred = any(
                    tl.predicate.name == pred_name and tl.predicate.arguments == args
                    for tl in timed_literals
                )
                if is_til_pred:
                    continue

                predicates.append(GroundPredicate(
                    name=pred_name,
                    arguments=args,
                    negated=False
                ))

        return InitialState(
            predicates=predicates,
            functions=functions,
            timed_literals=timed_literals
        )

    def _extract_goal(self, content: str) -> GoalCondition:
        """Extract goal conditions from (:goal ...) section."""
        goals = []
        metric = None

        # Find the :goal block - use balanced parentheses matching
        goal_start = content.find('(:goal')
        if goal_start != -1:
            # Find matching closing paren for (:goal ...)
            paren_count = 0
            goal_end = goal_start
            for i, char in enumerate(content[goal_start:], goal_start):
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        goal_end = i
                        break

            goal_block = content[goal_start:goal_end + 1]

            # Check if it's (and ...) or single predicate
            if '(and' in goal_block:
                # Extract content inside (and ...)
                and_start = goal_block.find('(and')
                # Find all predicates inside
                pred_pattern = r'\((\w+)\s+([^()]+)\)'
                for m in re.finditer(pred_pattern, goal_block[and_start:]):
                    pred_name = m.group(1)
                    if pred_name == 'and':
                        continue
                    args = m.group(2).strip().split() if m.group(2).strip() else []
                    goals.append(GroundPredicate(
                        name=pred_name,
                        arguments=args,
                        negated=False
                    ))
            else:
                # Single predicate goal
                match = re.search(r'\(:goal\s*\((\w+)\s+([^)]*)\)\)', goal_block)
                if match:
                    goals.append(GroundPredicate(
                        name=match.group(1),
                        arguments=match.group(2).strip().split(),
                        negated=False
                    ))

        # Extract metric if present
        metric_match = re.search(r'\(:metric\s+(minimize|maximize)\s+\(([^)]+)\)\)', content)
        if metric_match:
            metric = f"{metric_match.group(1)} ({metric_match.group(2)})"

        return GoalCondition(goals=goals, metric=metric)

    def get_all_type_names(self) -> List[str]:
        """Get all type names defined in the domain."""
        if self.domain:
            return list(self.domain.types.keys())
        return []


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

    # Test problem parsing
    test_problem = """
    (define (problem test_problem)
        (:domain test)
        (:objects
            t1 t2 - truck
            a b c - location
        )
        (:init
            (at t1 a)
            (at t2 b)
            (= (distance a b) 10)
            (at 20 (not (available t1)))
        )
        (:goal (and
            (at t1 c)
            (at t2 a)
        ))
        (:metric minimize (total-time))
    )
    """

    problem = parser.parse_problem_string(test_problem)
    print(f"\nProblem: {problem.name}")
    print(f"Domain: {problem.domain_name}")
    print(f"Objects: {problem.objects}")
    print(f"Initial predicates: {problem.init.predicates}")
    print(f"Initial functions: {problem.init.functions}")
    print(f"Timed literals: {problem.init.timed_literals}")
    print(f"Goals: {problem.goal.goals}")
    print(f"Metric: {problem.goal.metric}")