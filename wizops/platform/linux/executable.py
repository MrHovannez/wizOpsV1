from __future__ import annotations

from shutil import which

from wizops.inventory.models import (
    Executable,
    ExecutableInventory,
)


KNOWN_EXECUTABLES = (
    "ollama",
    "llama-server",
    "vllm",
    "docker",
    "podman",
    "containerd",
    "git",
    "python3",
)


class LinuxExecutableProvider:

    def snapshot(self) -> ExecutableInventory:

        executables: list[Executable] = []

        for name in KNOWN_EXECUTABLES:

            path = which(name)

            if path is None:
                continue

            executables.append(
                Executable(
                    name=name,
                    path=path,
                )
            )

        return ExecutableInventory(
            executables=executables,
        )
