from collections.abc import Sequence
from typing import Literal, Self

import psutil

from exo.shared.types.memory import Memory
from exo.shared.types.thunderbolt import ThunderboltIdentifier
from exo.utils.pydantic_ext import CamelCaseModel


class MemoryUsage(CamelCaseModel):
    ram_total: Memory
    ram_available: Memory
    swap_total: Memory
    swap_available: Memory
    gpu_vram_total: Memory = Memory.from_bytes(0)
    gpu_vram_available: Memory = Memory.from_bytes(0)

    @classmethod
    def from_bytes(
        cls,
        *,
        ram_total: int,
        ram_available: int,
        swap_total: int,
        swap_available: int,
        gpu_vram_total: int = 0,
        gpu_vram_available: int = 0,
    ) -> Self:
        return cls(
            ram_total=Memory.from_bytes(ram_total),
            ram_available=Memory.from_bytes(ram_available),
            swap_total=Memory.from_bytes(swap_total),
            swap_available=Memory.from_bytes(swap_available),
            gpu_vram_total=Memory.from_bytes(gpu_vram_total),
            gpu_vram_available=Memory.from_bytes(gpu_vram_available),
        )

    @classmethod
    def from_psutil(cls, *, override_memory: int | None) -> Self:
        import subprocess
        import sys

        vm = psutil.virtual_memory()
        sm = psutil.swap_memory()

        gpu_vram_total = 0
        gpu_vram_available = 0
        if sys.platform != "darwin":
            try:
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=memory.total,memory.free",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                for line in result.stdout.strip().splitlines():
                    parts = line.split(",")
                    gpu_vram_total += int(parts[0].strip()) * 1024 * 1024
                    gpu_vram_available += int(parts[1].strip()) * 1024 * 1024
            except Exception:
                pass

        return cls.from_bytes(
            ram_total=vm.total,
            ram_available=vm.available if override_memory is None else override_memory,
            swap_total=sm.total,
            swap_available=sm.free,
            gpu_vram_total=gpu_vram_total,
            gpu_vram_available=gpu_vram_available,
        )


class SystemPerformanceProfile(CamelCaseModel):
    # TODO: flops_fp16: float

    gpu_usage: float = 0.0
    temp: float = 0.0
    sys_power: float = 0.0
    pcpu_usage: float = 0.0
    ecpu_usage: float = 0.0


InterfaceType = Literal["wifi", "ethernet", "maybe_ethernet", "thunderbolt", "unknown"]


class NetworkInterfaceInfo(CamelCaseModel):
    name: str
    ip_address: str
    interface_type: InterfaceType = "unknown"


class NodeIdentity(CamelCaseModel):
    """Static and slow-changing node identification data."""

    model_id: str = "Unknown"
    chip_id: str = "Unknown"
    friendly_name: str = "Unknown"


class NodeNetworkInfo(CamelCaseModel):
    """Network interface information for a node."""

    interfaces: Sequence[NetworkInterfaceInfo] = []


class NodeThunderboltInfo(CamelCaseModel):
    """Thunderbolt interface identifiers for a node."""

    interfaces: Sequence[ThunderboltIdentifier] = []


class ThunderboltBridgeStatus(CamelCaseModel):
    """Whether the Thunderbolt Bridge network service is enabled on this node."""

    enabled: bool
    exists: bool
    service_name: str | None = None
