"""Integrations layer: clients that talk to external systems (JIRA, GitHub).

The :class:`~ai_engineering_metrics.integrations.base.MetricsSource` protocols
let the orchestration service depend on abstractions, so the real HTTP clients
and the mock clients are fully interchangeable.
"""
