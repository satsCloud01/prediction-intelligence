import { useNavigate } from 'react-router-dom'
import {
  Brain, ChevronRight, ChevronDown, Network, Users, Play, FileText, MessageCircle,
  Sparkles, TrendingUp, Globe, BarChart3, Shield, Zap, Target, Layers, Compass,
} from 'lucide-react'
import TourOverlay from '../components/ui/TourOverlay'
import useTour from '../hooks/useTour'

const STEPS = [
  { num: 1, icon: Network, title: 'Graph Build', desc: 'Upload seed materials, extract entities, and construct a knowledge graph using AI-powered entity recognition.', color: '#0899b5' },
  { num: 2, icon: Users, title: 'Environment Setup', desc: 'Generate diverse autonomous agent personas with unique personalities, beliefs, and behavioral logic.', color: '#4f56c2' },
  { num: 3, icon: Play, title: 'Parallel Simulation', desc: 'Run multi-round swarm intelligence simulations where agents interact, debate, and evolve opinions.', color: '#7c5cbf' },
  { num: 4, icon: FileText, title: 'Report Generation', desc: 'AI-generated prediction reports with confidence scores, key findings, and actionable insights.', color: '#d48f0b' },
  { num: 5, icon: MessageCircle, title: 'Deep Interaction', desc: 'Chat directly with simulated agents post-simulation to explore their reasoning and perspectives.', color: '#c94088' },
]

const DOMAINS = [
  { icon: TrendingUp, title: 'Financial Markets', desc: 'Forecast market trends, rate decisions, and sector performance' },
  { icon: Globe, title: 'Geopolitics', desc: 'Predict diplomatic outcomes, trade negotiations, and policy shifts' },
  { icon: BarChart3, title: 'Public Opinion', desc: 'Simulate sentiment evolution around events and policy proposals' },
  { icon: Shield, title: 'Risk Analysis', desc: 'Model risk scenarios and stress-test strategic decisions' },
  { icon: Zap, title: 'Technology', desc: 'Predict adoption curves, disruption patterns, and innovation trajectories' },
  { icon: Target, title: 'Creative & Narrative', desc: 'Explore story outcomes, scenario planning, and what-if analyses' },
]

const TENETS = [
  { icon: Sparkles, title: 'Universal BYOK', desc: 'Bring any LLM key — Anthropic, OpenAI, Google, Mistral, Groq, Together, or run locally with Ollama.' },
  { icon: Network, title: 'Knowledge Graphs', desc: 'AI-powered entity extraction and relationship mapping from seed documents with full manual CRUD.' },
  { icon: Users, title: 'Autonomous Agents', desc: 'Unique personas with personality, beliefs, memory, and behavioral logic — create manually or generate with AI.' },
  { icon: Layers, title: 'Swarm Intelligence', desc: 'Emergent consensus through real multi-round agent interaction, debate, and opinion evolution.' },
]

