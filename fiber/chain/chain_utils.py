import json
from pathlib import Path
from typing import Any

from substrateinterface import Keypair

from fiber import SubstrateInterface
from fiber.logging_utils import get_logger

logger = get_logger(__name__)


def format_error_message(error_message: dict | None) -> str:
    err_type, err_name, err_description = (
        "UnknownType",
        "UnknownError",
        "Unknown Description",
    )
    if isinstance(error_message, dict):
        err_type = error_message.get("type", err_type)
        err_name = error_message.get("name", err_name)
        err_description = error_message.get("docs", [err_description])[0]
    return f"substrate returned `{err_name} ({err_type})` error. Description: `{err_description}`"


def get_hotkey_file_path(wallet_name: str, hotkey_name: str) -> Path:
    file_path = Path.home() / ".bittensor" / "wallets" / wallet_name / "hotkeys" / hotkey_name
    return file_path


def get_coldkeypub_file_path(wallet_name: str) -> Path:
    file_path = Path.home() / ".bittensor" / "wallets" / wallet_name / "coldkeypub.txt"
    return file_path


def load_coldkeypub_keypair(wallet_name: str) -> Keypair:
    file_path = get_coldkeypub_file_path(wallet_name)
    try:
        with open(file_path, "r") as file:
            keypair_data = json.load(file)
        keypair = Keypair(ss58_address=keypair_data["ss58Address"])
        logger.info(f"Loaded keypair from {file_path}")
        return keypair
    except Exception as e:
        raise ValueError(f"Failed to load keypair: {str(e)}")


def load_hotkey_keypair(wallet_name: str, hotkey_name: str) -> Keypair:
    file_path = get_hotkey_file_path(wallet_name, hotkey_name)
    try:
        with open(file_path, "r") as file:
            keypair_data = json.load(file)
        keypair = Keypair.create_from_seed(keypair_data["secretSeed"])
        logger.info(f"Loaded keypair from {file_path}")
        return keypair
    except Exception as e:
        raise ValueError(f"Failed to load keypair: {str(e)}")


def sign_message(keypair: Keypair, message: str | None) -> str | None:
    if message is None:
        return None
    return f"0x{keypair.sign(message).hex()}"


def query_substrate(
    substrate: SubstrateInterface,
    module: str,
    method: str,
    params: list[Any],
    return_value: bool = True,
    block: int | None = None,
) -> tuple[SubstrateInterface, Any]:
    try:
        block_hash = substrate.get_block_hash(block) if block is not None else None
        query_result = substrate.query(module, method, params, block_hash=block_hash)

        return_val = query_result.value if return_value else query_result

        return substrate, return_val
    except Exception as e:
        logger.debug(f"Substrate query failed with error: {e}. Reconnecting and retrying.")

        substrate = SubstrateInterface(url=substrate.url)

        block_hash = substrate.get_block_hash(block) if block is not None else None
        query_result = substrate.query(module, method, params, block_hash=block_hash)

        return_val = query_result.value if return_value else query_result

        return substrate, return_val
