# Fedora -devel Package Discovery & Installation Workflow

When a build fails with missing C/C++ headers (e.g., `uv.h`, `luv.h`, `openssl/ssl.h`):

1. **Search quietly**:
   ```bash
   dnf search <library> --quiet | grep -i devel | head -5
   ```
2. **Install into container**:
   ```bash
   sudo dnf install -y <library>-devel
   ```
3. **Verify pkg-config**:
   ```bash
   pkg-config --cflags --libs <library>
   ```
