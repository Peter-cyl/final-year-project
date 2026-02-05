"""
PlanVerb NLG - Natural Language Generation for AI Planning Explanations

This package provides tools for converting PDDL planning abstractions
into human-readable natural language explanations.

Components:
- pddl_parser: Parse PDDL domain and problem files
- nlg_generator: Generate natural language explanations
- domain_config: Multi-domain configuration system
- predicate_processor: Predicate catalog and verbalization
- domain_summary: Domain summary generation
- xaip_integration: XAIPFramework integration layer
"""

# Parser components
from .pddl_parser import (
    PDDLParser,
    Domain,
    Action,
    Predicate,
    Parameter,
    Problem,
    InitialState,
    GoalCondition,
    GroundPredicate,
    TimedLiteral,
    FunctionValue
)

# NLG components
from .nlg_generator import (
    NLGGenerator,
    Abstraction,
    PlanStep,
    parse_plan_file
)

# Domain configuration
from .domain_config import (
    DomainProfile,
    DomainConfigManager
)

# Predicate processing
from .predicate_processor import (
    PredicateCatalog,
    PredicateEntry,
    PredicateProcessor
)

# Domain summary
from .domain_summary import (
    DomainSummaryGenerator,
    DomainSummary,
    ActionSummary
)

# XAIPFramework integration
from .xaip_integration import (
    XAIPIntegration,
    IntegrationConfig,
    FrameworkOutput
)

__all__ = [
    # Parser
    'PDDLParser',
    'Domain',
    'Action',
    'Predicate',
    'Parameter',
    'Problem',
    'InitialState',
    'GoalCondition',
    'GroundPredicate',
    'TimedLiteral',
    'FunctionValue',
    # NLG
    'NLGGenerator',
    'Abstraction',
    'PlanStep',
    'parse_plan_file',
    # Configuration
    'DomainProfile',
    'DomainConfigManager',
    # Predicate Processing
    'PredicateCatalog',
    'PredicateEntry',
    'PredicateProcessor',
    # Domain Summary
    'DomainSummaryGenerator',
    'DomainSummary',
    'ActionSummary',
    # Framework Integration
    'XAIPIntegration',
    'IntegrationConfig',
    'FrameworkOutput',
]

__version__ = '1.0.0'
