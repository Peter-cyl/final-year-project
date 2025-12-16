# PlanVerb NLG - Natural Language Explanations for AI Planning

This project generates human-readable explanations from AI planning abstractions.

## 🎯 Project Goal

Transform technical planning output like:
```
abstract predicate (refrigerated ?t - truck) from action extend_meat_life
```

Into natural language:
```
If we did not require that truck T1 is refrigerated in order to extend 
the life of the meat that is in the truck, then we could:

0.00: Driver D1 boards truck T1 at Depot (takes 0.01 minutes)
0.01: Driver D1 drives truck T1 from Depot to Grocer (takes 10.0 minutes)
...
```

---

## 📁 Project Structure

```
planverb_project/
├── main.py                 # Main entry point & demo
├── requirements.txt        # Python dependencies
├── domains/               
│   └── refrigerated_delivery_domain.pddl   # Annotated example domain
├── src/
│   ├── __init__.py
│   ├── pddl_parser.py      # PDDL parser with comment extraction
│   └── nlg_generator.py    # Natural language generator
├── tests/                  # Your test files go here
└── output/                 # Generated outputs go here
```

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Demo

```bash
python main.py --demo
```

### 3. Use with Your Own Domain

```bash
python main.py \
    --domain domains/your_domain.pddl \
    --abstraction "abstract predicate (your_pred ?x - type) from action your_action"
```

---

## 📝 How to Annotate PDDL Domains

The key to good explanations is adding comments to your PDDL files.

### Action-Level Comments

Add a comment line BEFORE each action:

```lisp
; Driver ?d drives the truck ?t from location ?l1 to location ?l2
(:durative-action drive_truck
  :parameters (?d - driver ?t - truck ?l1 ?l2 - location)
  ...
)
```

### Precondition Comments

Add inline comments after preconditions:

```lisp
:condition (and
    (over all (boarded ?d ?t))    ; ?d has boarded ?t
    (at start (at ?t ?l1))        ; ?t is at ?l1
)
```

### Predicate Comments

Add inline comments in the predicates section:

```lisp
(:predicates
    (at ?l1 - locatable ?l2 - location)  ; ?l1 is at location ?l2
    (refrigerated ?t - truck)             ; ?t is refrigerated
)
```

---

## 🔧 Key Components

### 1. PDDLParser (`src/pddl_parser.py`)

Parses PDDL domain files and extracts:
- Domain name and types
- Predicates with comments
- Actions with parameters, preconditions, effects, and comments

```python
from src.pddl_parser import PDDLParser

parser = PDDLParser()
domain = parser.parse_file("domains/refrigerated_delivery_domain.pddl")

# Access parsed data
for action in domain.actions:
    print(f"Action: {action.name}")
    print(f"Comment: {action.comment}")
```

### 2. NLGGenerator (`src/nlg_generator.py`)

Generates natural language from abstractions:

```python
from src.nlg_generator import NLGGenerator

nlg = NLGGenerator(parser)

# Parse abstraction specification
abstraction = nlg.parse_abstraction(
    "abstract predicate (refrigerated ?t - truck) from action extend_meat_life"
)

# Generate explanation
explanation = nlg.generate_explanation(
    abstraction,
    parameter_bindings={"?t": "t1", "?m": "m"}
)
print(explanation)
```

---

## 📊 Abstraction Types Supported

| Type | Format | Example |
|------|--------|---------|
| Predicate | `abstract predicate (PRED ?params) from action ACTION` | `abstract predicate (refrigerated ?t - truck) from action extend_meat_life` |
| Duration | `abstract duration from action ACTION` | `abstract duration from action drive_truck` |
| TIL | (Coming soon) | Timed Initial Literals |

---

## 🎯 TODO / Extensions

### Required Tasks
- [ ] Add comments to more domains (Rovers, Settlers, etc.)
- [ ] Handle all abstraction types from XAIPFramework
- [ ] Improve parameter substitution for natural text
- [ ] Parse plan files from XAIPFramework

### Optional Extensions  
- [ ] Plan visualization (highlight differences)
- [ ] Explanation ranking (which is best?)
- [ ] Integration with AIPlan4EU unified-planning library
- [ ] Web interface for explanations

---

## 🧪 Testing

Run the demo to verify everything works:

```bash
python main.py --demo
```

Expected output should show:
1. ✓ Domain parsed successfully
2. ✓ All 5 actions found
3. ✓ Natural language explanations generated

---

## 📚 Key Concepts

### What is an "Abstraction"?

When a planning problem is unsolvable with a constraint (e.g., "use truck2"), 
the system removes preconditions to find what's blocking it.

**Example:** 
- Original: `extend_meat_life` requires `(refrigerated ?t)` 
- If truck1 isn't refrigerated, plan fails
- Abstraction: Remove `(refrigerated ?t)` precondition
- Result: Plan now works with truck1
- **Explanation:** "If the truck didn't need to be refrigerated..."

### What is "Verbalization"?

Converting technical plan syntax into readable sentences:

**Before:** `(drive_truck d1 t1 a b)`

**After:** "Driver D1 drives truck T1 from Depot to Butcher"

---

## 🔗 Integration with XAIPFramework

The XAIPFramework generates abstraction specifications in its output.
Your job is to:

1. Parse those specifications
2. Match them to annotated PDDL domains
3. Generate natural language explanations

The framework outputs are typically in the `common/` folder after running.

---

## 📖 References

1. PlanVerb paper (Canal et al., 2022) - Inspiration for verbalization
2. Contrastive Explanations paper (Krarup et al., 2021) - Theory behind abstractions
3. AIPlan4EU unified-planning - Alternative PDDL parsing library

---

## ❓ Need Help?

1. Check the demo output: `python main.py --demo`
2. Look at the annotated domain file for comment format
3. Add print statements in the parser to debug
4. Check that comment format matches expected patterns

Good luck with your project! 🚀
