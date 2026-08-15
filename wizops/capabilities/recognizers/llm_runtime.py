from __future__ import annotations

from wizops.inventory.models import (
    Capability,
    CapabilityImplementation,
    CapabilityKind,
    InventorySnapshot,
)

from ..recognizer import CapabilityRecognizer


IMPLEMENTATIONS = {
    "ollama": "Ollama",
    "llama-server": "llama.cpp",
    "vllm": "vLLM",
}


class LlmRuntimeRecognizer(CapabilityRecognizer):

    def recognize(
        self,
        inventory: InventorySnapshot,
    ) -> Capability | None:

        implementations: list[CapabilityImplementation] = []

        for executable in inventory.executables.executables:

            implementation = IMPLEMENTATIONS.get(
                executable.name,
            )

            if implementation is None:
                continue

            implementations.append(
                CapabilityImplementation(
                    name=implementation,
                )
            )

        if not implementations:
            return None

        return Capability(
            kind=CapabilityKind.LLM_RUNTIME,
            implementations=implementations,
        )
