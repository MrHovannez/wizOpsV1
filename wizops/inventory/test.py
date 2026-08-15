from wizops.inventory.coordinator import InventoryCoordinator
from wizops.platform.linux.linux_platform import LinuxPlatform


def main():

    inventory = InventoryCoordinator(
        LinuxPlatform()
    ).snapshot()

    print(inventory)

    print()
    print("Executables")
    print("===========")

    if not inventory.executables.executables:
        print("No executables discovered.")
    else:
        for executable in inventory.executables.executables:
            print(f"- {executable.name}")
            print(f"  {executable.path}")


if __name__ == "__main__":
    main()