const TOUR_STEPS = [
  {
    target: '[data-tour="hero"]',
    title: 'Welcome to PredictionIntelligence',
    content: 'A swarm intelligence engine that builds parallel digital worlds with autonomous agents to predict outcomes across any domain.',
    example: 'Click "Get Started" to jump straight into creating your first prediction project.',
    proTip: 'The platform works entirely in your browser with your own API keys — no data leaves your machine.',
  },
  {
    target: '[data-tour="stats"]',
    title: 'Platform at a Glance',
    content: 'Key metrics showing the breadth of the platform: 7 LLM providers, 5 pipeline stages, unlimited agent personas, and 6+ prediction domains.',
    example: 'Hover over each stat card to see the subtle animation effect.',
    proTip: 'The "infinite agents" stat is real — you can generate as many unique personas as your prediction needs.',
  },
  {
    target: '[data-tour="pipeline-1"]',
    title: 'Stage 1: Graph Build',
    content: 'Upload seed documents (PDFs, articles, reports) and the AI extracts entities and relationships to build a knowledge graph.',
    example: 'Try uploading a news article about interest rate policy to see entities like "Federal Reserve", "inflation", and "bond yields" extracted automatically.',
    proTip: 'You can manually add, edit, or delete entities and relationships after the AI extraction.',
  },
  {
    target: '[data-tour="pipeline-2"]',
    title: 'Stage 2: Agent Generation',
    content: 'Create diverse autonomous agents with unique personalities, beliefs, expertise, and behavioral logic to represent different perspectives.',
    example: 'Generate 10 agents for a market prediction — you\'ll get personas like "Cautious Bond Trader" and "Tech-Optimist Analyst".',
    proTip: 'Each agent has memory that persists across simulation rounds, so their opinions evolve based on interactions.',
  },
  {
    target: '[data-tour="pipeline-3"]',
    title: 'Stage 3: Parallel Simulation',
    content: 'Run multi-round simulations where agents interact, debate, challenge each other, and evolve their positions through swarm dynamics.',
    example: 'Run a 5-round simulation on "Will AI regulation pass in 2026?" and watch consensus form.',
    proTip: 'More rounds lead to deeper convergence, but 3-5 rounds usually surface the key dynamics.',
  },
  {
    target: '[data-tour="pipeline-4"]',
    title: 'Stage 4: Report Generation',
    content: 'After simulation, the AI synthesizes all agent interactions into a structured prediction report with confidence scores and key findings.',
    example: 'View a sample report to see prediction confidence, dissenting views, and risk factors laid out clearly.',
    proTip: 'Reports include both majority consensus and notable minority opinions for balanced analysis.',
  },
  {
    target: '[data-tour="pipeline-5"]',
    title: 'Stage 5: Deep Interaction',
    content: 'Chat directly with any simulated agent post-simulation to explore their reasoning, challenge their assumptions, or dig deeper.',
    example: 'Ask the "Skeptical Economist" agent: "Why do you disagree with the majority prediction?"',
    proTip: 'Agent conversations reference their actual simulation memory, so responses are contextually grounded.',
  },
  {
    target: '[data-tour="domains"]',
    title: 'Prediction Domains',
    content: 'PredictionIntelligence works across any domain: financial markets, geopolitics, public opinion, risk analysis, technology trends, and creative scenario planning.',
    example: 'Try a geopolitics prediction: "What will happen with US-China trade relations in Q3 2026?"',
    proTip: 'You can combine multiple domains in a single project for cross-domain predictions.',
  },
  {
    target: '[data-tour="tenet-byok"]',
    title: 'BYOK: Bring Your Own Key',
    content: 'Use any LLM provider — Anthropic Claude, OpenAI GPT, Google Gemini, Mistral, Groq, Together AI, or even local models via Ollama.',
    example: 'Go to Settings and paste your Anthropic API key to start using Claude for agent generation and simulation.',
    proTip: 'Keys are stored only in your browser\'s localStorage and never sent to any server.',
  },
  {
    target: '[data-tour="tenet-graphs"]',
    title: 'Knowledge Graphs',
    content: 'AI-powered entity extraction builds rich knowledge graphs from your seed materials, mapping entities, relationships, and context.',
    example: 'Upload a financial report and see how companies, metrics, and market forces are automatically connected.',
    proTip: 'The graph visualization is interactive — drag nodes, zoom, and click edges to see relationship details.',
  },
  {
    target: '[data-tour="tenet-agents"]',
    title: 'Autonomous Agents',
    content: 'Each agent is a fully autonomous persona with personality traits, domain expertise, beliefs, reasoning style, and persistent memory.',
    example: 'Create a custom agent: "Conservative Central Banker" with high risk-aversion and monetary policy expertise.',
    proTip: 'Agents can be saved and reused across projects — build a library of expert personas.',
  },
  {
    target: '[data-tour="tenet-swarm"]',
    title: 'Swarm Intelligence',
    content: 'Emergent predictions arise from genuine multi-round agent interactions — not averaged scores, but real debate and convergence dynamics.',
    example: 'Watch the consensus chart during simulation to see how agent positions shift round by round.',
    proTip: 'Swarm intelligence often surfaces insights that no single agent or analyst would identify alone.',
  },
  {
    target: '[data-tour="nav-projects"]',
    title: 'Projects',
    content: 'The Projects page is your workspace — create, manage, and track all your prediction projects in one place.',
    example: 'Click "View Demo Project" to explore a pre-built prediction with sample data and results.',
    proTip: 'Each project maintains its own knowledge graph, agents, and simulation history independently.',
  },
  {
    target: '[data-tour="nav-dashboard"]',
    title: 'Dashboard',
    content: 'The Dashboard gives you an overview of all projects, recent simulations, prediction accuracy tracking, and system status.',
    example: 'Open the Dashboard to see your active projects, recent predictions, and accuracy trends.',
    proTip: 'Pin your most important projects to the Dashboard for quick access.',
  },
  {
    target: '[data-tour="nav-platform"]',
    title: 'Settings & API Keys',
    content: 'Configure your LLM provider keys, default simulation parameters, and agent generation preferences in Settings.',
    example: 'Navigate to Settings and configure your preferred LLM provider for agent generation.',
    proTip: 'You can set different providers for different tasks — e.g., Claude for agents, GPT for reports.',
  },
  {
    target: '[data-tour="pipeline-3"]',
    title: 'Round-by-Round Simulation',
    content: 'Each simulation round shows agent interactions in real time — see arguments form, alliances shift, and consensus emerge across rounds.',
    example: 'During a simulation, click on any round to see the full transcript of agent-to-agent interactions.',
    proTip: 'Export round-by-round data as JSON for external analysis or visualization.',
  },
  {
    target: '[data-tour="cta"]',
    title: 'Ready to Start Predicting?',
    content: 'You\'ve seen the full platform. Upload your seed materials, generate agents, run simulations, and get AI-powered prediction reports.',
    example: 'Click "Launch Platform" to create your first prediction project right now.',
    proTip: 'Start with a simple prediction question and 5 agents — you can always add complexity later.',
  },
]

