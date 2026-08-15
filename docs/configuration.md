# Configuration

Edit `config/toolkit.conf`. It centralizes service URLs, monitor intervals,
temperature/usage thresholds, doctor defaults, and benchmark defaults.

Toolkit 2.0 starts with monitor intervals centralized. Existing scripts remain
behavior-compatible; further threshold migration can be done incrementally.

## 2.0.1 centralization

Runtime paths, service hosts/ports and URLs, monitor intervals, bar width, health thresholds, process-VRAM thresholds, readiness polling, doctor defaults, and benchmark token defaults live in `config/toolkit.conf`. Commands source `lib/ai-common.sh`, which resolves the real toolkit root through `readlink -f`; installed symlinks therefore use the repository configuration rather than `$HOME/bin` as a false project root.

To test a temporary configuration without editing the repository, set `AI_TOOLKIT_CONFIG=/path/to/toolkit.conf` before invoking a toolkit command.
