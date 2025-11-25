from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

from pocket_ai.core.storage import DataLifecycleManager


def main(argv: Optional[list[str]] = None):
    parser = argparse.ArgumentParser(description="Pocket AI export helper")
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List available encrypted exports")
    list_cmd.set_defaults(func=_handle_list)

    decrypt_cmd = sub.add_parser("decrypt", help="Decrypt an export bundle")
    decrypt_cmd.add_argument("key", help="Export identifier")
    decrypt_cmd.add_argument(
        "--out",
        dest="output",
        help="Destination zip path; defaults to <key>.zip",
    )
    decrypt_cmd.set_defaults(func=_handle_decrypt)

    args = parser.parse_args(argv)
    manager = DataLifecycleManager()
    return args.func(manager, args)


def _handle_list(manager: DataLifecycleManager, args):
    exports = manager.list_keys("user_exports")
    if not exports:
        print("No exports found.")
        return 0
    for key in exports:
        print(key)
    return 0


def _handle_decrypt(manager: DataLifecycleManager, args):
    bundle = manager.retrieve("user_exports", args.key)
    if not bundle:
        print("Export not found.", file=sys.stderr)
        return 1

    output = Path(args.output or f"{args.key}.zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w") as archive:
        archive.writestr("export.json", json.dumps(bundle, indent=2))

    print(f"Wrote decrypted export to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

