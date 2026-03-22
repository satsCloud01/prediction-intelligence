from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./predictor.db"
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as session:
        yield session


async def init_db():
    from predictor.models import (  # noqa: F401
        Project, SeedDocument, KnowledgeNode, KnowledgeEdge,
        AgentPersona, SimulationRun, SimulationEvent, AgentMessage,
        PredictionReport, InteractionSession, ChatMessage,
        AuditLog, LLMUsageLog,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
