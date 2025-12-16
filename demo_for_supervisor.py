#!/usr/bin/env python3
"""
Supervisor Demo Script
======================

This script demonstrates the core verbalization logic:
    Input:  predicate-refrigeratedttruck
    Output: Natural language sentence

Run: python demo_for_supervisor.py
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.aiplan4eu_parser import create_domain_map
from src.prototype_verbalizer import PrototypeVerbalizer


def main():
    print("=" * 70)
    print("   PLANVERB - Natural Language Explanation Generator")
    print("   Supervisor Demo")
    print("=" * 70)
    
    # Step 1: Load the domain
    domain_file = os.path.join(os.path.dirname(__file__), 
                               "domains", "refrigerated_delivery_domain.pddl")
    
    print(f"\n📁 Loading domain: refrigerated_delivery_domain.pddl")
    domain_map = create_domain_map(domain_file)
    
    print(f"\n✅ Domain Map Created:")
    print(f"   • {len(domain_map.predicates)} predicates extracted")
    print(f"   • {len(domain_map.actions)} actions extracted")
    print(f"   • Comments successfully linked")
    
    # Step 2: Show the map
    print("\n" + "-" * 70)
    print("📋 EXTRACTED MAP:")
    print("-" * 70)
    
    print("\nPredicates with comments:")
    for name, pred in domain_map.predicates.items():
        comment = pred.comment if pred.comment else "(no comment)"
        print(f"   • {name}: \"{comment}\"")
    
    print("\nActions with comments:")
    for name, action in domain_map.actions.items():
        comment = action.comment if action.comment else "(no comment)"
        print(f"   • {name}: \"{comment}\"")
        if action.precondition_comments:
            for pred, pc in action.precondition_comments.items():
                print(f"      └─ precond '{pred}': \"{pc}\"")
    
    # Step 3: Demo the verbalization
    print("\n" + "=" * 70)
    print("🔄 VERBALIZATION DEMO")
    print("=" * 70)
    
    verbalizer = PrototypeVerbalizer(domain_map)
    
    # The exact examples from supervisor's requirements
    demo_cases = [
        ("predicate-refrigeratedttruck", 
         "Predicate 'refrigerated' with parameter ?t of type truck"),
        
        ("predicate-can_deliverpprod",
         "Predicate 'can_deliver' with parameter ?p of type prod"),
        
        ("predicate-boardedddriverttruck",
         "Predicate 'boarded' with parameters ?d:driver, ?t:truck"),
    ]
    
    for technical_input, description in demo_cases:
        print(f"\n{'─' * 70}")
        print(f"📥 TECHNICAL INPUT: {technical_input}")
        print(f"   ({description})")
        print()
        
        result = verbalizer.verbalize(technical_input)
        
        print(f"📤 NATURAL LANGUAGE OUTPUT:")
        print(f"   \"{result}\"")
    
    # Interactive mode
    print("\n" + "=" * 70)
    print("🎮 INTERACTIVE MODE")
    print("=" * 70)
    print("Enter a technical input (or 'quit' to exit):")
    print("Format: predicate-{name}{param}{type}")
    print("Examples: predicate-refrigeratedttruck, predicate-can_deliverpprod")
    print()
    
    while True:
        try:
            user_input = input(">>> ").strip()
            if user_input.lower() in ('quit', 'exit', 'q'):
                break
            if not user_input:
                continue
                
            result = verbalizer.verbalize(user_input)
            print(f"    → {result}\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"    Error: {e}\n")
    
    print("\nDemo complete! ✅")


if __name__ == "__main__":
    main()
