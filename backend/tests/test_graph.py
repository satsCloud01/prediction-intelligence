"""Knowledge graph (seeds, nodes, edges, build) tests — full CRUD."""

import pytest
from tests.conftest import create_project, add_seed, build_graph

pytestmark = pytest.mark.asyncio


class TestSeedDocuments:
    async def test_list_seeds_for_project1(self, client):
        r = await client.get("/api/graph/1/seeds")
        assert r.status_code == 200
        assert len(r.json()) >= 3

    async def test_seed_has_required_fields(self, client):
        seeds = (await client.get("/api/graph/1/seeds")).json()
        required = {"id", "filename", "doc_type", "word_count", "content", "created_at"}
        for s in seeds:
            assert required.issubset(s.keys())

    async def test_add_seed_text(self, client):
        p = await create_project(client, {"name": "Seed Text Test"})
        s = await add_seed(client, p["id"], {"filename": "text.txt", "doc_type": "text"})
        assert s["filename"] == "text.txt"
        assert s["word_count"] > 0

    @pytest.mark.parametrize("doc_type", ["text", "news", "report", "narrative"])
    async def test_add_seed_various_types(self, client, doc_type):
        p = await create_project(client, {"name": f"Seed {doc_type}"})
        s = await add_seed(client, p["id"], {"filename": f"{doc_type}.txt", "doc_type": doc_type})
        assert s["word_count"] > 0

    async def test_add_seed_project_not_found(self, client):
        r = await client.post("/api/graph/seeds", json={
            "project_id": 99999, "filename": "x.txt", "content": "x",
        })
        assert r.status_code == 404

    async def test_get_seed_detail(self, client):
        p = await create_project(client, {"name": "Get Seed Detail"})
        s = await add_seed(client, p["id"])
        r = await client.get(f"/api/graph/seeds/{s['id']}")
        assert r.status_code == 200
        assert r.json()["content"] is not None
        assert r.json()["project_id"] == p["id"]

    async def test_get_seed_not_found(self, client):
        r = await client.get("/api/graph/seeds/99999")
        assert r.status_code == 404

    async def test_update_seed_content(self, client):
        p = await create_project(client, {"name": "Update Seed"})
        s = await add_seed(client, p["id"])
        r = await client.put(f"/api/graph/seeds/{s['id']}", json={"content": "updated content here"})
        assert r.status_code == 200
        assert r.json()["word_count"] == 3

    async def test_update_seed_filename(self, client):
        p = await create_project(client, {"name": "Update Seed Name"})
        s = await add_seed(client, p["id"])
        await client.put(f"/api/graph/seeds/{s['id']}", json={"filename": "renamed.txt"})
        detail = (await client.get(f"/api/graph/seeds/{s['id']}")).json()
        assert detail["filename"] == "renamed.txt"

    async def test_delete_seed(self, client):
        p = await create_project(client, {"name": "Delete Seed Test"})
        s = await add_seed(client, p["id"])
        r = await client.delete(f"/api/graph/seeds/{s['id']}")
        assert r.status_code == 200
        assert r.json()["deleted"] is True

    async def test_delete_seed_not_found(self, client):
        r = await client.delete("/api/graph/seeds/99999")
        assert r.status_code == 404

    async def test_seed_word_count_accuracy(self, client):
        p = await create_project(client, {"name": "Word Count Test"})
        s = await add_seed(client, p["id"], {"filename": "counted.txt", "content": "one two three four five"})
        assert s["word_count"] == 5


