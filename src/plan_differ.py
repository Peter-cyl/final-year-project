"""
Plan Differencing Module
Compares two plans and generates natural language descriptions of the key differences.

This module addresses the project extension described in the specification:
identifying and highlighting where two plans differ in important ways to provide
succinct explanations, rather than presenting entire plans.

Usage:
    differ = PlanDiffer(nlg_generator)
    diff = differ.compare_plans(original_plan, alternative_plan)
    print(differ.verbalize_diff(diff))
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set


@dataclass
class PlanStep:
    """Represents a single step in a plan."""
    time: float
    action_name: str
    parameters: List[str]
    duration: float
    
    def signature(self) -> str:
        """Unique signature based on action name and parameters (ignoring timing)."""
        return f"{self.action_name}({','.join(self.parameters)})"
    
    def action_type(self) -> str:
        """Just the action name without parameters."""
        return self.action_name


@dataclass
class PlanDiff:
    """Represents the differences between two plans."""
    # Actions only in the original plan
    only_in_original: List[PlanStep] = field(default_factory=list)
    # Actions only in the alternative plan
    only_in_alternative: List[PlanStep] = field(default_factory=list)
    # Actions present in both but with different parameters
    parameter_changes: List[Tuple[PlanStep, PlanStep]] = field(default_factory=list)
    # Actions present in both but at different times
    timing_changes: List[Tuple[PlanStep, PlanStep]] = field(default_factory=list)
    # Actions identical in both plans
    shared: List[PlanStep] = field(default_factory=list)
    # Overall metrics
    original_cost: float = 0.0
    alternative_cost: float = 0.0
    original_length: int = 0
    alternative_length: int = 0


class PlanDiffer:
    """
    Compares two plans and generates natural language summaries of differences.
    
    The differencing algorithm works in three passes:
    1. Match actions by exact signature (action name + parameters)
    2. Match remaining actions by action name (detecting parameter changes)
    3. Report unmatched actions as unique to each plan
    """
    
    def __init__(self, nlg_generator=None):
        """
        Initialize with optional NLG generator for verbalization.
        
        Args:
            nlg_generator: NLGGenerator instance for action verbalization
        """
        self.nlg = nlg_generator
    
    def parse_plan_file(self, filepath: str) -> List[PlanStep]:
        """
        Parse a plan file into a list of PlanSteps.
        
        Handles the standard planner output format:
            0.001: (action_name param1 param2) [duration] ; optional comment
        
        Args:
            filepath: Path to the plan file
            
        Returns:
            List of PlanStep objects
        """
        steps = []
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(';'):
                    continue
                
                # Pattern: TIME: (ACTION PARAMS) [DURATION] ; optional
                match = re.match(
                    r'([\d.]+):\s*\(([\w-]+)([^)]*)\)\s*\[([\d.]+)\]',
                    line
                )
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
    
    def parse_plan_string(self, plan_text: str) -> List[PlanStep]:
        """
        Parse a plan from a string (same format as file).
        
        Args:
            plan_text: Plan text content
            
        Returns:
            List of PlanStep objects
        """
        steps = []
        for line in plan_text.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            
            match = re.match(
                r'([\d.]+):\s*\(([\w-]+)([^)]*)\)\s*\[([\d.]+)\]',
                line
            )
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
    
    def compare_plans(self, original: List[PlanStep],
                      alternative: List[PlanStep]) -> PlanDiff:
        """
        Compare two plans and identify differences.
        
        Uses a three-pass matching algorithm:
        Pass 1: Match by exact signature (action + params)
        Pass 2: Match remaining by action name (detect param changes)
        Pass 3: Report unmatched as unique
        
        Args:
            original: Steps from the original plan
            alternative: Steps from the alternative plan
            
        Returns:
            PlanDiff object describing the differences
        """
        diff = PlanDiff()
        diff.original_length = len(original)
        diff.alternative_length = len(alternative)
        
        # Calculate total costs (sum of last action time + duration)
        if original:
            last = max(original, key=lambda s: s.time + s.duration)
            diff.original_cost = last.time + last.duration
        if alternative:
            last = max(alternative, key=lambda s: s.time + s.duration)
            diff.alternative_cost = last.time + last.duration
        
        # Track which steps have been matched
        orig_matched = set()
        alt_matched = set()
        
        # Pass 1: Exact signature match
        for i, orig_step in enumerate(original):
            for j, alt_step in enumerate(alternative):
                if j in alt_matched:
                    continue
                if orig_step.signature() == alt_step.signature():
                    # Same action and params — check timing
                    if abs(orig_step.time - alt_step.time) > 0.01:
                        diff.timing_changes.append((orig_step, alt_step))
                    else:
                        diff.shared.append(orig_step)
                    orig_matched.add(i)
                    alt_matched.add(j)
                    break
        
        # Pass 2: Match by action name (parameter changes)
        for i, orig_step in enumerate(original):
            if i in orig_matched:
                continue
            for j, alt_step in enumerate(alternative):
                if j in alt_matched:
                    continue
                if orig_step.action_name == alt_step.action_name:
                    diff.parameter_changes.append((orig_step, alt_step))
                    orig_matched.add(i)
                    alt_matched.add(j)
                    break
        
        # Pass 3: Unmatched steps
        for i, step in enumerate(original):
            if i not in orig_matched:
                diff.only_in_original.append(step)
        
        for j, step in enumerate(alternative):
            if j not in alt_matched:
                diff.only_in_alternative.append(step)
        
        return diff
    
    def verbalize_diff(self, diff: PlanDiff,
                       domain_name: str = "") -> str:
        """
        Generate a natural language summary of plan differences.
        
        Produces a concise, selective summary focusing on the most
        important differences, following Miller's (2019) insight that
        explanations should be selective rather than exhaustive.
        
        Args:
            diff: PlanDiff object from compare_plans
            domain_name: Optional domain name for context
            
        Returns:
            Natural language description of differences
        """
        sections = []
        
        # Overall comparison
        cost_diff = diff.alternative_cost - diff.original_cost
        if abs(cost_diff) > 0.01:
            if cost_diff > 0:
                sections.append(
                    f"The alternative plan takes {diff.alternative_cost:.2f} time units "
                    f"compared to {diff.original_cost:.2f} for the original plan "
                    f"({cost_diff:.2f} longer)."
                )
            else:
                sections.append(
                    f"The alternative plan takes {diff.alternative_cost:.2f} time units "
                    f"compared to {diff.original_cost:.2f} for the original plan "
                    f"({abs(cost_diff):.2f} shorter)."
                )
        
        step_diff = diff.alternative_length - diff.original_length
        if step_diff != 0:
            more_fewer = "more" if step_diff > 0 else "fewer"
            sections.append(
                f"The alternative plan has {diff.alternative_length} steps "
                f"compared to {diff.original_length} ({abs(step_diff)} {more_fewer})."
            )
        
        # Actions only in original
        if diff.only_in_original:
            removed = self._group_actions(diff.only_in_original)
            desc_parts = []
            for action_name, steps in removed.items():
                if len(steps) == 1:
                    desc_parts.append(self._verbalize_step(steps[0]))
                else:
                    desc_parts.append(
                        f"{len(steps)} instances of {self._verbalize_action_name(action_name)}"
                    )
            sections.append(
                "The original plan includes the following actions that the "
                "alternative plan does not: " + "; ".join(desc_parts) + "."
            )
        
        # Actions only in alternative
        if diff.only_in_alternative:
            added = self._group_actions(diff.only_in_alternative)
            desc_parts = []
            for action_name, steps in added.items():
                if len(steps) == 1:
                    desc_parts.append(self._verbalize_step(steps[0]))
                else:
                    desc_parts.append(
                        f"{len(steps)} instances of {self._verbalize_action_name(action_name)}"
                    )
            sections.append(
                "The alternative plan includes the following actions that the "
                "original plan does not: " + "; ".join(desc_parts) + "."
            )
        
        # Parameter changes (most interesting for explanation)
        if diff.parameter_changes:
            change_parts = []
            for orig, alt in diff.parameter_changes:
                # Find which parameters differ
                changed_params = []
                for k in range(min(len(orig.parameters), len(alt.parameters))):
                    if orig.parameters[k] != alt.parameters[k]:
                        changed_params.append(
                            (orig.parameters[k], alt.parameters[k])
                        )
                
                if changed_params:
                    orig_desc = self._verbalize_step(orig)
                    alt_desc = self._verbalize_step(alt)
                    change_parts.append(
                        f"Instead of \"{orig_desc}\", the alternative plan uses "
                        f"\"{alt_desc}\""
                    )
            
            if change_parts:
                sections.append(
                    "Key differences in how actions are performed: " +
                    ". ".join(change_parts) + "."
                )
        
        # Timing changes (summarise rather than list all)
        if diff.timing_changes:
            sections.append(
                f"{len(diff.timing_changes)} action(s) occur at different times "
                f"in the two plans due to the changes above."
            )
        
        # Shared actions summary
        if diff.shared:
            sections.append(
                f"{len(diff.shared)} action(s) are identical in both plans."
            )
        
        if not sections:
            return "The two plans are identical."
        
        return "\n\n".join(sections)
    
    def verbalize_diff_concise(self, diff: PlanDiff) -> str:
        """
        Generate a very concise (1-3 sentence) summary of differences.
        Suitable for display in the GUI alongside the abstraction explanation.
        
        Args:
            diff: PlanDiff object
            
        Returns:
            Short natural language summary
        """
        parts = []
        
        # Cost difference
        cost_diff = diff.alternative_cost - diff.original_cost
        if abs(cost_diff) > 0.01:
            if cost_diff > 0:
                parts.append(f"The alternative plan is {cost_diff:.1f} time units longer")
            else:
                parts.append(f"The alternative plan is {abs(cost_diff):.1f} time units shorter")
        
        # Key structural differences — deduplicate parameter changes
        if diff.parameter_changes:
            all_changes = {}  # from_val -> to_val
            for orig, alt in diff.parameter_changes:
                for k in range(min(len(orig.parameters), len(alt.parameters))):
                    if orig.parameters[k] != alt.parameters[k]:
                        key = (orig.parameters[k], alt.parameters[k])
                        all_changes[key] = all_changes.get(key, 0) + 1
            
            for (from_val, to_val), count in all_changes.items():
                # Use readable names if NLG generator is available
                from_readable = self.nlg._get_readable_value(from_val) if self.nlg else from_val
                to_readable = self.nlg._get_readable_value(to_val) if self.nlg else to_val
                if count > 1:
                    parts.append(f"uses {to_readable} instead of {from_readable} (in {count} actions)")
                else:
                    parts.append(f"uses {to_readable} instead of {from_readable}")
        
        if diff.only_in_alternative:
            names = set(s.action_name for s in diff.only_in_alternative)
            parts.append(f"adds {', '.join(names)}")
        
        if diff.only_in_original:
            names = set(s.action_name for s in diff.only_in_original)
            parts.append(f"removes {', '.join(names)}")
        
        if not parts:
            return "The two plans are identical."
        
        # Capitalize first letter of each part
        parts = [p[0].upper() + p[1:] for p in parts]
        return ". ".join(parts) + "."
    
    def _verbalize_step(self, step: PlanStep) -> str:
        """Verbalize a single plan step."""
        if self.nlg:
            return self.nlg.verbalize_action(step.action_name, step.parameters)
        # Fallback: readable format
        readable_params = " ".join(step.parameters)
        action_readable = step.action_name.replace("_", " ").replace("-", " ")
        return f"{action_readable} {readable_params}"
    
    def _verbalize_action_name(self, action_name: str) -> str:
        """Make an action name readable."""
        return action_name.replace("_", " ").replace("-", " ")
    
    def _group_actions(self, steps: List[PlanStep]) -> Dict[str, List[PlanStep]]:
        """Group steps by action name."""
        groups = {}
        for step in steps:
            if step.action_name not in groups:
                groups[step.action_name] = []
            groups[step.action_name].append(step)
        return groups


def compare_plan_files(original_path: str, alternative_path: str,
                       nlg_generator=None, concise: bool = False) -> str:
    """
    Convenience function to compare two plan files and produce a summary.
    
    Args:
        original_path: Path to original plan file
        alternative_path: Path to alternative plan file
        nlg_generator: Optional NLG generator for better verbalization
        concise: If True, produce a short summary
        
    Returns:
        Natural language diff summary
    """
    differ = PlanDiffer(nlg_generator)
    original = differ.parse_plan_file(original_path)
    alternative = differ.parse_plan_file(alternative_path)
    diff = differ.compare_plans(original, alternative)
    
    if concise:
        return differ.verbalize_diff_concise(diff)
    return differ.verbalize_diff(diff)


# Test
if __name__ == "__main__":
    import sys
    
    # Test with inline plan data
    plan_a_text = """
