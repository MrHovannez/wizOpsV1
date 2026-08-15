from __future__ import annotations

from .recognizers.gpu import GpuComputeRecognizer
from .recognizers.remote_access import RemoteAccessRecognizer
from .recognizers.package_manager import PackageManagerRecognizer
from .recognizers.scheduler import SchedulerRecognizer
from .recognizers.container_runtime import ContainerRuntimeRecognizer
from .recognizer import CapabilityRecognizer
from .recognizers.llm_runtime import LlmRuntimeRecognizer

def recognizers() -> list[CapabilityRecognizer]:
    return [
        GpuComputeRecognizer(),
        PackageManagerRecognizer(),
        RemoteAccessRecognizer(),
        SchedulerRecognizer(),
        ContainerRuntimeRecognizer(),
        LlmRuntimeRecognizer(),
    ]

