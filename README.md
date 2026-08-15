# WizardingOps

**Wizarding Operations Console**


A Linux system observability and event forensics tool built around a terminal-based operational workspace.


WizOps provides a single interface for understanding what is happening on a Linux system, what changed, and what deserves attention.


## What WizOps Does


WizOps currently provides:


- System and service discovery
- Event collection from system sources
- Normalized event storage
- Event severity classification
- Event history and forensic inspection
- Service activity and health information
- System resource information
- Event activity and severity trends
- Runtime and database status
- Interactive terminal UI
- Event selection, copying, and exporting
- Persistent local event history


The application is designed around **observation and evidence** rather than automatically making configuration changes.


## Requirements


Currently supported:


- Linux
- Python 3
- `systemd` / `journalctl`
- Bash
- Python `textual` for the interactive interface


WizOps is currently developed and tested on Fedora Linux.


## Installation


Clone or download the repository:


```bash
git clone git@github.com:MrHovannez/wizOpsV1.git
cd wizOpsV1
```

Make the scripts executable:
```bash
chmod +x install.sh uninstall.sh
```

Run the installer:
```bash
./install.sh
```

After installation, launch WizOps with:
```bash
wizops tui
```

The installer places the application under:
```bash
~/.local/share/wizops
```

The command launcher is installed under:
```bash
~/.local/bin/wizops
```

Runtime data is stored separately under:
```bash
~/.wizops
```

This separation keeps application files independent from the user's collected runtime data.


## Usage


Show available commands:
```bash
wizops --help
```

Discover system services and collect recent events:
```bash
wizops discover
```

Launch the interactive console:
```bash
wizops tui
```

Open the operator manual:
```bash
wizops manual
```


## Interactive Console


The TUI is the primary WizOps interface.

It provides multiple operational views for:

Current system state
Event history
Service activity
Event activity over time
Severity trends
Collection status
Database status
Recent attention-worthy events
System resources

Events can be inspected directly from the interface and selected for copying or export.

Data

WizOps maintains a local SQLite event archive.

Runtime data is stored in:
```bash
~/.wizops
```

The database is created automatically during initialization and collection.

WizOps does not require a remote database or external service for its core functionality.


## Uninstallation


To remove the installed application and launcher:
```bash
./uninstall.sh
```

The uninstaller preserves runtime data by default.

It will offer the option to remove the runtime data as well.

Project Structure
 WizardingOps/
  ├── docs/
  │     ├── commands.md
  │     ├── configuration.md
  │     └── manual.md
  ├── install.sh
  ├── uninstall.sh
  └── wizops/
      ├── application/
      ├── capabilities/
      ├── collectors/
      ├── config/
      ├── domain/
      ├── events/
      ├── infrastructure/
      ├── inventory/
      ├── orchestration/
      ├── platform/
      ├── presentation/
      ├── services/
      ├── cli.py
      ├── startup.py
      └── tui.py




## Status


Version 1.0.0

WizOps 1.0 establishes the core operational console, event archive, system discovery, collection pipeline, and interactive observability interface.

The project is currently undergoing cross-machine testing on Fedora Linux.


## License


Open-source free to use.
Further license information will be added in a future release.
