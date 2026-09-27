# AI Studio: design blueprint

The **AI Agents** page shipped in Lumen is the working first slice of a larger
vision: an AI-native workspace where people collaborate with specialized agents.
This document is the design blueprint for that full product (the parts beyond
the current page are spec, not yet built).

> Scope note: Lumen today ships the **Agent Hub** (directory, cards, detail,
> persona chat grounded in real data). Projects / Discussion Studio / Task board
> / Deliverables are designed here and are the roadmap.

---

## 1. Information architecture

```
Workspace
├── Dashboard            exec view: project health, agent utilization, deliverables
├── Projects             primary object; each has its own workspace
│   └── Project
│       ├── Overview     context, problem, objective, success metrics, stakeholders
│       ├── Discussion   threaded chat with @agent mentions
│       ├── Tasks        kanban / list / timeline / sprint / calendar
│       ├── AI Team      agents assigned; collaboration graph
│       ├── Documents    notes, specs, research
│       ├── Deliverables versioned agent outputs
│       ├── Decisions    decision log
│       ├── Timeline     milestones
│       └── Analytics    project metrics
├── AI Agents            ← SHIPPED: directory, cards, detail, persona chat
├── Tasks                cross-project task inbox
├── Documents            knowledge base
├── Discussions          cross-project conversations
├── Deliverables         all generated artifacts
├── Analytics            productivity, ROI, AI utilization
└── Settings             workspace, members, agents config, billing
```

## 2. Primary user flow

`Create project → describe problem & objective → assign agents → agents
discuss & challenge → tasks generated → agents produce deliverables → human
reviews/approves → versioned & stored → dashboard reflects progress.`

## 3. Sitemap (routes)

```
/                         dashboard
/projects                 list
/projects/:id/(overview|discussion|tasks|team|docs|deliverables|decisions|timeline|analytics)
/agents                   hub   (shipped)
/agents/:id               agent detail (modal in current build)
/tasks                    global task views
/docs                     knowledge base
/discussions              global discussions
/deliverables             artifact library
/analytics                exec analytics
/settings/*               workspace settings
```

## 4. Agent model

19 roles across Product, Data, Engineering, Design, Growth (see
`app/agents.py`). Each agent: `id, role, category, expertise, persona,
status (active|busy|idle), workload, open tasks, deliverables, rating, skills`.
A persona system-prompt shapes the agent's voice; **all numeric claims come
from the deterministic analytics engine** (no naked numbers), so a Data
Analyst answer is grounded, not invented.

Actions per agent: Chat · Assign Task · Invite to Project · Create Deliverable
· Review Work · Collaborate.

## 5. Collaboration model

Agents assigned to a project share a context bus (project overview + documents +
prior decisions). They can: propose, challenge an assumption, hand off
(`@DataAnalyst → @PM`), and review each other's deliverables. Visualized as a
directed collaboration graph on the project **AI Team** tab.

## 6. Database schema (sketch)

```
workspaces(id, name, plan)
users(id, workspace_id, name, role)
agents(id, role, category, persona, skills[], default_status)
projects(id, workspace_id, name, problem, objective, success_metrics,
         status, priority, created_by, created_at)
project_agents(project_id, agent_id, role_on_project)
tasks(id, project_id, title, description, owner_user_id, agent_id,
      status, priority, due_date)
task_links(task_id, depends_on_task_id)            -- dependencies/blockers
messages(id, project_id, thread_id, author_type[user|agent], author_id,
         body, mentions[], created_at)
deliverables(id, project_id, agent_id, type, title, content_ref, version,
             status[draft|in_review|approved], created_at)
deliverable_versions(deliverable_id, version, content_ref, created_at)
decisions(id, project_id, summary, rationale, decided_by, decided_at)
events(id, workspace_id, actor_type, actor_id, verb, object, ts)  -- activity
```

## 7. API architecture (REST sketch)

```
GET    /api/agents                       roster (shipped)
POST   /api/ask/stream {question, agent}  grounded chat in agent voice (shipped)
GET    /api/projects | POST /api/projects
GET    /api/projects/:id
POST   /api/projects/:id/agents          assign agent
GET/POST /api/projects/:id/tasks
GET/POST /api/projects/:id/messages      discussion (SSE stream for live)
POST   /api/projects/:id/deliverables    agent generates an artifact
GET    /api/deliverables/:id/versions
GET    /api/analytics/overview           exec dashboard
```

Agent execution: an orchestrator routes a task to the agent's tool set
(analytics engine, doc generator, code scaffolder) and streams results over SSE.

## 8. Design system

Reuses Lumen's tokens (Solarized light/dark, `app.css`): semantic color tokens,
4/8px spacing, Inter + JetBrains Mono, card/glass surfaces, 150–250ms motion.
Agent-specific components: avatar with status dot, workload bar, skill chips,
metric trio, action grid (`.agent-*` classes).

## 9. Wireframes (described)

- **Dashboard:** top KPI row (project health, active agents, deliverables,
  blocked) → 2-col: project health list + agent utilization heat → activity feed.
- **Agent Hub (shipped):** hero → KPI row → category filter → card grid → detail
  modal with capabilities + action grid.
- **Project Workspace:** left context rail (overview fields) · center tabbed
  panel · right AI-team rail (assigned agents, quick @mention).
- **Discussion Studio:** Slack-style threads, `@agent` mentions, inline
  deliverable previews, file/voice attach, project-context chip.
- **Task board:** Linear-style kanban with agent avatars on cards, swimlanes by
  status, command-K to create.

## 10. Hi-fi UI principles

Clean, dense, fast (Linear/Vercel/Stripe quality). Keyboard-first (⌘K), instant
optimistic updates, streaming agent output, versioned everything, light/dark.

## 11. Roadmap

1. **Now:** Agent Hub + grounded persona chat *(shipped)*.
2. **Next:** Projects object + AI-team assignment + Overview tab.
3. Discussion Studio (threaded, @mentions, SSE).
4. Task board (kanban/list) with agent-owned tasks.
5. Deliverable system (versioned artifacts) + review/approve.
6. Exec dashboard (utilization, ROI) + multi-agent collaboration graph.
