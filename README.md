# PlanVerb

Natural language generation for explainable AI planning. Takes the technical
output of a contrastive explanation system and turns it into plain English.

Final Year Project, BSc Artificial Intelligence, King's College London.
Author: Yat Long Chang (k23062413). Supervisor: Dr Amanda Coles.

## What it does

Input (from the XAIPFramework):

    predicate-refrigeratedttruck

Output:

    "If we did not require that Truck 1 is refrigerated
     in order to keep the meat fresh in Truck 1, then we could:"

It also compares two plans and summarises the differences:

    "The alternative plan is 10.0 time units shorter.
     Uses Truck 2 instead of Truck 1 (in 7 actions).
     Adds extend_meat_life."

## Setup

Python 3.9 or later. One optional dependency:

    pip install unified-planning

If your system complains about managed packages:

    pip install unified-planning --break-system-packages

Everything else is standard library.

## Quick start

Run the demo to check everything works:

    python main.py --demo

Try a single abstraction:

    python main.py -d domains/refrigerated_delivery_domain.pddl \
        -a "abstract predicate (refrigerated ?t - truck) from action extend_meat_life"

Get a domain summary:

    python main.py summary -d domains/rover.pddl

Compare two plans:

    python main.py diff -d domains/settlers.pddl \
        --plan1 "test_domains/Settlers/Original/example-plan.txt" \
        --plan2 "test_domains/Settlers/Constrained/example-plan-constrained.txt" \
        --concise

## Watch mode (XAIPFramework integration)

    python main.py watch -d domains/refrigerated_delivery_domain.pddl \
        --common-dir /path/to/shared/directory

Polls the shared directory for request files from the C++ GUI and writes
natural language responses back. Ctrl+C to stop.

## File layout

    main.py                     CLI entry point (demo, summary, diff, watch)
    src/
        pddl_parser.py          PDDL parsing with comment extraction
        aiplan4eu_parser.py     AIPlan4EU integration (optional)
        predicate_processor.py  predicate cataloguing
        nlg_generator.py        NLG engine (predicate/duration/TIL abstractions)
        domain_config.py        domain profiles for 5 domains
        plan_differ.py          plan comparison and diff verbalization
        xaip_integration.py     XAIPFramework file-based communication
        domain_summary.py       domain summary generator
        prototype_verbalizer.py early prototype, kept for reference
    domains/                    annotated PDDL domain files
        refrigerated_delivery_domain.pddl
        rover.pddl
        satellite.pddl
        settlers.pddl
        crewplanning.pddl
    test_domains/               plan files and abstraction test cases

## Supported domains

All five have annotated PDDL files and configuration profiles:

- Refrigeration -- truck logistics with perishable goods
- Rover -- Mars rover exploration
- Satellite -- observation scheduling
- Settlers -- colony building with carts and trains
- CrewPlanning -- astronaut daily scheduling

Adding a new domain means writing a profile in domain_config.py (or a JSON file)
and adding comments to the PDDL domain file. See the Refrigeration domain for
an example of how comments should be structured.

## How PDDL annotations work

Comments before actions describe what the action does:

    ; Driver ?d drives the truck ?t from ?l1 to ?l2
    (:durative-action drive_truck ...)

Inline comments on preconditions describe the condition:

    (over all (boarded ?d ?t))    ; ?d has boarded ?t

The system uses these comments to build natural language explanations.
When a domain profile is available, it uses the profile's cleaner templates
instead, avoiding the redundancy issues that come from naive substitution
into comments (e.g. "Driver Driver 1 drives the truck Truck 1").

## Three abstraction types

1. Predicate -- "If we did not require that X in order to Y..."
2. Duration -- "If it took 0 minutes to Y..."
3. Timed Initial Literal -- "If X did not become false at time T..."

## Testing

    python main.py --demo                          # full pipeline test
    python -m src.pddl_parser                      # parser only
    python -m src.nlg_generator                     # NLG only
    python -m src.plan_differ                       # plan diff only
