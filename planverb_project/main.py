#!/usr/bin/env python3
"""
PlanVerb Natural Language Generator
Main entry point for generating natural language explanations from AI planning abstractions.

Usage:
    python main.py --domain <domain.pddl> --abstraction <abstraction_spec>
    
Example:
    python main.py --domain domains/refrigerated_delivery_domain.pddl \
                   --abstraction "abstract predicate (refrigerated ?t - truck) from action extend_meat_life"
"""

import argparse
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pddl_parser import PDDLParser
from src.nlg_generator import NLGGenerator, PlanStep, parse_plan_file


def demo_refrigeration_domain():
    """
    Demonstrate the NLG system with the refrigeration domain.
    Shows several example abstractions and their natural language explanations.
    """
    print("=" * 70)
    print("PlanVerb NLG Demo - Refrigeration Domain")
    print("=" * 70)
    
    # Parse the domain
    domain_path = os.path.join(os.path.dirname(__file__), 
                               "domains/refrigerated_delivery_domain.pddl")
    
    print(f"\n1. Parsing domain: {domain_path}")
    parser = PDDLParser()
    
    try:
        domain = parser.parse_file(domain_path)
        print(f"   ✓ Domain '{domain.name}' parsed successfully")
        print(f"   ✓ Found {len(domain.actions)} actions")
        print(f"   ✓ Found {len(domain.predicates)} predicates")
    except FileNotFoundError:
        print(f"   ✗ Domain file not found. Using embedded example.")
        # Use embedded domain for demo
        domain = parser.parse_string(EXAMPLE_DOMAIN)
    
    # Show parsed actions
    print("\n2. Parsed Actions with Comments:")
    print("-" * 50)
    for action in domain.actions:
        print(f"   • {action.name}")
        print(f"     Comment: \"{action.comment}\"")
        print(f"     Parameters: {[(p.name, p.type) for p in action.parameters]}")
        print(f"     Preconditions: {len(action.preconditions)}")
        for pc in action.preconditions:
            if pc.comment:
                print(f"       - {pc.name}: \"{pc.comment}\"")
        print()
    
    # Create NLG generator
    nlg = NLGGenerator(parser)
    
    # Demo different abstractions
    print("\n3. Example Explanations:")
    print("=" * 70)
    
    # Example 1: Refrigerated predicate abstraction
    print("\n--- Example 1: Predicate Abstraction (refrigerated) ---")
    abstraction1 = nlg.parse_abstraction(
        "abstract predicate (refrigerated ?t - truck) from action extend_meat_life"
    )
    explanation1 = nlg.generate_explanation(
        abstraction1,
        parameter_bindings={"?t": "t1", "?m": "m"}
    )
    print(explanation1)
    
    # Example 2: can_deliver predicate abstraction  
    print("\n--- Example 2: Predicate Abstraction (can_deliver) ---")
    abstraction2 = nlg.parse_abstraction(
        "abstract predicate (can_deliver ?p - prod) from action deliver_produce"
    )
    explanation2 = nlg.generate_explanation(
        abstraction2,
        parameter_bindings={"?p": "m", "?t": "t1", "?l": "b"}
    )
    print(explanation2)
    
    # Example 3: boarded predicate abstraction
    print("\n--- Example 3: Predicate Abstraction (boarded) ---")
    abstraction3 = nlg.parse_abstraction(
        "abstract predicate (boarded ?d - driver ?t - truck) from action drive_truck"
    )
    explanation3 = nlg.generate_explanation(
        abstraction3,
        parameter_bindings={"?d": "d1", "?t": "t1", "?l1": "a", "?l2": "b"}
    )
    print(explanation3)
    
    # Example 4: With a hypothetical plan
    print("\n--- Example 4: Full Explanation with Plan ---")
    example_plan = [
        PlanStep(0.00, "load_truck", ["ce", "t1", "a"], 0.01),
        PlanStep(0.00, "load_truck", ["m", "t1", "a"], 0.01),
        PlanStep(0.00, "board_truck", ["d1", "t1", "a"], 0.01),
        PlanStep(0.01, "drive_truck", ["d1", "t1", "a", "c"], 10.0),
        PlanStep(10.01, "deliver_produce", ["ce", "t1", "c"], 0.01),
        PlanStep(10.02, "drive_truck", ["d1", "t1", "c", "b"], 15.0),
        PlanStep(25.02, "deliver_produce", ["m", "t1", "b"], 0.01),
    ]
    
    explanation4 = nlg.generate_explanation(
        abstraction1,
        parameter_bindings={"?t": "t1", "?m": "m"},
        new_plan=example_plan
    )
    print(explanation4)
    
    # Demo action verbalization
    print("\n\n4. Action Verbalization Demo:")
    print("-" * 50)
    
    test_actions = [
        ("drive_truck", ["d1", "t1", "a", "b"]),
        ("load_truck", ["m", "t1", "a"]),
        ("deliver_produce", ["ce", "t1", "c"]),
        ("board_truck", ["d1", "t2", "a"]),
    ]
    
    for action_name, params in test_actions:
        verbalized = nlg.verbalize_action(action_name, params)
        print(f"   {action_name}({', '.join(params)})")
        print(f"   → \"{verbalized}\"")
        print()


