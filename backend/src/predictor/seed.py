"""Auto-seed demo data on first run."""

from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from predictor.models import (
    Project, SeedDocument, KnowledgeNode, KnowledgeEdge,
    AgentPersona, SimulationRun, SimulationEvent, AgentMessage,
    PredictionReport, AuditLog,
)


async def seed(db: AsyncSession):
    existing = (await db.execute(select(Project))).scalars().first()
    if existing:
        return

    # --- Demo Project 1: Market Prediction ---
    p1 = Project(
        name="Q3 2026 Global Market Outlook",
        description="Predict global financial market trends for Q3 2026 using swarm intelligence simulation with diverse economic agent personas.",
        domain="finance",
        prediction_goal="Forecast major market indices movement, interest rate decisions, and sector performance for July-September 2026.",
        status="reported",
        current_step=5,
        agent_count=5,
        simulation_rounds=10,
    )
    db.add(p1)
    await db.flush()

    # Seed documents
    seeds = [
        SeedDocument(project_id=p1.id, filename="fed_minutes_june2026.txt", doc_type="report", word_count=3200,
                     content="Federal Reserve meeting minutes from June 2026 indicate continued monitoring of inflation metrics. The committee noted that while headline inflation has moderated to 2.3%, core services inflation remains sticky at 3.1%. Labor markets show signs of cooling with unemployment rising to 4.2%. GDP growth revised down to 2.1% for 2026."),
        SeedDocument(project_id=p1.id, filename="tech_earnings_q2.txt", doc_type="report", word_count=1800,
                     content="Q2 2026 tech earnings exceeded expectations. AI infrastructure spending drove 15% YoY revenue growth for cloud providers. Semiconductor demand remains strong. Consumer tech showed mixed results with smartphone sales flat but wearables up 22%."),
        SeedDocument(project_id=p1.id, filename="geopolitical_brief.txt", doc_type="news", word_count=1500,
                     content="Trade negotiations between US and EU reach critical phase. New tariff framework proposed covering digital services and agricultural products. Asian markets respond positively to regional trade pact expansion. Middle East tensions ease following diplomatic breakthrough."),
    ]
    for s in seeds:
        db.add(s)
    await db.flush()

    # Knowledge graph nodes
    nodes_data = [
        ("Federal Reserve", "organization", "US central bank responsible for monetary policy"),
        ("Inflation Rate", "concept", "Rate of increase in general price level, currently at 2.3% headline"),
        ("GDP Growth", "concept", "Gross Domestic Product growth rate, revised to 2.1% for 2026"),
        ("Tech Sector", "concept", "Technology industry including AI, cloud, and semiconductors"),
        ("AI Infrastructure", "concept", "Computing infrastructure for artificial intelligence workloads"),
        ("Consumer Confidence", "concept", "Economic indicator measuring household spending outlook"),
        ("Trade Policy", "concept", "International trade agreements and tariff frameworks"),
        ("Labor Market", "concept", "Employment conditions including unemployment rate at 4.2%"),
        ("Interest Rates", "concept", "Federal funds rate and its impact on borrowing costs"),
        ("Global Markets", "concept", "International equity, bond, and commodity markets"),
        ("EU Economy", "organization", "European Union economic bloc and its trade dynamics"),
        ("Semiconductor Industry", "concept", "Chip manufacturing and demand dynamics"),
    ]
    node_objs = []
    for i, (label, etype, desc) in enumerate(nodes_data):
        n = KnowledgeNode(project_id=p1.id, label=label, entity_type=etype, description=desc,
                          x=100 + (i % 4) * 200, y=100 + (i // 4) * 180)
        db.add(n)
        node_objs.append(n)
    await db.flush()

    # Knowledge graph edges
    edges_data = [
        (0, 1, "monitors"), (0, 8, "sets"), (1, 9, "affects"),
        (2, 9, "drives"), (3, 2, "contributes_to"), (4, 3, "enables"),
        (5, 9, "influences"), (6, 9, "impacts"), (7, 0, "informs"),
        (3, 11, "depends_on"), (10, 6, "negotiates"), (8, 5, "affects"),
    ]
    for si, ti, rel in edges_data:
        db.add(KnowledgeEdge(project_id=p1.id, source_node_id=node_objs[si].id,
                             target_node_id=node_objs[ti].id, relation=rel))

    # Agent personas
    personas_data = [
        ("Dr. Sarah Chen", "economist", 42, "Analytical and data-driven, prefers quantitative evidence",
         "PhD in macroeconomics from MIT, 15 years at the Fed", "Markets are fundamentally rational long-term",
         "Predict policy impacts accurately", "#06b6d4"),
        ("Marcus Rivera", "trader", 35, "Risk-tolerant and intuitive, quick decision maker",
         "15 years on Wall Street, specializes in derivatives", "Market sentiment drives short-term moves",
         "Identify profitable trends before the crowd", "#8b5cf6"),
        ("Prof. Aisha Patel", "analyst", 55, "Cautious and methodical, weighs all evidence",
         "Former IMF advisor, Oxford economics professor", "Geopolitics shapes economic outcomes more than models predict",
         "Provide balanced risk assessments", "#f59e0b"),
        ("James O'Brien", "journalist", 38, "Skeptical and investigative, questions consensus",
         "Financial Times senior reporter, Pulitzer nominee", "Transparency and information asymmetry drive market efficiency",
         "Uncover hidden market dynamics and narratives", "#ef4444"),
        ("Lin Wei", "policy_maker", 50, "Diplomatic and strategic, consensus builder",
         "Central bank economist, 20 years in monetary policy", "Stability is the primary objective of economic management",
         "Maintain economic equilibrium while enabling growth", "#10b981"),
    ]
    persona_objs = []
    for name, role, age, personality, bg, beliefs, goals, color in personas_data:
        p = AgentPersona(project_id=p1.id, name=name, role=role, age=age, personality=personality,
                         background=bg, beliefs=beliefs, goals=goals, avatar_color=color)
        db.add(p)
        persona_objs.append(p)
    await db.flush()

    # Simulation run
    run = SimulationRun(
        project_id=p1.id, status="completed", total_rounds=10, current_round=10,
        started_at=datetime.utcnow() - timedelta(hours=2),
        completed_at=datetime.utcnow() - timedelta(hours=1),
        summary="10-round simulation completed with 5 agents. Consensus reached on cautiously optimistic market outlook with key risk factors identified.",
    )
    db.add(run)
    await db.flush()

    # Simulation events
    events_data = [
        (1, "interaction", "Dr. Chen presents inflation data showing unexpected moderation trend", [0, 4], 0.3, 0.6),
        (1, "opinion_shift", "Marcus Rivera adjusts bullish equity position based on inflation data", [1], 0.5, 0.4),
        (2, "interaction", "Prof. Patel raises concerns about EU trade negotiation stalling", [2, 3], -0.2, 0.5),
        (2, "event", "Breaking: New US-EU digital services agreement framework announced", [], 0.6, 0.7),
        (3, "conflict", "Rivera and Patel debate impact of AI spending on broader economy", [1, 2], 0.1, 0.5),
        (3, "interaction", "O'Brien uncovers data suggesting corporate earnings guidance is overly optimistic", [3], -0.3, 0.6),
        (4, "opinion_shift", "Chen revises GDP forecast down slightly after labor data review", [0], -0.1, 0.4),
        (4, "interaction", "Wei proposes monetary policy scenario modeling", [4, 0], 0.2, 0.5),
        (5, "consensus", "Group agrees tech sector will outperform but cautions on valuation", [0, 1, 2, 3, 4], 0.4, 0.8),
        (5, "interaction", "Patel provides historical parallel analysis of current conditions", [2], 0.1, 0.6),
        (6, "event", "Semiconductor supply chain data shows inventory normalization", [], 0.5, 0.5),
        (6, "opinion_shift", "O'Brien shifts from skeptical to cautiously optimistic after new trade data", [3], 0.3, 0.4),
        (7, "interaction", "Wei and Chen discuss interest rate trajectory for Q3", [4, 0], 0.2, 0.7),
        (7, "conflict", "Rivera challenges consensus on rate hold — argues for cut scenario", [1, 4], 0.0, 0.5),
        (8, "interaction", "All agents review consolidated prediction framework", [0, 1, 2, 3, 4], 0.3, 0.8),
        (8, "consensus", "4 of 5 agents agree on moderate bull case with geopolitical hedging", [0, 1, 3, 4], 0.5, 0.9),
        (9, "opinion_shift", "Patel concedes bull case has merit but maintains risk warnings", [2], 0.2, 0.4),
        (10, "consensus", "Final consensus: cautiously optimistic Q3 with sector rotation thesis", [0, 1, 2, 3, 4], 0.5, 1.0),
    ]
    for rnd, etype, desc, agents, sent, imp in events_data:
        db.add(SimulationEvent(run_id=run.id, round_num=rnd, event_type=etype, description=desc,
                               agents_involved=[persona_objs[i].name for i in agents] if agents else [],
                               sentiment=sent, impact=imp))

    # Agent messages (sample)
    messages_data = [
        (0, 1, "Looking at the latest CPI data, headline inflation has moderated to 2.3%. This is significant because it suggests the Fed's tightening cycle may be having the desired effect. However, core services remain sticky at 3.1%."),
        (1, 1, "The inflation moderation you're describing could trigger a relief rally. I'm seeing positioning data that suggests the market isn't fully pricing in a dovish pivot scenario."),
        (2, 2, "I'd urge caution here. The EU trade negotiations are at a critical juncture, and any breakdown could introduce significant volatility. We've seen this pattern before — in 2018 and 2022."),
        (3, 3, "My sources indicate the corporate earnings guidance we've been seeing may be overly optimistic. Several CFOs I've spoken with are hedging their language on forward guidance."),
        (4, 4, "From a policy perspective, we need to balance growth objectives with financial stability. The current rate environment is achieving its goals, but there's limited room for error."),
    ]
    for pi, rnd, content in messages_data:
        db.add(AgentMessage(persona_id=persona_objs[pi].id, run_id=run.id, round_num=rnd, content=content))

    # Prediction report
    report = PredictionReport(
        project_id=p1.id,
        title="Q3 2026 Global Market Outlook — Swarm Intelligence Report",
        executive_summary="Based on a 10-round multi-agent simulation with 5 specialized personas (economist, trader, analyst, journalist, policy maker), the swarm intelligence consensus indicates a moderately positive Q3 2026 outlook. Key drivers include inflation moderation, strong tech sector performance, and improving trade relations. Primary risks center on geopolitical uncertainty and potential earnings disappointments.",
        key_findings=[
            "Strong consensus (78%) on positive short-term market trajectory",
            "Inflation moderation to 2.3% supports continued Fed rate hold through Q3",
            "Tech and AI infrastructure spending remains primary growth driver",
            "Geopolitical risk identified as the main downside factor by 3 of 5 agents",
            "Consumer confidence expected to improve marginally as labor market stabilizes",
            "Sector rotation from defensive to cyclical anticipated mid-quarter",
        ],
        predictions=[
            {"prediction": "S&P 500 will gain 5-8% in Q3 2026", "confidence": 0.72, "timeframe": "90 days"},
            {"prediction": "Federal Reserve maintains current rate through September", "confidence": 0.85, "timeframe": "90 days"},
            {"prediction": "Tech sector outperforms broader market by 3-5%", "confidence": 0.68, "timeframe": "180 days"},
            {"prediction": "US-EU trade deal finalized by August 2026", "confidence": 0.55, "timeframe": "120 days"},
            {"prediction": "Unemployment peaks at 4.3% before declining in Q4", "confidence": 0.62, "timeframe": "180 days"},
        ],
        confidence_score=0.74,
        methodology="Swarm intelligence simulation using 5 diverse autonomous agent personas with distinct expertise, biases, and goals. Agents interacted over 10 rounds, exchanging information, debating, and forming consensus through natural social dynamics. Sentiment analysis and consensus tracking produced the final prediction set.",
    )
    db.add(report)

    # --- Demo Project 2: Public Opinion ---
    p2 = Project(
        name="AI Regulation Public Sentiment",
        description="Simulate public opinion evolution around proposed AI regulation framework using diverse citizen agent personas.",
        domain="politics",
        prediction_goal="Predict public sentiment trajectory and key concerns around the proposed AI Safety Act over the next 6 months.",
        status="draft",
        current_step=1,
        agent_count=0,
        simulation_rounds=15,
    )
    db.add(p2)

    # --- Demo Project 3: Creative ---
    p3 = Project(
        name="Climate Summit Outcome Prediction",
        description="Model international climate negotiation dynamics using agent personas representing key national interests and NGOs.",
        domain="geopolitics",
        prediction_goal="Predict the likely outcomes, agreements, and sticking points of the upcoming Global Climate Summit.",
        status="graph_built",
        current_step=2,
        agent_count=0,
        simulation_rounds=12,
    )
    db.add(p3)

    # Audit logs
    db.add(AuditLog(action="create", entity_type="project", entity_id=p1.id, details="Demo project created: Q3 2026 Global Market Outlook"))
    db.add(AuditLog(action="create", entity_type="project", entity_id=p1.id, details="Demo project created: AI Regulation Public Sentiment"))
    db.add(AuditLog(action="create", entity_type="project", entity_id=p1.id, details="Demo project created: Climate Summit Outcome Prediction"))

    await db.commit()