0.001: (load_truck ce t1 a) [0.010]
0.001: (load_truck m t1 a) [0.010]
0.001: (board_truck d1 t1 a) [0.010]
0.011: (drive_truck d1 t1 a b) [20.000]
20.011: (deliver_produce m t1 b) [0.010]
20.021: (drive_truck d1 t1 b c) [15.000]
35.021: (deliver_produce ce t1 c) [0.010]
"""
    
    plan_b_text = """
0.001: (board_truck d1 t2 a) [0.010]
0.001: (load_truck ce t2 a) [0.010]
0.001: (load_truck m t2 a) [0.010]
0.011: (drive_truck d1 t2 a c) [10.000]
10.011: (deliver_produce ce t2 c) [0.010]
10.021: (drive_truck d1 t2 c b) [15.000]
21.991: (extend_meat_life m t2) [0.010]
25.021: (deliver_produce m t2 b) [0.010]
"""
    
    differ = PlanDiffer()
    plan_a = differ.parse_plan_string(plan_a_text)
    plan_b = differ.parse_plan_string(plan_b_text)
    
    print("Parsed plan A:", len(plan_a), "steps")
    print("Parsed plan B:", len(plan_b), "steps")
    
    diff = differ.compare_plans(plan_a, plan_b)
    
    print("\n" + "=" * 60)
    print("FULL DIFF:")
    print("=" * 60)
    print(differ.verbalize_diff(diff))
    
    print("\n" + "=" * 60)
    print("CONCISE DIFF:")
    print("=" * 60)
    print(differ.verbalize_diff_concise(diff))