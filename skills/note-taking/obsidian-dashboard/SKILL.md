---
name: obsidian-dashboard
description: Create interactive HTML dashboards for projects inside the Obsidian Second Brain vault. Generates self-contained HTML files with dark theme, progress tracking, milestone timelines, task management, and optional chart visualizations.
version: 1.0.0
author: CLAWG
license: MIT
metadata:
  clawg:
    tags: [Obsidian, Dashboard, HTML, Visualization, Project Management]
    related_skills: [note-taking, project-tracking]
---

# Obsidian Dashboard Creator

Create interactive HTML project dashboards inside the Obsidian Second Brain vault.

## When to Use

- A project has been active for **2+ weeks** and would benefit from visual tracking
- Multiple agents collaborate on the same project
- The user needs visibility into **progress, milestones, metrics, or KPIs**
- A project has **recurring tasks, cron jobs, or scheduled deliverables**
- The user explicitly asks for a project dashboard or progress tracker

**Proactive behavior**: When you detect a long-term project, propose creating a dashboard.
Say something like: "This project is growing — I can create an interactive dashboard in your Second Brain to track progress. Want me to set one up?"

## Where Dashboards Live

All dashboards go in the `dashboard/` folder at the vault root:

```
vault/
└── dashboard/
    ├── command-center.html    ← Global CLAWG Command Center (pre-installed)
    ├── my-project.html        ← Per-project dashboards you create
    └── another-project.html
```

## How to View in Obsidian

Dashboards are HTML files. Obsidian needs a plugin to render them inline:

### Option 1: Custom Frames plugin (recommended)
1. Install **Custom Frames** by Ellpeck from Obsidian Community Plugins
2. In Settings > Custom Frames > Add Frame:
   - URL: path to the HTML file (use `file://` protocol)
   - Or open the HTML file externally and point to `localhost` if using the CLAWG server

### Option 2: HTML Reader plugin
1. Install **HTML Reader** (`obsidian-html-plugin`) by nuthrash
2. Simply click any `.html` file in the vault — it opens as a tab
3. Set security mode to `BALANCE_MODE` for interactive dashboards

### Option 3: Embed in a note
Create a markdown note that embeds the dashboard:

```markdown
# Project Dashboard

<iframe src="dashboard/my-project.html" width="100%" height="900" style="border:none; border-radius:8px;"></iframe>
```

Or with the `embed-html` plugin:
```
​```embedhtml
path: dashboard/my-project.html
height: 900
​```
```

### Option 4: CLAWG Dashboard Server
Run `clawg dashboard` to serve all dashboards with a local API that provides live data.

## Steps to Create a Dashboard

### 1. Gather Project Information

Collect from the user or infer from context:
- **Project name** and one-line description
- **Start date** and target completion date (if any)
- **Milestones** — key deliverables with dates/status
- **Tasks** — current task list with assignees and status
- **Metrics** — any KPIs to track (lines of code, tests passing, revenue, users, etc.)
- **Agents involved** — which CLAWG agents work on this project

### 2. Generate the HTML Dashboard

Use the template below as a starting point. Customize sections based on what the project needs.

**File naming**: `dashboard/<project-slug>.html` (lowercase, hyphens, no spaces)

### 3. Announce to the User

After creating the dashboard, tell the user:
- Where the file is: `dashboard/<name>.html`
- How to view it: recommend HTML Reader or Custom Frames plugin
- That they can run `clawg dashboard` to view it in browser

### 4. Keep it Updated

When you work on the project in future sessions:
- Update task statuses
- Add new milestones or events
- Update metrics
- Add timeline entries

## Dashboard Template

The template below is a complete, self-contained HTML file. Copy and customize it.

Key sections to customize:
- `PROJECT_CONFIG` object at the top — project name, dates, description
- `MILESTONES` array — add/remove milestones
- `TASKS` array — current task list
- `METRICS` array — KPIs and their values
- `TIMELINE` array — chronological events

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{PROJECT_NAME}} — Dashboard</title>
<style>
:root {
  --bg: #0a0a0f;
  --bg2: #12121a;
  --card: #1a1a2e;
  --border: #2a2a4a;
  --accent: #6c5ce7;
  --accent2: #a29bfe;
  --green: #00e676;
  --red: #ff5252;
  --orange: #ffab40;
  --cyan: #18ffff;
  --text: #e8e8f0;
  --text2: #8888aa;
  --muted: #555577;
  --mono: 'SF Mono', 'Cascadia Code', 'Fira Code', monospace;
  --sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:var(--sans); background:var(--bg); color:var(--text); padding:24px; }
