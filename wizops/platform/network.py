from __future__ import annotations

from socket import AF_INET
from socket import AF_INET6

import psutil

from wizops.inventory.models import NetworkInterface
from wizops.inventory.models import NetworkInventory


class NetworkProvider:

    def snapshot(self) -> NetworkInventory:

        interfaces: list[NetworkInterface] = []

        stats = psutil.net_if_stats()

        for name, addrs in psutil.net_if_addrs().items():

            ipv4 = []
            ipv6 = []
            mac = None

            for addr in addrs:

                if addr.family == AF_INET:
                    ipv4.append(addr.address)

                elif addr.family == AF_INET6:
                    ipv6.append(addr.address.split("%")[0])

                elif addr.family == psutil.AF_LINK:
                    mac = addr.address

            state = "unknown"

            if name in stats:
                state = "up" if stats[name].isup else "down"

            interfaces.append(
                NetworkInterface(
                    name=name,
                    kind=self._classify(name),
                    state=state,
                    mac_address=mac,
                    ipv4=ipv4,
                    ipv6=ipv6,
                )
            )

        return NetworkInventory(
            interfaces=interfaces,
        )

    def _classify(self, interface: str) -> str:

        name = interface.lower()

        if name == "lo":
            return "loopback"

        if (
            name.startswith("eth")
            or name.startswith("en")
        ):
            return "ethernet"

        if (
            name.startswith("wl")
            or name.startswith("wifi")
        ):
            return "wifi"

        if (
            name.startswith("docker")
            or name.startswith("br")
        ):
            return "bridge"

        if (
            name.startswith("vir")
            or name.startswith("veth")
        ):
            return "virtual"

        if name.startswith("tun"):
            return "tunnel"

        if name.startswith("bond"):
            return "bond"

        if "." in name:
            return "vlan"

        return "unknown"
