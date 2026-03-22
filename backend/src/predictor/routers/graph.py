"""Knowledge graph: seed documents, nodes, edges — full CRUD + AI build."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from predictor.database import get_db
from predictor.models import Project, SeedDocument, KnowledgeNode, KnowledgeEdge
from predictor.llm_dispatcher import call_llm_json

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class SeedDocumentCreate(BaseModel):
    project_id: int
    filename: str
    content: str
    doc_type: str = "text"


class NodeCreate(BaseModel):
    project_id: int
    label: str
    entity_type: str = "entity"
    description: str = ""
    x: float = 0.0
    y: float = 0.0


class NodeUpdate(BaseModel):
    label: str | None = None
    entity_type: str | None = None
    description: str | None = None
    x: float | None = None
    y: float | None = None


class EdgeCreate(BaseModel):
    project_id: int
    source_node_id: int
    target_node_id: int
    relation: str = "related_to"
    weight: float = 1.0


class EdgeUpdate(BaseModel):
    relation: str | None = None
    weight: float | None = None


class BuildGraphRequest(BaseModel):
    project_id: int
    provider: str = ""
    model: str = ""


# ---------------------------------------------------------------------------
# Seed Documents
# ---------------------------------------------------------------------------
@router.get("/{project_id}/seeds")
async def list_seeds(project_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(SeedDocument).where(SeedDocument.project_id == project_id)
    )).scalars().all()
    return [
        {"id": s.id, "filename": s.filename, "doc_type": s.doc_type,
         "word_count": s.word_count, "content": s.content,
         "created_at": s.created_at.isoformat()}
        for s in rows
    ]


@router.post("/seeds")
async def add_seed(body: SeedDocumentCreate, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, body.project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    doc = SeedDocument(
        project_id=body.project_id, filename=body.filename,
        content=body.content, doc_type=body.doc_type,
        word_count=len(body.content.split()),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return {"id": doc.id, "filename": doc.filename, "word_count": doc.word_count}


@router.post("/seeds/upload")
async def upload_seed(
    project_id: int = Form(...),
    doc_type: str = Form("text"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file as a seed document."""
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    content_bytes = await file.read()
    content = content_bytes.decode("utf-8", errors="replace")
    doc = SeedDocument(
        project_id=project_id, filename=file.filename or "uploaded.txt",
        content=content, doc_type=doc_type,
        word_count=len(content.split()),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return {"id": doc.id, "filename": doc.filename, "word_count": doc.word_count}


@router.get("/seeds/{seed_id}")
async def get_seed(seed_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(SeedDocument, seed_id)
    if not doc:
        raise HTTPException(404, "Seed document not found")
    return {"id": doc.id, "filename": doc.filename, "doc_type": doc.doc_type,
            "word_count": doc.word_count, "content": doc.content,
            "project_id": doc.project_id, "created_at": doc.created_at.isoformat()}


@router.put("/seeds/{seed_id}")
async def update_seed(seed_id: int, body: dict, db: AsyncSession = Depends(get_db)):
    doc = await db.get(SeedDocument, seed_id)
    if not doc:
        raise HTTPException(404, "Seed document not found")
    for k in ("filename", "content", "doc_type"):
        if k in body and body[k] is not None:
            setattr(doc, k, body[k])
    if "content" in body:
        doc.word_count = len(body["content"].split())
    await db.commit()
    return {"id": doc.id, "filename": doc.filename, "word_count": doc.word_count}


@router.delete("/seeds/{seed_id}")
async def delete_seed(seed_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(SeedDocument, seed_id)
    if not doc:
        raise HTTPException(404, "Seed document not found")
    await db.delete(doc)
    await db.commit()
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Knowledge Nodes — full CRUD
# ---------------------------------------------------------------------------
@router.get("/{project_id}/nodes")
async def list_nodes(project_id: int, db: AsyncSession = Depends(get_db)):
    nodes = (await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.project_id == project_id)
    )).scalars().all()
    return [
        {"id": n.id, "label": n.label, "entity_type": n.entity_type,
         "description": n.description, "x": n.x, "y": n.y}
        for n in nodes
    ]


@router.post("/nodes")
async def create_node(body: NodeCreate, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, body.project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    node = KnowledgeNode(**body.model_dump())
    db.add(node)
    await db.commit()
    await db.refresh(node)
    return {"id": node.id, "label": node.label, "entity_type": node.entity_type}


@router.get("/nodes/{node_id}")
async def get_node(node_id: int, db: AsyncSession = Depends(get_db)):
    n = await db.get(KnowledgeNode, node_id)
    if not n:
        raise HTTPException(404, "Node not found")
    return {"id": n.id, "label": n.label, "entity_type": n.entity_type,
            "description": n.description, "x": n.x, "y": n.y, "project_id": n.project_id}


@router.put("/nodes/{node_id}")
async def update_node(node_id: int, body: NodeUpdate, db: AsyncSession = Depends(get_db)):
    n = await db.get(KnowledgeNode, node_id)
    if not n:
        raise HTTPException(404, "Node not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(n, k, v)
    await db.commit()
    return {"id": n.id, "label": n.label, "entity_type": n.entity_type}


@router.delete("/nodes/{node_id}")
async def delete_node(node_id: int, db: AsyncSession = Depends(get_db)):
    n = await db.get(KnowledgeNode, node_id)
    if not n:
        raise HTTPException(404, "Node not found")
    # Delete connected edges first
    edges = (await db.execute(
        select(KnowledgeEdge).where(
            (KnowledgeEdge.source_node_id == node_id) | (KnowledgeEdge.target_node_id == node_id)
        )
    )).scalars().all()
    for e in edges:
        await db.delete(e)
    await db.delete(n)
    await db.commit()
    return {"deleted": True, "edges_removed": len(edges)}


# ---------------------------------------------------------------------------
# Knowledge Edges — full CRUD
# ---------------------------------------------------------------------------
@router.get("/{project_id}/edges")
async def list_edges(project_id: int, db: AsyncSession = Depends(get_db)):
    edges = (await db.execute(
        select(KnowledgeEdge).where(KnowledgeEdge.project_id == project_id)
    )).scalars().all()
    return [
        {"id": e.id, "source_node_id": e.source_node_id,
         "target_node_id": e.target_node_id, "relation": e.relation, "weight": e.weight}
        for e in edges
    ]


@router.post("/edges")
async def create_edge(body: EdgeCreate, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, body.project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    src = await db.get(KnowledgeNode, body.source_node_id)
    tgt = await db.get(KnowledgeNode, body.target_node_id)
    if not src or not tgt:
        raise HTTPException(400, "Source or target node not found")
    if src.project_id != body.project_id or tgt.project_id != body.project_id:
        raise HTTPException(400, "Nodes must belong to the same project")
    edge = KnowledgeEdge(**body.model_dump())
    db.add(edge)
    await db.commit()
    await db.refresh(edge)
    return {"id": edge.id, "relation": edge.relation}


@router.put("/edges/{edge_id}")
async def update_edge(edge_id: int, body: EdgeUpdate, db: AsyncSession = Depends(get_db)):
    e = await db.get(KnowledgeEdge, edge_id)
    if not e:
        raise HTTPException(404, "Edge not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(e, k, v)
    await db.commit()
    return {"id": e.id, "relation": e.relation, "weight": e.weight}


@router.delete("/edges/{edge_id}")
async def delete_edge(edge_id: int, db: AsyncSession = Depends(get_db)):
    e = await db.get(KnowledgeEdge, edge_id)
    if not e:
        raise HTTPException(404, "Edge not found")
    await db.delete(e)
    await db.commit()
    return {"deleted": True}


# ---------------------------------------------------------------------------
# AI-powered graph build (extract entities from seeds)
# ---------------------------------------------------------------------------
@router.post("/build")
async def build_graph(body: BuildGraphRequest, x_api_key: Optional[str] = Header(None),
                      db: AsyncSession = Depends(get_db)):
    """Extract entities and relations from seed documents using LLM, build knowledge graph."""
    p = await db.get(Project, body.project_id)
    if not p:
        raise HTTPException(404, "Project not found")

    seeds = (await db.execute(
        select(SeedDocument).where(SeedDocument.project_id == body.project_id)
    )).scalars().all()
    if not seeds:
        raise HTTPException(400, "No seed documents uploaded yet")

    combined = "\n\n---\n\n".join(f"[{s.filename}]\n{s.content}" for s in seeds)

    prompt = f"""Analyze the following documents and extract a knowledge graph.

DOCUMENTS:
{combined}

Extract ALL entities (people, organizations, concepts, events, locations) and their relationships.
Return JSON with this exact structure:
{{
  "entities": [
    {{"label": "entity name", "type": "person|organization|concept|event|location", "description": "brief description"}}
  ],
  "relations": [
    {{"source": "entity label", "target": "entity label", "relation": "relationship verb"}}
  ]
}}"""

    result = await call_llm_json(prompt, api_key=x_api_key or "", provider=body.provider, model=body.model)
    parsed = result.get("parsed", {})
    entities = parsed.get("entities", [])
    relations = parsed.get("relations", [])

    # Clear existing graph
    old_edges = (await db.execute(select(KnowledgeEdge).where(KnowledgeEdge.project_id == body.project_id))).scalars().all()
    for e in old_edges:
        await db.delete(e)
    old_nodes = (await db.execute(select(KnowledgeNode).where(KnowledgeNode.project_id == body.project_id))).scalars().all()
    for n in old_nodes:
        await db.delete(n)
    await db.flush()

    label_to_node = {}
    for i, ent in enumerate(entities):
        node = KnowledgeNode(
            project_id=body.project_id, label=ent.get("label", f"Entity_{i}"),
            entity_type=ent.get("type", "entity"), description=ent.get("description", ""),
            x=100 + (i % 5) * 180, y=100 + (i // 5) * 160,
        )
        db.add(node)
        await db.flush()
        label_to_node[node.label] = node

    edge_count = 0
    for rel in relations:
        src = label_to_node.get(rel.get("source"))
        tgt = label_to_node.get(rel.get("target"))
        if src and tgt:
            db.add(KnowledgeEdge(
                project_id=body.project_id, source_node_id=src.id,
                target_node_id=tgt.id, relation=rel.get("relation", "related_to"),
            ))
            edge_count += 1

    p.status = "graph_built"
    p.current_step = max(p.current_step, 2)
    p.updated_at = datetime.utcnow()
    await db.commit()

    return {
        "nodes_created": len(label_to_node),
        "edges_created": edge_count,
        "llm_provider": result.get("provider", "mock"),
    }
