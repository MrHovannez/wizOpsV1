from wizops.capabilities.coordinator import CapabilityCoordinator
from wizops.inventory.coordinator import InventoryCoordinator
from wizops.platform.linux.linux_platform import LinuxPlatform


def main():

    inventory = InventoryCoordinator(
        LinuxPlatform(),
    ).snapshot()

    capabilities = CapabilityCoordinator().recognize(
        inventory,
    )

    print()
    print("Capabilities")
    print("============")
    print()

    if not capabilities.capabilities:
        print("No capabilities discovered.")
        return

    for capability in capabilities.capabilities:

        print(f"• {capability.kind.value.replace('_', ' ').title()}")

        for implementation in capability.implementations:
            print(f"    - {implementation.name}")

        print()


if __name__ == "__main__":
    main()