class TestNodeCRUD:
    async def test_list_nodes_for_project1(self, client):
        r = await client.get("/api/graph/1/nodes")
        assert r.status_code == 200
        assert len(r.json()) >= 10

    async def test_create_node(self, client):
        p = await create_project(client, {"name": "Create Node Test"})
        r = await client.post("/api/graph/nodes", json={
            "project_id": p["id"], "label": "Test Entity",
            "entity_type": "concept", "description": "A test concept",
        })
        assert r.status_code == 200
        assert r.json()["label"] == "Test Entity"
        assert r.json()["entity_type"] == "concept"

    async def test_create_node_project_not_found(self, client):
        r = await client.post("/api/graph/nodes", json={
            "project_id": 99999, "label": "X", "entity_type": "entity",
        })
        assert r.status_code == 404

    async def test_get_node_detail(self, client):
        p = await create_project(client, {"name": "Get Node"})
        created = (await client.post("/api/graph/nodes", json={
            "project_id": p["id"], "label": "Detail Node", "entity_type": "person",
        })).json()
        r = await client.get(f"/api/graph/nodes/{created['id']}")
        assert r.status_code == 200
        assert r.json()["label"] == "Detail Node"
        assert r.json()["project_id"] == p["id"]

    async def test_get_node_not_found(self, client):
        r = await client.get("/api/graph/nodes/99999")
        assert r.status_code == 404

    async def test_update_node_label(self, client):
        p = await create_project(client, {"name": "Update Node Label"})
        created = (await client.post("/api/graph/nodes", json={
            "project_id": p["id"], "label": "Before", "entity_type": "entity",
        })).json()
        r = await client.put(f"/api/graph/nodes/{created['id']}", json={"label": "After"})
        assert r.status_code == 200
        assert r.json()["label"] == "After"

    async def test_update_node_type(self, client):
        p = await create_project(client, {"name": "Update Node Type"})
        created = (await client.post("/api/graph/nodes", json={
            "project_id": p["id"], "label": "TypeTest", "entity_type": "entity",
        })).json()
        await client.put(f"/api/graph/nodes/{created['id']}", json={"entity_type": "person"})
        detail = (await client.get(f"/api/graph/nodes/{created['id']}")).json()
        assert detail["entity_type"] == "person"

    async def test_update_node_not_found(self, client):
        r = await client.put("/api/graph/nodes/99999", json={"label": "X"})
        assert r.status_code == 404

    async def test_delete_node(self, client):
        p = await create_project(client, {"name": "Delete Node"})
        created = (await client.post("/api/graph/nodes", json={
            "project_id": p["id"], "label": "ToDelete", "entity_type": "entity",
        })).json()
        r = await client.delete(f"/api/graph/nodes/{created['id']}")
        assert r.status_code == 200
        assert r.json()["deleted"] is True

    async def test_delete_node_cascades_edges(self, client):
        p = await create_project(client, {"name": "Cascade Edge Delete"})
        n1 = (await client.post("/api/graph/nodes", json={"project_id": p["id"], "label": "N1", "entity_type": "entity"})).json()
        n2 = (await client.post("/api/graph/nodes", json={"project_id": p["id"], "label": "N2", "entity_type": "entity"})).json()
        await client.post("/api/graph/edges", json={
            "project_id": p["id"], "source_node_id": n1["id"], "target_node_id": n2["id"], "relation": "linked",
        })
        r = await client.delete(f"/api/graph/nodes/{n1['id']}")
        assert r.json()["edges_removed"] >= 1
        edges = (await client.get(f"/api/graph/{p['id']}/edges")).json()
        assert len(edges) == 0

    async def test_delete_node_not_found(self, client):
        r = await client.delete("/api/graph/nodes/99999")
        assert r.status_code == 404

    @pytest.mark.parametrize("entity_type", ["entity", "concept", "event", "location", "organization", "person"])
    async def test_create_various_node_types(self, client, entity_type):
        p = await create_project(client, {"name": f"NodeType {entity_type}"})
        r = await client.post("/api/graph/nodes", json={
            "project_id": p["id"], "label": f"Test {entity_type}", "entity_type": entity_type,
        })
        assert r.json()["entity_type"] == entity_type


