# Hermes Container & Workspace Migration Documentation

## 1. Overview
The workspace and runtime for Hermes Agent have been cleanly decoupled, migrated from the legacy `ws-ai` container / `LLMs/Cluster` environment into a dedicated, isolated Distrobox container named `ws-hermes`.

- **Container Name**: `ws-hermes`
- **Container Home Directory**: `/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes`
- **Hardware Acceleration**: Enabled via NVIDIA Container Toolkit (`--nvidia`)
- **Package Manager Speedup**: Configured `max_parallel_downloads=20` in `/etc/dnf/dnf.conf`

---

## 2. Directory Layout & Upstream Conformance
All files now strictly conform to upstream standard locations with zero hardcoded legacy paths:

```
/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/
├── .hermes/
│   ├── config.yaml          # Core configuration
│   ├── SOUL.md              # System personality / agent instructions (normalized $HOME paths)
│   ├── .env                 # Environment credentials
│   ├── bin/                 # Tooling & security binaries (e.g. tirith, uv)
│   ├── profiles/            # Custom profiles (cleaned of legacy logs/dbs/hardcoded paths)
│   ├── skills/              # Agent skillsets
│   ├── plugins/             # Active plugins
│   ├── hooks/               # Custom lifecycle hooks
│   └── hermes-agent/        # Core agent repository (Git clone)
├── .local/
│   ├── bin/
│   │   └── hermes           # Upstream production launcher
│   └── share/
│       └── chezmoi/         # Active Git dotfiles tracking repository
├── packages.json            # Complete DNF & Python dependency manifest
├── setup.sh                 # 1:1 automated reproducibility script
└── MIGRATION.md             # This migration record
```

---

## 3. Configuration & Dotfiles Management (Chezmoi)
- `chezmoi` is initialized at `~/.local/share/chezmoi` inside the container home.
- Tracked configurations:
  - `~/.hermes/config.yaml`
  - `~/.hermes/SOUL.md`
  - `~/.local/bin/hermes`
  - `~/.hermes/plugins/`, `hooks/`, `desktop-plugins/`
- All temporary SQLite WAL files, run caches, and legacy paths (`LLMs/Cluster`) have been eradicated.

---

## 4. How to Enter and Run Hermes

### Entering the Container:
```bash
distrobox enter ws-hermes
```

### Running Hermes from Host:
```bash
distrobox enter ws-hermes -- hermes version
distrobox enter ws-hermes -- hermes -m "<model>" --provider "<provider>" -z "<prompt>"
```

### Reproducing on Another Machine:
```bash
cd /path/to/hermes
./setup.sh
```
