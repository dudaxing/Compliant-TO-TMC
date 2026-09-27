"""v4 kernel-repair launch entry; the private worker mode is reserved for the coordinator."""
from contact_c2_launch_v4 import cli


if __name__ == "__main__":
    raise SystemExit(cli())