export default function Landing() {
  const navigate = useNavigate()
  const tour = useTour('landing', TOUR_STEPS)

  return (
    <div style={{ background: 'linear-gradient(180deg, #f8f9fc 0%, #eef1f8 50%, #e8ecf4 100%)' }}>
      {/* ── Navbar ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md" style={{ borderBottom: '1px solid rgba(30,45,82,0.08)' }}>
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center animate-glow" style={{ background: 'var(--navy)' }}>
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-display font-bold text-navy-700">Prediction</span>
              <span className="font-display font-bold text-gold-500">Intelligence</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={(e) => { e.preventDefault(); e.stopPropagation(); tour.start(); }}
              className="flex items-center gap-2 text-sm px-5 py-2.5 rounded-lg font-medium transition-all"
              style={{
                color: '#c8a96e',
                border: '1px solid rgba(200,169,110,0.3)',
                background: 'rgba(200,169,110,0.06)',
              }}
            >
              <Compass className="w-4 h-4" /> Take a Tour
            </button>
            <button onClick={() => navigate('/dashboard')} className="btn-primary text-sm px-6 py-2.5" data-tour="nav-dashboard">
              Open Platform <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section data-tour="hero" className="min-h-screen flex flex-col items-center justify-center px-6 relative grid-bg">
        <div className="max-w-[1400px] mx-auto text-center relative z-10">
          <div className="section-label mb-6">Swarm Intelligence Engine</div>
          <h1 className="font-display font-black text-navy-700 leading-tight mb-6"
            style={{ fontSize: 'clamp(42px, 5.5vw, 80px)' }}>
            Predict Anything
          </h1>
          <p className="font-display italic text-navy-500 mb-10"
            style={{ fontSize: 'clamp(18px, 2.2vw, 28px)' }}>
            Build parallel digital worlds. Let autonomous agent swarms converge on the future.
          </p>

          {/* Stats row */}
          <div data-tour="stats" className="flex flex-wrap justify-center gap-5 mb-12">
            {[
              { value: '7', label: 'LLM Providers' },
              { value: '5', label: 'Pipeline Stages' },
              { value: '\u221e', label: 'Agent Personas' },
              { value: '6+', label: 'Prediction Domains' },
            ].map(s => (
              <div key={s.label} className="stat-card text-center min-w-[140px]">
                <div className="font-display font-extrabold text-navy-700" style={{ fontSize: 36 }}>{s.value}</div>
                <div className="text-[11px] uppercase tracking-[2px] text-navy-400 font-semibold mt-1">{s.label}</div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-center gap-4">
            <button onClick={() => navigate('/dashboard')} className="btn-primary text-lg px-10 py-4" data-tour="nav-platform">
              Get Started <ChevronRight className="w-5 h-5" />
            </button>
            <button onClick={() => navigate('/projects')} className="btn-outline text-lg px-10 py-4" data-tour="nav-projects">
              View Demo Project
            </button>
          </div>
        </div>

        {/* Scroll hint */}
        <div className="absolute bottom-8 flex flex-col items-center animate-bounce-subtle">
          <span className="text-[11px] uppercase tracking-[3px] text-navy-300 font-semibold mb-2">Explore</span>
          <ChevronDown className="w-5 h-5 text-navy-300" />
        </div>
      </section>

      <div className="section-divider" />

      {/* ── 5-Stage Pipeline ── */}
      <section className="py-24 px-6 md:px-10">
        <div className="max-w-[1400px] mx-auto">
          <div className="text-center mb-4">
            <div className="section-label mb-4">Architecture</div>
            <h2 className="font-display font-extrabold text-navy-700" style={{ fontSize: 'clamp(28px, 3.5vw, 48px)' }}>
              5-Stage Prediction Pipeline
            </h2>
          </div>
          <div className="gold-divider mx-auto mb-12" />

          <div className="grid grid-cols-1 md:grid-cols-5 gap-5">
            {STEPS.map((step) => (
              <div key={step.num}
                data-tour={`pipeline-${step.num}`}
                className="rounded-2xl p-7 transition-all duration-300 hover:-translate-y-1 relative"
                style={{
                  background: `rgba(${hexToRgb(step.color)}, 0.04)`,
                  border: `1px solid rgba(${hexToRgb(step.color)}, 0.12)`,
                  borderTop: `3px solid ${step.color}`,
                }}>
                <div className="flex items-center gap-2.5 mb-4">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold"
                    style={{ background: step.color }}>
                    {step.num}
                  </div>
                  <step.icon className="w-5 h-5" style={{ color: step.color }} />
                </div>
                <h3 className="text-base font-bold text-navy-700 mb-2">{step.title}</h3>
                <p className="text-sm text-navy-400 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* ── Prediction Domains ── */}
      <section className="py-24 px-6 md:px-10">
        <div className="max-w-[1400px] mx-auto">
          <div className="text-center mb-4">
            <div className="section-label mb-4">Applications</div>
            <h2 className="font-display font-extrabold text-navy-700" style={{ fontSize: 'clamp(28px, 3.5vw, 48px)' }}>
              Prediction Domains
            </h2>
          </div>
          <div className="gold-divider mx-auto mb-12" />

          <div data-tour="domains" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {DOMAINS.map((d) => (
              <div key={d.title} className="card">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
                  style={{ background: 'rgba(30,58,110,0.06)' }}>
                  <d.icon className="w-6 h-6 text-navy-600" />
                </div>
                <h3 className="text-lg font-bold text-navy-700 mb-2">{d.title}</h3>
                <p className="text-sm text-navy-400 leading-relaxed">{d.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* ── Design Tenets ── */}
      <section className="py-24 px-6 md:px-10">
        <div className="max-w-[1400px] mx-auto">
          <div className="text-center mb-4">
            <div className="section-label mb-4">Principles</div>
            <h2 className="font-display font-extrabold text-navy-700" style={{ fontSize: 'clamp(28px, 3.5vw, 48px)' }}>
              Key Capabilities
            </h2>
          </div>
          <div className="gold-divider mx-auto mb-12" />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {TENETS.map((t, i) => {
              const tourKeys = ['tenet-byok', 'tenet-graphs', 'tenet-agents', 'tenet-swarm']
              return (
                <div key={t.title} data-tour={tourKeys[i]} className="card">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
                    style={{ background: 'rgba(200,169,110,0.1)', border: '1px solid rgba(200,169,110,0.15)' }}>
                    <t.icon className="w-6 h-6 text-gold-600" />
                  </div>
                  <h3 className="text-lg font-bold text-navy-700 mb-2">{t.title}</h3>
                  <p className="text-sm text-navy-400 leading-relaxed">{t.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* ── CTA ── */}
      <section data-tour="cta" className="py-24 px-6 md:px-10">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="font-display font-extrabold text-navy-700 mb-4"
            style={{ fontSize: 'clamp(28px, 3.5vw, 48px)' }}>
            Ready to Predict the Future?
          </h2>
          <p className="text-navy-400 text-lg mb-10 max-w-xl mx-auto">
            Upload your seed materials, let swarm intelligence do the work, and get prediction reports you can act on.
          </p>
          <button onClick={() => navigate('/dashboard')} className="btn-primary text-lg px-12 py-4">
            Launch Platform <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="py-10 px-6" style={{ borderTop: '1px solid rgba(30,45,82,0.08)' }}>
        <div className="max-w-[1400px] mx-auto flex items-center justify-between text-xs text-navy-300">
          <div className="flex items-center gap-2">
            <Brain className="w-3.5 h-3.5" />
            <span className="font-display font-semibold">PredictionIntelligence</span>
            <span className="text-navy-200">v1.0</span>
          </div>
          <div className="uppercase tracking-[2px] text-[10px]">Swarm Intelligence Prediction Engine</div>
        </div>
      </footer>

      {/* ── Tour Overlay ── */}
      {tour.isActive && (
        <TourOverlay
          step={tour.step}
          currentStep={tour.currentStep}
          totalSteps={tour.totalSteps}
          onNext={tour.next}
          onPrev={tour.prev}
          onClose={tour.finish}
        />
      )}
    </div>
  )
}

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `${r},${g},${b}`
}
