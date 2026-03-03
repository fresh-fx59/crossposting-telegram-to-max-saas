"""Validation checks for Telegram bot command parser helpers."""

import ast
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "backend/app/api/telegram_bot_commands.py"
MODULE_AST = ast.parse(MODULE_PATH.read_text())

PARSE_COMMAND_NODE = None
for node in MODULE_AST.body:
    if isinstance(node, ast.FunctionDef) and node.name == "_parse_command":
        PARSE_COMMAND_NODE = node
        break

if PARSE_COMMAND_NODE is None:
    raise RuntimeError("Failed to locate _parse_command function")

EXTRACTED_MODULE = ast.Module(body=[PARSE_COMMAND_NODE], type_ignores=[])
ast.fix_missing_locations(EXTRACTED_MODULE)
NAMESPACE: dict[str, object] = {}
exec(compile(EXTRACTED_MODULE, str(MODULE_PATH), "exec"), NAMESPACE)  # noqa: S102
parse_command = NAMESPACE["_parse_command"]


def test_parse_command_without_arg() -> None:
    command, arg = parse_command("/status")
    assert command == "/status"
    assert arg is None


def test_parse_command_with_bot_mention_and_arg() -> None:
    command, arg = parse_command("/pay@iron_lady_assistant_bot annual")
    assert command == "/pay"
    assert arg == "annual"


if __name__ == "__main__":
    test_parse_command_without_arg()
    test_parse_command_with_bot_mention_and_arg()
    print("telegram_bot_commands_validation_ok")