h1 { font-size:24px; font-weight:800; margin-bottom:4px;
     background:linear-gradient(135deg,var(--accent),var(--accent2));
     -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.subtitle { font-size:13px; color:var(--text2); margin-bottom:24px; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-bottom:24px; }
.card { background:var(--card); border:1px solid var(--border); border-radius:8px; padding:16px; }
.card-label { font-size:10px; text-transform:uppercase; letter-spacing:1.5px; color:var(--muted); margin-bottom:4px; }
.card-value { font-size:28px; font-weight:700; font-family:var(--mono); }
.card-value.green { color:var(--green); }
.card-value.purple { color:var(--accent); }
.card-value.orange { color:var(--orange); }
.card-value.cyan { color:var(--cyan); }
h2 { font-size:16px; font-weight:700; margin:24px 0 12px; }
.progress-bar { background:var(--border); border-radius:4px; height:8px; margin:8px 0 16px; overflow:hidden; }
.progress-fill { height:100%; border-radius:4px; background:linear-gradient(90deg,var(--accent),var(--green)); transition:width 0.5s; }
table { width:100%; border-collapse:collapse; }
th { text-align:left; font-size:10px; text-transform:uppercase; letter-spacing:1px; color:var(--muted);
     padding:8px 12px; border-bottom:1px solid var(--border); }
td { padding:8px 12px; font-size:13px; border-bottom:1px solid rgba(42,42,74,0.3); }
tr:hover td { background:var(--card); }
.badge { display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; font-family:var(--mono); }
.badge-done { background:rgba(0,230,118,0.15); color:var(--green); }
.badge-active { background:rgba(108,92,231,0.15); color:var(--accent); }
.badge-pending { background:rgba(255,171,64,0.15); color:var(--orange); }
.badge-blocked { background:rgba(255,82,82,0.15); color:var(--red); }
.timeline { border-left:2px solid var(--border); margin-left:12px; padding-left:20px; }
.tl-item { margin-bottom:16px; position:relative; }
.tl-item::before { content:''; position:absolute; left:-25px; top:4px; width:10px; height:10px;
  border-radius:50%; background:var(--accent); border:2px solid var(--bg); }
.tl-date { font-size:11px; color:var(--muted); font-family:var(--mono); }
.tl-text { font-size:13px; margin-top:2px; }
.footer { margin-top:32px; font-size:11px; color:var(--muted); text-align:center; font-family:var(--mono); }
</style>
</head>
<body>

<h1 id="title"></h1>
<div class="subtitle" id="subtitle"></div>

<!-- Metrics Cards -->
<div class="grid" id="metrics-grid"></div>

<!-- Progress -->
<h2>Overall Progress</h2>
<div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>

<!-- Milestones -->
<h2>Milestones</h2>
<table id="milestones-table">
  <thead><tr><th>Status</th><th>Milestone</th><th>Target</th><th>Notes</th></tr></thead>
  <tbody></tbody>
</table>

<!-- Tasks -->
<h2>Tasks</h2>
<table id="tasks-table">
  <thead><tr><th>Status</th><th>Task</th><th>Agent</th><th>Priority</th></tr></thead>
  <tbody></tbody>
</table>

<!-- Timeline -->
<h2>Timeline</h2>
<div class="timeline" id="timeline"></div>

<div class="footer">
  CLAWG Dashboard &mdash; Last updated: <span id="updated"></span>
</div>

<script>
// ═══════════════════════════════════════
// CUSTOMIZE THIS SECTION FOR YOUR PROJECT
// ═══════════════════════════════════════

const PROJECT = {
  name: "{{PROJECT_NAME}}",
  description: "{{PROJECT_DESCRIPTION}}",
  startDate: "{{START_DATE}}",
  targetDate: "{{TARGET_DATE}}",
};

const METRICS = [
  { label: "Progress", value: "{{PROGRESS}}%", color: "green" },
  { label: "Tasks Done", value: "{{DONE}}/{{TOTAL}}", color: "purple" },
  { label: "Days Left", value: "{{DAYS_LEFT}}", color: "orange" },
  { label: "Agents", value: "{{AGENT_COUNT}}", color: "cyan" },
];

const MILESTONES = [
  // { status: "done|active|pending", name: "...", target: "YYYY-MM-DD", notes: "..." },
  { status: "done", name: "Project kickoff", target: "{{START_DATE}}", notes: "Initial setup complete" },
  { status: "active", name: "Core implementation", target: "{{MID_DATE}}", notes: "In progress" },
  { status: "pending", name: "Testing & QA", target: "{{QA_DATE}}", notes: "" },
  { status: "pending", name: "Launch", target: "{{TARGET_DATE}}", notes: "" },
];

const TASKS = [
  // { status: "done|active|pending|blocked", name: "...", agent: "...", priority: "critical|high|medium|low" },
];

const TIMELINE = [
  // { date: "YYYY-MM-DD", text: "..." },
  { date: "{{START_DATE}}", text: "Project created" },
];

// ═══════════════════════════════════════
// RENDERING (do not edit below)
// ═══════════════════════════════════════

document.getElementById('title').textContent = PROJECT.name;
document.getElementById('subtitle').textContent =
  `${PROJECT.description} — Started ${PROJECT.startDate}` +
  (PROJECT.targetDate ? ` — Target ${PROJECT.targetDate}` : '');

// Metrics
const grid = document.getElementById('metrics-grid');
METRICS.forEach(m => {
  grid.innerHTML += `<div class="card"><div class="card-label">${m.label}</div><div class="card-value ${m.color}">${m.value}</div></div>`;
});

// Progress bar
const done = MILESTONES.filter(m => m.status === 'done').length;
const pct = Math.round((done / Math.max(MILESTONES.length, 1)) * 100);
document.getElementById('progress-fill').style.width = pct + '%';

// Milestones
const mTbody = document.querySelector('#milestones-table tbody');
MILESTONES.forEach(m => {
  mTbody.innerHTML += `<tr>
    <td><span class="badge badge-${m.status}">${m.status}</span></td>
    <td style="font-weight:600">${m.name}</td>
    <td style="font-family:var(--mono);font-size:12px">${m.target}</td>
    <td style="color:var(--text2)">${m.notes}</td>
  </tr>`;
});

// Tasks
const tTbody = document.querySelector('#tasks-table tbody');
if (TASKS.length === 0) {
  tTbody.innerHTML = '<tr><td colspan="4" style="color:var(--muted);text-align:center;padding:20px">No tasks added yet</td></tr>';
} else {
  TASKS.forEach(t => {
    tTbody.innerHTML += `<tr>
      <td><span class="badge badge-${t.status}">${t.status}</span></td>
      <td style="font-weight:600">${t.name}</td>
      <td style="font-family:var(--mono);font-size:12px">${t.agent}</td>
      <td><span class="badge badge-${t.priority === 'critical' ? 'blocked' : t.priority === 'high' ? 'pending' : 'active'}">${t.priority}</span></td>
    </tr>`;
  });
}

// Timeline
const tl = document.getElementById('timeline');
TIMELINE.forEach(e => {
  tl.innerHTML += `<div class="tl-item"><div class="tl-date">${e.date}</div><div class="tl-text">${e.text}</div></div>`;
});

// Updated timestamp
document.getElementById('updated').textContent = new Date().toLocaleString();
</script>
</body>
</html>
```

## Customization Guidelines

### Naming
- File: `dashboard/<project-slug>.html` (lowercase, hyphens)
- Title: Full project name in `PROJECT.name`

### Colors
The template uses the CLAWG dark theme. Available badge classes:
- `badge-done` (green) — completed items
- `badge-active` (purple) — in progress
- `badge-pending` (orange) — not started
- `badge-blocked` (red) — blocked

### Metrics
Replace the `METRICS` array values. Common metrics:
- Progress percentage
- Tasks done / total
- Days remaining
- Agents involved
- Test coverage, builds passing, revenue, users, etc.

### Adding Charts
For projects that need charts, add Chart.js via CDN:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```
Then create `<canvas>` elements and initialize charts in the script section.

### Keeping Dashboards Updated
When working on the project in subsequent sessions:
1. Read the existing dashboard HTML
2. Update the `MILESTONES`, `TASKS`, `TIMELINE`, and `METRICS` arrays
3. Write the updated file back

## Constraints

- Dashboards must be **self-contained** — no external dependencies except CDN libraries
- Use the **CLAWG dark theme** (CSS variables from the template)
- Keep file size under **100KB** per dashboard
- No server-side code — dashboards are static HTML rendered in Obsidian
- Do not store secrets or API keys in dashboard files
