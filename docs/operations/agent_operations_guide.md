# Agent Operations — Part 2 of 3: How to Run Hermes

> **Read order**: You are reading file **2/3**.
> Prev → [`AGENT_CONTEXT.md`](./AGENT_CONTEXT.md) (environment & migration state)
> Next → [`AGENT_MILESTONES.md`](./AGENT_MILESTONES.md) (gaps & next steps)

---

## ⚠️ Critical: Do NOT use bare `hermes`

On both the host and inside any distrobox other than `ws-hermes`, the `hermes` command resolves to the **host's** hermes install (Python 3.11, different venv). Always use the patterns below.

---

## Option A — Running inside `ws-ai` distrobox (e.g. Codex)

From inside a container, `distrobox` is not available. Use the **`HOME` override** pattern instead — both `ws-ai` and `ws-hermes` share the same host filesystem, so the hermes home is just a directory.

```bash
# Set convenience vars at session start
export HERMES_HOME=/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes
export HERMES_BIN=$HERMES_HOME/.local/bin/hermes

# Verify hermes version
HOME=$HERMES_HOME $HERMES_BIN version

# Run hermes with a prompt
HOME=$HERMES_HOME $HERMES_BIN -z "your prompt"

# Run with a specific model
HOME=$HERMES_HOME $HERMES_BIN -m gemma-4-4b -z "your prompt"

# Run llama-server
HOME=$HERMES_HOME $HERMES_HOME/.local/bin/llama-server --version

# Use python3.13 directly
HOME=$HERMES_HOME python3.13 -m hermes_cli.main version
```

```bash
# Convenience alias (add at session start)
alias hermes-ws='HOME=/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes /var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.local/bin/hermes'
```

**File access:** Read/write to `$HERMES_HOME` directly — no special access needed.

**Chezmoi:**
```bash
HOME=$HERMES_HOME chezmoi add <file>
HOME=$HERMES_HOME chezmoi git -- commit -m "msg"
```

---

## Option B — Running natively on the host (e.g. opencode)

If launched directly on the Fedora Silverblue host (not inside a distrobox), you have full access to `distrobox` and all host tools.

### B1 — distrobox (proper container isolation, preferred for interactive work)
```bash
# Run a single command inside ws-hermes
distrobox enter ws-hermes -- bash -i -c "hermes version"
distrobox enter ws-hermes -- bash -i -c "hermes -m gemma-4-4b -z 'your prompt'"

# Drop into an interactive shell
distrobox enter ws-hermes
```

### B2 — HOME override (faster, no container spawn, good for file ops)
```bash
export HERMES_HOME=/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes
export HERMES_BIN=$HERMES_HOME/.local/bin/hermes

HOME=$HERMES_HOME $HERMES_BIN version
HOME=$HERMES_HOME $HERMES_BIN -z "your prompt"
```

**Chezmoi from host:**
```bash
distrobox enter ws-hermes -- bash -i -c "chezmoi add <file> && chezmoi git -- commit -m 'msg'"
```

---

## Option C — Running inside `ws-hermes` itself

If you have entered the container directly, everything resolves normally:
```bash
hermes version
hermes -z "your prompt"
chezmoi add <file> && chezmoi git -- commit -m "msg"
```

---

> **Next** → [`AGENT_MILESTONES.md`](./AGENT_MILESTONES.md)
