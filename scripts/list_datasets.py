from edgeforge.data.registry import DATASETS


def main() -> None:
    for d in DATASETS:
        order_ids = "yes" if d.order_ids else "no"
        print(f"{d.phase:7}  {d.key:28}  order_ids={order_ids:3}  {d.access}")
        print(f"          {d.url}")


if __name__ == "__main__":
    main()
