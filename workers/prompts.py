"""
Prompt templates for the automated interview preparation platform.

This module contains prompt definitions only.
It intentionally does not contain LLM clients, API wrappers, or
prompt-execution logic.
"""


# ---------------------------------------------------------------------------
# Evaluation Prompts
# ---------------------------------------------------------------------------

QUALITY_EVALUATION_PROMPT = (
    "You are an expert technical interviewer. Evaluate this candidate answer. "
    "Return a JSON object with keys: overall_quality_score (0-100), "
    "relevance (0-1), completeness (0-1), clarity (0-1), feedback (string)."
)

TECHNICAL_ACCURACY_PROMPT = (
    "You are a technical interviewer evaluating a candidate's answer. "
    "Return a JSON object with keys: accuracy_score (0-100), "
    "correct_concepts_count (int), incorrect_concepts_count (int), "
    "knowledge_gaps (list of strings)."
)

COMMUNICATION_EVALUATION_PROMPT = (
    "Evaluate the candidate's communication quality. "
    "Return a JSON object with keys: clarity_score (0-100), "
    "professionalism (0-100), confidence_level (0-1), "
    "pace_appropriateness (0-1)."
)


# ---------------------------------------------------------------------------
# Junior System Design Prompt Templates
# ---------------------------------------------------------------------------

JUNIOR_SYSTEM_DESIGN_SCALABILITY_PROMPT = (
    "Generate one junior-level system-design interview question focused "
    "on foundational scalability. The question should ask the candidate "
    "to reason about a simple application starting with a single server "
    "and explain when and why it should move toward a multi-tier or "
    "multi-server architecture. Include basic load balancing and "
    "horizontal scaling considerations. Keep the expected architecture "
    "simple and avoid advanced distributed-system concepts."
)

JUNIOR_SYSTEM_DESIGN_DATA_PROMPT = (
    "Generate one junior-level system-design interview question focused "
    "on basic data-storage decisions. The scenario should require the "
    "candidate to choose between a relational database and a NoSQL "
    "database and explain the reasoning behind the choice. The question "
    "may also involve a basic caching layer using Redis or Memcached. "
    "Keep the scale and requirements realistic for a junior engineer "
    "and avoid advanced consistency models, distributed transactions, "
    "or multi-region database architectures."
)

JUNIOR_SYSTEM_DESIGN_API_PROMPT = (
    "Generate one junior-level system-design interview question focused "
    "on designing and protecting a simple API. The question should test "
    "fundamental API rate limiting, basic load balancing, caching, and "
    "request-handling concepts. The candidate should explain where these "
    "components fit in the architecture and what problems they solve. "
    "Keep the problem bounded and avoid advanced event-driven systems, "
    "distributed transactions, multi-region replication, or complex "
    "failure-handling strategies."
)


# ---------------------------------------------------------------------------
# Senior System Design Prompt Templates
# ---------------------------------------------------------------------------

SENIOR_SYSTEM_DESIGN_DISTRIBUTED_PROMPT = (
    "Generate one senior-level system-design interview question involving "
    "a large-scale distributed system. The question must require the "
    "candidate to analyze architectural trade-offs involving throughput, "
    "latency, availability, consistency, and partition tolerance. Include "
    "a scenario where CAP theorem considerations and failure-domain "
    "isolation matter. The candidate should justify trade-offs rather "
    "than simply name technologies."
)

SENIOR_SYSTEM_DESIGN_MULTIREGION_PROMPT = (
    "Generate one senior-level system-design interview question involving "
    "a globally distributed, multi-region system. Require the candidate "
    "to reason about cross-region replication, consistency models, "
    "regional failures, asynchronous processing, event-driven "
    "backpressure, and recovery behavior. Include competing latency, "
    "availability, correctness, and operational-cost requirements. "
    "The question should require the candidate to clarify ambiguous "
    "business requirements before finalizing the architecture."
)

SENIOR_SYSTEM_DESIGN_TRANSACTIONS_PROMPT = (
    "Generate one senior-level system-design interview question involving "
    "multiple services that must coordinate state changes reliably at "
    "large scale. Require discussion of distributed transactions, "
    "idempotency, retries, partial failures, consistency guarantees, "
    "failure-domain isolation, and asynchronous event processing. "
    "Introduce ambiguous or competing business constraints such as "
    "cost versus latency or consistency versus availability. The "
    "candidate should identify assumptions, discuss alternatives, and "
    "justify the final architecture based on explicit trade-offs."
)


# ---------------------------------------------------------------------------
# System Design Prompt Registry
# ---------------------------------------------------------------------------

SYSTEM_DESIGN_PROMPT_CONFIGS = [
    {
        "domain": "system-design",
        "seniority": "junior",
        "prompt_template": JUNIOR_SYSTEM_DESIGN_SCALABILITY_PROMPT,
    },
    {
        "domain": "system-design",
        "seniority": "junior",
        "prompt_template": JUNIOR_SYSTEM_DESIGN_DATA_PROMPT,
    },
    {
        "domain": "system-design",
        "seniority": "junior",
        "prompt_template": JUNIOR_SYSTEM_DESIGN_API_PROMPT,
    },
    {
        "domain": "system-design",
        "seniority": "senior",
        "prompt_template": SENIOR_SYSTEM_DESIGN_DISTRIBUTED_PROMPT,
    },
    {
        "domain": "system-design",
        "seniority": "senior",
        "prompt_template": SENIOR_SYSTEM_DESIGN_MULTIREGION_PROMPT,
    },
    {
        "domain": "system-design",
        "seniority": "senior",
        "prompt_template": SENIOR_SYSTEM_DESIGN_TRANSACTIONS_PROMPT,
    },
]