from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from predictor.database import Base


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str] = mapped_column(Text, default="")
    domain: Mapped[str] = mapped_column(default="general")
    prediction_goal: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(default="draft")  # draft|graph_built|env_ready|simulating|simulated|reported
    current_step: Mapped[int] = mapped_column(default=1)  # 1-5
    agent_count: Mapped[int] = mapped_column(default=0)
    simulation_rounds: Mapped[int] = mapped_column(default=10)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    seeds: Mapped[list["SeedDocument"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    nodes: Mapped[list["KnowledgeNode"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    edges: Mapped[list["KnowledgeEdge"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    personas: Mapped[list["AgentPersona"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    runs: Mapped[list["SimulationRun"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    reports: Mapped[list["PredictionReport"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    interactions: Mapped[list["InteractionSession"]] = relationship(back_populates="project", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Seed Documents
# ---------------------------------------------------------------------------
class SeedDocument(Base):
    __tablename__ = "seed_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    filename: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    doc_type: Mapped[str] = mapped_column(default="text")  # text|news|report|narrative
    word_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="seeds")


# ---------------------------------------------------------------------------
# Knowledge Graph
# ---------------------------------------------------------------------------
class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    label: Mapped[str]
    entity_type: Mapped[str] = mapped_column(default="entity")  # entity|concept|event|location|organization|person
    description: Mapped[str] = mapped_column(Text, default="")
    properties: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    x: Mapped[float] = mapped_column(default=0.0)
    y: Mapped[float] = mapped_column(default=0.0)

    project: Mapped["Project"] = relationship(back_populates="nodes")


class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    source_node_id: Mapped[int] = mapped_column(ForeignKey("knowledge_nodes.id"))
    target_node_id: Mapped[int] = mapped_column(ForeignKey("knowledge_nodes.id"))
    relation: Mapped[str] = mapped_column(default="related_to")
    weight: Mapped[float] = mapped_column(default=1.0)

    project: Mapped["Project"] = relationship(back_populates="edges")


# ---------------------------------------------------------------------------
# Agent Personas
# ---------------------------------------------------------------------------
class AgentPersona(Base):
    __tablename__ = "agent_personas"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str]
    role: Mapped[str] = mapped_column(default="citizen")
    age: Mapped[int] = mapped_column(default=30)
    personality: Mapped[str] = mapped_column(Text, default="")
    background: Mapped[str] = mapped_column(Text, default="")
    beliefs: Mapped[str] = mapped_column(Text, default="")
    goals: Mapped[str] = mapped_column(Text, default="")
    memory: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    avatar_color: Mapped[str] = mapped_column(default="#06b6d4")

    project: Mapped["Project"] = relationship(back_populates="personas")
    messages: Mapped[list["AgentMessage"]] = relationship(back_populates="persona", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    status: Mapped[str] = mapped_column(default="pending")  # pending|running|completed|failed
    total_rounds: Mapped[int] = mapped_column(default=10)
    current_round: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")

    project: Mapped["Project"] = relationship(back_populates="runs")
    events: Mapped[list["SimulationEvent"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class SimulationEvent(Base):
    __tablename__ = "simulation_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("simulation_runs.id"))
    round_num: Mapped[int]
    event_type: Mapped[str] = mapped_column(default="interaction")  # interaction|opinion_shift|conflict|consensus|event
    description: Mapped[str] = mapped_column(Text)
    agents_involved: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    sentiment: Mapped[float] = mapped_column(default=0.0)  # -1 to 1
    impact: Mapped[float] = mapped_column(default=0.0)  # 0 to 1
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    run: Mapped["SimulationRun"] = relationship(back_populates="events")


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("agent_personas.id"))
    run_id: Mapped[int] = mapped_column(ForeignKey("simulation_runs.id"))
    round_num: Mapped[int]
    content: Mapped[str] = mapped_column(Text)
    target_persona_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    sentiment: Mapped[float] = mapped_column(default=0.0)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    persona: Mapped["AgentPersona"] = relationship(back_populates="messages")


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
class PredictionReport(Base):
    __tablename__ = "prediction_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str]
    executive_summary: Mapped[str] = mapped_column(Text, default="")
    key_findings: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    predictions: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[float] = mapped_column(default=0.0)
    methodology: Mapped[str] = mapped_column(Text, default="")
    raw_content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="reports")


# ---------------------------------------------------------------------------
# Interaction (Post-sim chat)
# ---------------------------------------------------------------------------
class InteractionSession(Base):
    __tablename__ = "interaction_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    agent_persona_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agent_personas.id"), nullable=True)
    session_type: Mapped[str] = mapped_column(default="agent")  # agent|analyst
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="interactions")
    chats: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("interaction_sessions.id"))
    role: Mapped[str]  # user|assistant
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    session: Mapped["InteractionSession"] = relationship(back_populates="chats")


# ---------------------------------------------------------------------------
# Audit & Usage
# ---------------------------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str]
    entity_type: Mapped[str]
    entity_id: Mapped[int]
    details: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class LLMUsageLog(Base):
    __tablename__ = "llm_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str]
    model: Mapped[str]
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    latency_ms: Mapped[int] = mapped_column(default=0)
    endpoint: Mapped[str] = mapped_column(default="")
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
