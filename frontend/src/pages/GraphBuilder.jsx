import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';
import { Upload, Plus, Trash2, Edit3, ArrowLeft, ArrowRight, Brain, FileText, Link2, X } from 'lucide-react';
import { api } from '../lib/api';
import { useLLM } from '../lib/llmContext';

const TYPE_COLORS = { entity: '#06b6d4', concept: '#8b5cf6', event: '#f59e0b', location: '#10b981', organization: '#3b82f6', person: '#ec4899' };
const ENTITY_TYPES = Object.keys(TYPE_COLORS);

export default function GraphBuilder() {
  const { id: projectId } = useParams();
  const navigate = useNavigate();
  const { hasActiveKey } = useLLM();
  const [seeds, setSeeds] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [editSeed, setEditSeed] = useState(null);
  const [pasteText, setPasteText] = useState('');
  const [pasteType, setPasteType] = useState('text');
  const [dragOver, setDragOver] = useState(false);
  const [modal, setModal] = useState(null);
  const [building, setBuilding] = useState(false);

  const load = useCallback(async () => {
    if (!projectId) return;
    try {
      const [s, rawNodes, rawEdges] = await Promise.all([
        api.graph.seeds(projectId).catch(() => []),
        api.graph.nodes(projectId).catch(() => []),
        api.graph.edges(projectId).catch(() => []),
      ]);
      setSeeds(Array.isArray(s) ? s : []);
      const gn = rawNodes.map(n => ({
        id: String(n.id),
        position: { x: n.x ?? Math.random() * 600, y: n.y ?? Math.random() * 400 },
        data: { label: n.label, entity_type: n.entity_type, description: n.description },
        style: { background: TYPE_COLORS[n.entity_type] || '#06b6d4', color: '#fff', borderRadius: 8, padding: 10, border: 'none', fontSize: 12 }
      }));
      const ge = rawEdges.map(e => ({
        id: String(e.id), source: String(e.source_node_id), target: String(e.target_node_id),
        label: e.relation, style: { stroke: '#475569' }, labelStyle: { fill: '#94a3b8', fontSize: 10 }
      }));
      setNodes(gn);
      setEdges(ge);
    } catch (e) { alert(e.message); }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  if (!projectId) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="card text-center p-8">
        <p className="text-slate-400 mb-4">Select a project first.</p>
        <button className="btn-primary" onClick={() => navigate('/projects')}>Go to Projects</button>
      </div>
    </div>
  );

  const handleFileDrop = async (e) => {
    e.preventDefault(); setDragOver(false);
    const files = e.dataTransfer?.files || e.target.files;
    if (!files?.length) return;
    for (const file of files) {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('project_id', projectId);
      fd.append('doc_type', file.name.split('.').pop() || 'text');
      try { await api.graph.uploadSeed(fd); } catch (err) { alert(err.message); }
    }
    load();
  };

  const handlePaste = async () => {
    if (!pasteText.trim()) return;
    const fd = new FormData();
    fd.append('file', new Blob([pasteText], { type: 'text/plain' }), 'pasted.txt');
    fd.append('project_id', projectId);
    fd.append('doc_type', pasteType);
    try { await api.graph.uploadSeed(fd); setPasteText(''); load(); } catch (e) { alert(e.message); }
  };

  const deleteSeed = async (seedId) => {
    if (!confirm('Delete this seed?')) return;
    try { await api.graph.deleteSeed(seedId); load(); } catch (e) { alert(e.message); }
  };

  const saveSeedEdit = async () => {
    try {
      await api.graph.updateSeed(editSeed.id, { content: editSeed.content });
      setEditSeed(null); load();
    } catch (e) { alert(e.message); }
  };

  const buildGraph = async () => {
    setBuilding(true);
    try { await api.graph.build(projectId); load(); } catch (e) { alert(e.message); } finally { setBuilding(false); }
  };

  const saveNode = async () => {
    const { data, isEdit } = modal;
    try {
      if (isEdit) {
        await api.graph.updateNode(data.id, { label: data.label, entity_type: data.entity_type, description: data.description, position: data.position });
      } else {
        await api.graph.createNode({ project_id: projectId, label: data.label, entity_type: data.entity_type, description: data.description, position: { x: 300, y: 200 } });
      }
      setModal(null); load();
    } catch (e) { alert(e.message); }
  };

  const deleteNode = async (nodeId) => {
    if (!confirm('Delete this node?')) return;
    try { await api.graph.deleteNode(nodeId); load(); } catch (e) { alert(e.message); }
  };

  const saveEdge = async () => {
    const { data, isEdit } = modal;
    try {
      if (isEdit) {
        await api.graph.updateEdge(data.id, { relation: data.relation });
      } else {
        await api.graph.createEdge({ project_id: +projectId, source_node_id: +data.source, target_node_id: +data.target, relation: data.relation });
      }
      setModal(null); load();
    } catch (e) { alert(e.message); }
  };

  const deleteEdge = async (edgeId) => {
    if (!confirm('Delete this edge?')) return;
    try { await api.graph.deleteEdge(edgeId); load(); } catch (e) { alert(e.message); }
  };

  const onNodeClick = (_, node) => setModal({
    kind: 'node', isEdit: true,
    data: { id: node.id, label: node.data.label, entity_type: node.data.entity_type, description: node.data.description || '', position: node.position }
  });

  const onEdgeClick = (_, edge) => setModal({
    kind: 'edge', isEdit: true,
    data: { id: edge.id, source: edge.source, target: edge.target, relation: edge.label || '' }
  });

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <button className="btn-ghost flex items-center gap-2" onClick={() => navigate(`/projects/${projectId}`)}>
          <ArrowLeft size={16} /> Back
        </button>
        <h1 className="text-lg font-semibold">Knowledge Graph Builder</h1>
        <button className="btn-primary flex items-center gap-2" onClick={() => navigate(`/projects/${projectId}/agents`)}>
          Agents <ArrowRight size={16} />
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel */}
        <div className="w-80 border-r border-slate-800 overflow-y-auto p-4 space-y-4 flex-shrink-0">
          {/* File Upload Drop Zone */}
          <div
            className={`card border-2 border-dashed p-4 text-center cursor-pointer transition ${dragOver ? 'border-cyan-500 bg-cyan-500/10' : 'border-slate-700'}`}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleFileDrop}
          >
            <Upload size={24} className="mx-auto text-cyan-400 mb-2" />
            <p className="text-sm text-slate-400">Drag & drop files or</p>
            <label className="btn-outline text-xs mt-2 inline-block cursor-pointer">
              Browse
              <input type="file" multiple className="hidden" onChange={handleFileDrop} />
            </label>
          </div>

          {/* Manual Text Paste */}
          <div className="card p-3 space-y-2">
            <textarea className="textarea w-full h-20 text-xs" placeholder="Paste text..." value={pasteText} onChange={e => setPasteText(e.target.value)} />
            <div className="flex gap-2">
              <select className="select flex-1 text-xs" value={pasteType} onChange={e => setPasteType(e.target.value)}>
                <option value="text">Text</option>
                <option value="notes">Notes</option>
                <option value="report">Report</option>
              </select>
              <button className="btn-primary text-xs" onClick={handlePaste}>Add</button>
            </div>
          </div>

          {/* AI Graph Build */}
          <button className="btn-primary w-full flex items-center justify-center gap-2" onClick={buildGraph} disabled={building}>
            <Brain size={16} /> {building ? 'Building...' : 'AI Graph Build'}
          </button>

          {/* Seed Documents */}
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-slate-400 flex items-center gap-1">
              <FileText size={14} /> Seeds ({seeds.length})
            </h3>
            {seeds.map(s => (
              <div key={s.id} className="card p-3 text-xs space-y-1">
                <div className="flex justify-between items-center">
                  <span className="font-medium truncate">{s.filename || 'Pasted'}</span>
                  <span className="badge text-[10px]">{s.doc_type}</span>
                </div>
                <p className="text-slate-500">{(s.content || '').split(/\s+/).length} words</p>
                {editSeed?.id === s.id ? (
                  <div className="space-y-1">
                    <textarea className="textarea w-full h-20 text-xs" value={editSeed.content} onChange={e => setEditSeed({ ...editSeed, content: e.target.value })} />
                    <div className="flex gap-1">
                      <button className="btn-primary text-[10px]" onClick={saveSeedEdit}>Save</button>
                      <button className="btn-ghost text-[10px]" onClick={() => setEditSeed(null)}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <p className="text-slate-400 line-clamp-3">{s.content}</p>
                )}
                <div className="flex gap-1">
                  <button className="btn-ghost p-1" onClick={() => setEditSeed({ id: s.id, content: s.content })}><Edit3 size={12} /></button>
                  <button className="btn-ghost p-1 text-red-400" onClick={() => deleteSeed(s.id)}><Trash2 size={12} /></button>
                </div>
              </div>
            ))}
          </div>

          {/* Add Node / Add Edge Buttons */}
          <div className="flex gap-2">
            <button className="btn-outline flex-1 text-xs flex items-center justify-center gap-1" onClick={() => setModal({ kind: 'node', isEdit: false, data: { label: '', entity_type: 'entity', description: '' } })}>
              <Plus size={12} /> Node
            </button>
            <button className="btn-outline flex-1 text-xs flex items-center justify-center gap-1" onClick={() => setModal({ kind: 'edge', isEdit: false, data: { source: '', target: '', relation: '' } })}>
              <Link2 size={12} /> Edge
            </button>
          </div>
        </div>

        {/* Right - React Flow Graph */}
        <div className="flex-1 relative">
          <ReactFlow nodes={nodes} edges={edges} onNodeClick={onNodeClick} onEdgeClick={onEdgeClick} fitView>
            <Background color="#1e293b" gap={20} />
            <Controls className="!bg-slate-800 !border-slate-700" />
            <MiniMap nodeColor={n => TYPE_COLORS[n.data?.entity_type] || '#06b6d4'} className="!bg-slate-900 !border-slate-700" />
          </ReactFlow>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 card p-2 flex gap-3 text-[10px]">
            {ENTITY_TYPES.map(t => (
              <span key={t} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ background: TYPE_COLORS[t] }} />
                {t}
              </span>
            ))}
          </div>

          {/* Edge Management Panel */}
          {edges.length > 0 && (
            <div className="absolute top-4 right-4 card p-2 max-h-40 overflow-y-auto space-y-1 text-[10px] w-48">
              <p className="font-medium text-slate-400">Edges</p>
              {edges.map(e => (
                <div key={e.id} className="flex items-center justify-between">
                  <span className="truncate">{e.label || '—'}</span>
                  <div className="flex gap-1">
                    <button className="btn-ghost p-0" onClick={() => setModal({ kind: 'edge', isEdit: true, data: { id: e.id, source: e.source, target: e.target, relation: e.label || '' } })}>
                      <Edit3 size={10} />
                    </button>
                    <button className="btn-ghost p-0 text-red-400" onClick={() => deleteEdge(e.id)}>
                      <Trash2 size={10} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal for Node/Edge CRUD */}
      {modal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setModal(null)}>
          <div className="card p-6 w-96 space-y-4" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center">
              <h2 className="font-semibold">{modal.isEdit ? 'Edit' : 'Add'} {modal.kind === 'node' ? 'Node' : 'Edge'}</h2>
              <button className="btn-ghost p-1" onClick={() => setModal(null)}><X size={16} /></button>
            </div>
            {modal.kind === 'node' ? (
              <>
                <input className="input w-full" placeholder="Label" value={modal.data.label} onChange={e => setModal({ ...modal, data: { ...modal.data, label: e.target.value } })} />
                <select className="select w-full" value={modal.data.entity_type} onChange={e => setModal({ ...modal, data: { ...modal.data, entity_type: e.target.value } })}>
                  {ENTITY_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
                <textarea className="textarea w-full h-20" placeholder="Description" value={modal.data.description} onChange={e => setModal({ ...modal, data: { ...modal.data, description: e.target.value } })} />
                <div className="flex gap-2 justify-end">
                  {modal.isEdit && <button className="btn-ghost text-red-400" onClick={() => { deleteNode(modal.data.id); setModal(null); }}>Delete</button>}
                  <button className="btn-primary" onClick={saveNode}>{modal.isEdit ? 'Update' : 'Create'}</button>
                </div>
              </>
            ) : (
              <>
                <select className="select w-full" value={modal.data.source} onChange={e => setModal({ ...modal, data: { ...modal.data, source: e.target.value } })}>
                  <option value="">Source node...</option>
                  {nodes.map(n => <option key={n.id} value={n.id}>{n.data.label}</option>)}
                </select>
                <select className="select w-full" value={modal.data.target} onChange={e => setModal({ ...modal, data: { ...modal.data, target: e.target.value } })}>
                  <option value="">Target node...</option>
                  {nodes.map(n => <option key={n.id} value={n.id}>{n.data.label}</option>)}
                </select>
                <input className="input w-full" placeholder="Relation" value={modal.data.relation} onChange={e => setModal({ ...modal, data: { ...modal.data, relation: e.target.value } })} />
                <div className="flex gap-2 justify-end">
                  {modal.isEdit && <button className="btn-ghost text-red-400" onClick={() => { deleteEdge(modal.data.id); setModal(null); }}>Delete</button>}
                  <button className="btn-primary" onClick={saveEdge}>{modal.isEdit ? 'Update' : 'Create'}</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
