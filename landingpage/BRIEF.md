# CLAWG Landing Page — Creative Brief & Prompt

## Objectif

Creer une landing page pour CLAWG, un framework open-source d'agents IA autonomes avec un "cerveau portable" base sur Obsidian. Le site doit donner envie d'installer et utiliser le produit en moins de 30 secondes.

---

## Headline & Sub-headline (exactes, ne pas modifier)

**Headline :**
```
  ███████╗███╗   ███╗ █████╗ ██████╗ ████████╗
  ██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝
  ███████╗██╔████╔██║███████║██████╔╝   ██║
  ╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║
  ███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║
  ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝
   ██████╗██╗      █████╗ ██╗    ██╗ ██████╗
  ██╔════╝██║     ██╔══██╗██║    ██║██╔════╝
  ██║     ██║     ███████║██║ █╗ ██║██║  ███╗
  ██║     ██║     ██╔══██║██║███╗██║██║   ██║
  ╚██████╗███████╗██║  ██║╚███╔███╔╝╚██████╔╝
   ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝  ╚═════╝
```

Le ASCII art doit etre affiche en violet (#a29bfe) dans une police monospace, centre, sur fond sombre. C'est la premiere chose que le visiteur voit.

**Sub-headline :**
> Autonomous open-source AI agents with a portable brain.

**CTA principal :**
```bash
curl -fsSL https://raw.githubusercontent.com/gquthier/CLAWG/main/scripts/install.sh | bash
```
Affiche dans un bloc code stylise, avec un bouton "Copy" a cote.

---

## Palette de couleurs

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg-primary` | `#0a0a0f` | Fond principal (quasi-noir) |
| `--bg-secondary` | `#12121a` | Fond des sections alternees |
| `--bg-card` | `#1a1a2e` | Cartes et blocs de contenu |
| `--border` | `#2a2a4a` | Bordures subtiles |
| `--accent` | `#6c5ce7` | Violet principal (boutons, liens, highlights) |
| `--accent-light` | `#a29bfe` | Violet clair (ASCII art, hover states) |
| `--accent-glow` | `rgba(108, 92, 231, 0.3)` | Glow autour des elements interactifs |
| `--green` | `#00e676` | Status actif, succes, terminal output |
| `--cyan` | `#18ffff` | Accents secondaires, metriques |
| `--orange` | `#ffab40` | Avertissements, badges |
| `--text` | `#e8e8f0` | Texte principal |
| `--text-secondary` | `#8888aa` | Texte secondaire |
| `--text-muted` | `#555577` | Texte discret |

**Theme general :** Dark mode exclusif. Tons violet/indigo sur fond quasi-noir. Pas de mode clair. Gradients subtils violet → noir. Glow effects discrets sur les elements interactifs.

**Polices :**
- Interface : Geist Sans (ou Inter, -apple-system fallback)
- Code / terminal : Geist Mono (ou 'SF Mono', 'Fira Code' fallback)

---

## Proposition de valeur

CLAWG est un framework d'agents IA autonomes dont le "cerveau" (contexte, memoire, skills, profils) vit dans un vault Obsidian portable. Chaque agent demarre avec le meme contexte partage. Le cerveau se synchronise entre machines via Obsidian Sync.

### Les 3 piliers

1. **Un cerveau portable** — Le contexte de tes agents vit dans un vault Obsidian. Edite-le comme des notes. Synchronise-le entre tes machines. C'est du markdown, pas une base de donnees opaque.

2. **Des agents autonomes** — 150+ agents specialises (engineering, marketing, design, sales, testing...) qui partagent le meme cerveau, les memes skills, les memes outils.

3. **Open-source et self-hosted** — Pas de cloud, pas d'abonnement, pas de vendor lock-in. Ton cerveau reste sur ta machine. Tu controles tout.

---

## Sections du site (dans l'ordre)

### Section 1 — Hero
- ASCII art SMART CLAWG en violet (#a29bfe), centre, police monospace
- Sub-headline : "Autonomous open-source AI agents with a portable brain."
- Bloc code avec la commande d'installation curl
- Bouton "Copy" + bouton "View on GitHub"
- Lien discret : www.gquthier.com

### Section 2 — Le probleme
- "Vos agents IA oublient tout entre chaque session."
- "Chaque nouvel agent repart de zero. Pas de memoire partagee. Pas de contexte. Pas de skills reutilisables."
- "Et si vos agents avaient un cerveau ?"

### Section 3 — Comment ca marche (3 colonnes ou etapes)

**Etape 1 : Installe CLAWG**
```bash
curl -fsSL https://raw.githubusercontent.com/gquthier/CLAWG/main/scripts/install.sh | bash
```
Le script detecte ton OS, installe les deps, et te guide.

**Etape 2 : Connecte ton cerveau**
```bash
clawg second-brain link --path "~/Second Brain"
```
Pointe vers un vault Obsidian existant ou cree-en un nouveau.

**Etape 3 : Lance tes agents**
```bash
clawg --agent-id founder
```
L'agent charge automatiquement : ton profil, tes preferences, tes skills, ta memoire, tes cles API chiffrees.

### Section 4 — Le cerveau (vue du vault)

Afficher la structure du vault de maniere visuelle :

```
Second Brain/
├── user.md              ← Qui tu es
├── environment.md       ← Ta machine, tes conventions
├── philosophy.md        ← Tes principes
├── api.md               ← Tes endpoints et cles (chiffrees)
├── agents/
│   └── founder/         ← Profil de ton agent
│       ├── identity.md
│       ├── soul.md
│       └── AGENTS.md
├── skills/              ← 150+ skills partages
├── learning/            ← Lecons durables
├── Projects/            ← Notes de projets
├── secrets/             ← Cles API chiffrees (AES)
└── dashboard/           ← Command Center 3D
```

Chaque element doit etre cliquable/hoverable avec une courte description.

### Section 5 — Chiffres cles (metriques en gros)

| Metrique | Valeur |
|----------|--------|
| Agents specialises | 150+ |
| Skills disponibles | 5 200+ |
| Plateformes de messagerie | 16 (Telegram, Discord, Slack, WhatsApp...) |
| Outils integres | 41 |
| Divisions d'agents | 14 (engineering, marketing, design, sales...) |
| Encryption | AES / PBKDF2 |
| Licence | MIT |
| Prix | Gratuit. Pour toujours. |

### Section 6 — Features (grille de cartes)

**Cerveau portable**
Ton contexte vit dans Obsidian. Edite en markdown, sync entre tes machines. Chaque agent y accede nativement.

**150+ agents specialises**
14 divisions : engineering, marketing, design, sales, testing, product, strategy, spatial-computing... Chaque agent a son identite, son style, ses competences.

**Cles API chiffrees**
Vault keystore avec encryption AES. Les agents sauvegardent et recuperent les cles automatiquement. Jamais affichees en clair.

**Command Center 3D**
Dashboard interactif avec visualisation 3D force-directed de tous tes agents, skills, projets et crons. Embarque dans Obsidian.

**16 plateformes de messagerie**
Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email, SMS, Home Assistant... Un seul cerveau, tous les canaux.

**Skills marketplace**
5 200+ skills dans le catalogue. Installe, cree, partage. Les skills vivent dans le vault et sont partages entre agents.

**Cron jobs & scheduling**
Planifie des taches recurrentes assignees a des agents specifiques. Resultats livres sur la plateforme de ton choix.

**Open-source & self-hosted**
MIT licence. Pas de cloud. Pas de telemetrie. Ton cerveau reste chez toi.

### Section 7 — Installation (reprise du hero, plus detaillee)

```bash
# Install CLAWG (macOS, Linux, WSL2)
curl -fsSL https://raw.githubusercontent.com/gquthier/CLAWG/main/scripts/install.sh | bash

# Configure tes cles API
clawg setup

# Lance ton premier agent
clawg --agent-id founder

# Ouvre le Command Center
clawg dashboard
```

### Section 8 — Footer
- Logo SMART CLAWG (petit, monospace)
- Liens : GitHub, Documentation, www.gquthier.com
- "Autonomous open-source AI agents with a portable brain."
- MIT License

---

## References de design

Le style doit s'inspirer de ces sites (dark mode, terminal-aesthetic, developer-focused) :

- **OpenClaw** (openclaw.org) — Dark theme, violet/purple accents, ASCII art, terminal blocks
- **Hermes Agent** — Dark mode, gradient hero, code-first presentation
- **Cursor.com** — Clean dark UI, glow effects subtils, animations douces
- **Linear.app** — Dark mode, cartes avec bordures subtiles, typographie clean
- **Warp.dev** — Terminal aesthetic, dark background, code blocks stylises

### Patterns a reprendre
- Hero plein ecran avec ASCII art + commande d'installation
- Sections alternant fond #0a0a0f et #12121a
- Cartes avec bordure 1px solid #2a2a4a et hover glow violet
- Blocs de code avec fond #1a1a2e, syntax highlighting vert (#00e676) pour le terminal
- Animations subtiles au scroll (fade-in, slide-up)
- Pas de carousel, pas de popup, pas de cookie banner
- Mobile responsive (le ASCII art passe en plus petit ou est remplace par le texte "SMART CLAWG")

---

## Contraintes techniques

- HTML/CSS/JS pur (pas de framework, pas de build step)
- Un seul fichier HTML self-contained (ou HTML + CSS + JS separes max)
- Pas de dependances externes sauf CDN pour les fonts
- Doit se charger en < 2 secondes
- Mobile-first responsive
- Pas de tracking, pas de cookies, pas d'analytics

---

## Liens

- GitHub : https://github.com/gquthier/CLAWG
- Site : www.gquthier.com
- Installation : `curl -fsSL https://raw.githubusercontent.com/gquthier/CLAWG/main/scripts/install.sh | bash`
