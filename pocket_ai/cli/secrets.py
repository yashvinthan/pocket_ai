from __future__ import annotations

import argparse

from pocket_ai.core.secrets_manager import secrets_manager


def cmd_set(args):
    secrets_manager.set_secret(args.name, args.value)
    print(f"Stored secret: {args.name}")


def cmd_get(args):
    value = secrets_manager.get_secret(args.name)
    if value is None:
        print("Secret not found")
    else:
        print(value)


def cmd_list(_args):
    for key in secrets_manager.list_secrets():
        print(f"- {key}")


def cmd_delete(args):
    secrets_manager.delete_secret(args.name)
    print(f"Deleted secret: {args.name}")


def main():
    parser = argparse.ArgumentParser(description="POCKET-AI secrets helper")
    sub = parser.add_subparsers(dest="command", required=True)

    set_cmd = sub.add_parser("set", help="Store/update a secret")
    set_cmd.add_argument("name")
    set_cmd.add_argument("value")
    set_cmd.set_defaults(func=cmd_set)

    get_cmd = sub.add_parser("get", help="Retrieve a secret")
    get_cmd.add_argument("name")
    get_cmd.set_defaults(func=cmd_get)

    list_cmd = sub.add_parser("list", help="List stored secrets")
    list_cmd.set_defaults(func=cmd_list)

    del_cmd = sub.add_parser("delete", help="Delete a secret")
    del_cmd.add_argument("name")
    del_cmd.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()