# Embedded example domain for testing without file
EXAMPLE_DOMAIN = """
(define (domain refrigerated_delivery)
  (:requirements :typing :durative-actions :fluents :timed-initial-literals) 
  (:types 
    prod driver truck - locatable
    meat cereal - prod
    location
  )
  (:predicates 
    (at ?l1 - locatable ?l2 - location)
    (in ?p - prod ?t - truck)
    (boarded ?d - driver ?t - truck)
    (refrigerated ?t - truck)
    (can_deliver ?p - prod)
  )

  (:functions
    (time_to_drive ?loc ?loc1 - location)
  )

  ; Load the produce ?prod into the truck ?truck at location ?loc
  (:durative-action load_truck
    :parameters (?prod - prod ?truck - truck ?loc - location)
    :duration (= ?duration 0.01)
    :condition (and 
                  (over all (at ?truck ?loc))
                  (at start (at ?prod ?loc))
                )
    :effect (and 
              (at start (not (at ?prod ?loc))) 
              (at end (in ?prod ?truck))
            )
  )

  ; Driver ?d boards the truck ?t at location ?l1
  (:durative-action board_truck
    :parameters (?d - driver ?t - truck ?l1 - location)
    :duration (= ?duration 0.01)
    :condition (and
                  (over all (at ?t ?l1))
                  (at start (at ?d ?l1))
               )
    :effect (and
              (at start (not (at ?d ?l1)))
              (at end (boarded ?d ?t))
            )
  )

  ; Driver ?d drives the truck ?t from location ?l1 to location ?l2
  (:durative-action drive_truck
    :parameters (?d - driver ?t - truck ?l1 ?l2 - location)
    :duration (= ?duration (time_to_drive ?l1 ?l2))
    :condition (and
                  (over all (boarded ?d ?t))
                  (at start (at ?t ?l1))
               )
    :effect (and
              (at start (not (at ?t ?l1)))
              (at end (at ?t ?l2))
            )
  )
  
  ; Extend the life of the meat ?m that is in the truck ?t
  (:durative-action extend_meat_life
    :parameters (?m - meat ?t - truck)
    :duration (= ?duration 0.01)
    :condition (and
                (over all (in ?m ?t))
                (over all (refrigerated ?t))
              )
    :effect (and
              (at end (can_deliver ?m))
            )
  )

  ; Deliver the produce ?p from truck ?t to location ?l
  (:durative-action deliver_produce
    :parameters (?p - prod ?t - truck ?l - location)
    :duration (= ?duration 0.01)
    :condition (and
                  (over all (at ?t ?l))
                  (over all (can_deliver ?p))
                  (at start (in ?p ?t))
               )
    :effect (and
              (at start (not (in ?p ?t)))
              (at end (at ?p ?l))
            )
  )
)
"""


def main():
    """Main entry point."""
    arg_parser = argparse.ArgumentParser(
        description="Generate natural language explanations for AI planning abstractions"
    )
    arg_parser.add_argument(
        "--domain", "-d",
        help="Path to PDDL domain file"
    )
    arg_parser.add_argument(
        "--abstraction", "-a", 
        help="Abstraction specification string"
    )
    arg_parser.add_argument(
        "--plan", "-p",
        help="Path to plan file (optional)"
    )
    arg_parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo with refrigeration domain"
    )
    
    args = arg_parser.parse_args()
    
    if args.demo or (not args.domain and not args.abstraction):
        demo_refrigeration_domain()
        return
    
    if not args.domain or not args.abstraction:
        print("Error: Both --domain and --abstraction are required")
        print("Or use --demo to see example output")
        arg_parser.print_help()
        sys.exit(1)
    
    # Parse domain
    parser = PDDLParser()
    domain = parser.parse_file(args.domain)
    print(f"Parsed domain: {domain.name}")
    
    # Create generator
    nlg = NLGGenerator(parser)
    
    # Parse abstraction
    abstraction = nlg.parse_abstraction(args.abstraction)
    
    # Parse plan if provided
    plan = None
    if args.plan:
        plan = parse_plan_file(args.plan)
    
    # Generate explanation
    explanation = nlg.generate_explanation(abstraction, new_plan=plan)
    
    print("\n" + "=" * 50)
    print("Generated Explanation:")
    print("=" * 50)
    print(explanation)


if __name__ == "__main__":
    main()