class TestEdgeCRUD:
    async def test_list_edges_for_project1(self, client):
        r = await client.get("/api/graph/1/edges")
        assert r.status_code == 200
        assert len(r.json()) >= 10

    async def test_create_edge(self, client):
        p = await create_project(client, {"name": "Create Edge"})
        n1 = (await client.post("/api/graph/nodes", json={"project_id": p["id"], "label": "Src", "entity_type": "entity"})).json()
        n2 = (await client.post("/api/graph/nodes", json={"project_id": p["id"], "label": "Tgt", "entity_type": "entity"})).json()
        r = await client.post("/api/graph/edges", json={
            "project_id": p["id"], "source_node_id": n1["id"], "target_node_id": n2["id"], "relation": "connects_to",
        })
        assert r.status_code == 200
        assert r.json()["relation"] == "connects_to"

    async def test_create_edge_invalid_nodes(self, client):
        p = await create_project(client, {"name": "Bad Edge"})
        r = await client.post("/api/graph/edges", json={
            "project_id": p["id"], "source_node_id": 99999, "target_node_id": 99998, "relation": "x",
        })
        assert r.status_code == 400

    async def test_update_edge_relation(self, client):
        p = await create_project(client, {"name": "Update Edge"})
        n1 = (await client.post("/api/graph/nodes", json={"project_id": p["id"], "label": "A", "entity_type": "entity"})).json()
        n2 = (await client.post("/api/graph/nodes", json={"project_id": p["id"], "label": "B", "entity_type": "entity"})).json()
        edge = (await client.post("/api/graph/edges", json={
            "project_id": p["id"], "source_node_id": n1["id"], "target_node_id": n2["id"], "relation": "old",
        })).json()
        r = await client.put(f"/api/graph/edges/{edge['id']}", json={"relation": "new_rel"})
        assert r.status_code == 200
        assert r.json()["relation"] == "new_rel"

    async def test_update_edge_not_found(self, client):
        r = await client.put("/api/graph/edges/99999", json={"relation": "x"})
        assert r.status_code == 404

    async def test_delete_edge(self, client):
        p = await create_project(client, {"name": "Delete Edge"})
        n1 = (await client.post("/api/graph/nodes", json={"project_id": p["id"], "label": "X", "entity_type": "entity"})).json()
        n2 = (await client.post("/api/graph/nodes", json={"project_id": p["id"], "label": "Y", "entity_type": "entity"})).json()
        edge = (await client.post("/api/graph/edges", json={
            "project_id": p["id"], "source_node_id": n1["id"], "target_node_id": n2["id"], "relation": "z",
        })).json()
        r = await client.delete(f"/api/graph/edges/{edge['id']}")
        assert r.status_code == 200
        assert r.json()["deleted"] is True

    async def test_delete_edge_not_found(self, client):
        r = await client.delete("/api/graph/edges/99999")
        assert r.status_code == 404

    async def test_cross_project_edge_rejected(self, client):
        p1 = await create_project(client, {"name": "Cross P1"})
        p2 = await create_project(client, {"name": "Cross P2"})
        n1 = (await client.post("/api/graph/nodes", json={"project_id": p1["id"], "label": "A", "entity_type": "entity"})).json()
        n2 = (await client.post("/api/graph/nodes", json={"project_id": p2["id"], "label": "B", "entity_type": "entity"})).json()
        r = await client.post("/api/graph/edges", json={
            "project_id": p1["id"], "source_node_id": n1["id"], "target_node_id": n2["id"], "relation": "x",
        })
        assert r.status_code == 400


class TestBuildGraph:
    async def test_build_graph_no_seeds_returns_400(self, client):
        p = await create_project(client, {"name": "No Seeds Build"})
        r = await client.post("/api/graph/build", json={"project_id": p["id"]})
        assert r.status_code == 400

    async def test_build_graph_project_not_found(self, client):
        r = await client.post("/api/graph/build", json={"project_id": 99999})
        assert r.status_code == 404

    async def test_build_graph_creates_nodes(self, client):
        p = await create_project(client, {"name": "Build Nodes Test"})
        await add_seed(client, p["id"])
        result = await build_graph(client, p["id"])
        assert result["nodes_created"] > 0

    async def test_build_graph_mock_provider(self, client):
        p = await create_project(client, {"name": "Build Mock Provider"})
        await add_seed(client, p["id"])
        result = await build_graph(client, p["id"])
        assert result["llm_provider"] == "mock"

    async def test_build_graph_updates_project_status(self, client):
        p = await create_project(client, {"name": "Build Status Update"})
        await add_seed(client, p["id"])
        await build_graph(client, p["id"])
        project = (await client.get(f"/api/projects/{p['id']}")).json()
        assert project["status"] == "graph_built"
        assert project["current_step"] >= 2
