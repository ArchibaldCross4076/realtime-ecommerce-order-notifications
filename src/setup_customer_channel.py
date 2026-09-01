from __future__ import annotations

import argparse
import json

from infrai_realtime import InfraiRealtime


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a customer order channel and issue its browser token")
    parser.add_argument("customer_id")
    args = parser.parse_args()

    channel = f"customer:{args.customer_id}:orders"
    client = InfraiRealtime()
    client.create_channel(channel)
    token = client.issue_token(client_id=args.customer_id, channel=channel)
    print(json.dumps({"channel": channel, "token": token}, indent=2))


if __name__ == "__main__":
    main()
