import netaddr
from async_substrate_interface import SubstrateInterface
from scalecodec.utils.ss58 import ss58_encode
from tenacity import retry, stop_after_attempt, wait_exponential

from fiber import constants as fcst
from fiber.chain import chain_utils as chain_utils
from fiber.chain import models
from fiber.chain.interface import get_substrate
from fiber.logging_utils import get_logger

logger = get_logger(__name__)


def _ss58_encode(address: list[int] | list[list[int]], ss58_format: int = fcst.SS58_FORMAT) -> str:
    if not isinstance(address[0], int):
        address = address[0]
    return ss58_encode(bytes(address).hex(), ss58_format)


def _normalise_u16_float(x: int) -> float:
    return float(x) / float(fcst.U16_MAX)


def _rao_to_tao(rao: float | int) -> float:
    return int(rao) / 10**9


def _get_node_from_neuron_info(neuron_info_decoded: dict) -> models.Node:
    neuron_info_copy = neuron_info_decoded.copy()
    stake_dict = {_ss58_encode(coldkey, fcst.SS58_FORMAT): _rao_to_tao(stake) for coldkey, stake in neuron_info_copy["stake"]}
    return models.Node(
        hotkey=_ss58_encode(neuron_info_copy["hotkey"], fcst.SS58_FORMAT),
        coldkey=_ss58_encode(neuron_info_copy["coldkey"], fcst.SS58_FORMAT),
        node_id=neuron_info_copy["uid"],
        netuid=neuron_info_copy["netuid"],
        stake=sum(stake_dict.values()),
        incentive=neuron_info_copy["incentive"],
        trust=_normalise_u16_float(neuron_info_copy["trust"]),
        vtrust=_normalise_u16_float(neuron_info_copy["validator_trust"]),
        last_updated=neuron_info_copy["last_update"],
        ip=str(netaddr.IPAddress(int(neuron_info_copy["axon_info"]["ip"]))),
        ip_type=neuron_info_copy["axon_info"]["ip_type"],
        port=neuron_info_copy["axon_info"]["port"],
        protocol=neuron_info_copy["axon_info"]["protocol"],
    )


def _get_nodes_from_neuron_infos(neuron_infos: list[dict]) -> list[models.Node]:
    nodes = []
    for decoded_neuron in neuron_infos:
        node = _get_node_from_neuron_info(decoded_neuron)
        if node is not None:
            nodes.append(node)
    return nodes


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
def _get_nodes_for_uid(substrate: SubstrateInterface, netuid: int, block: int | None = None):

    if block is not None:
        block_hash = substrate.get_block_hash(block)
    else:
        block_hash = None

    with substrate as si:
        neuron_infos = si.runtime_call(
            api="NeuronInfoRuntimeApi",
            method="get_neurons_lite",
            params=[netuid],
            block_hash=block_hash,
        ).value

    return _get_nodes_from_neuron_infos(neuron_infos)


def get_nodes_for_netuid(substrate: SubstrateInterface, netuid: int, block: int | None = None) -> list[models.Node]:
    # Make a new substrate connection for this. Could I add this to the _get_nodes_for_uid function
    # and do the try: except: reraise pattern?
    substrate = get_substrate(subtensor_address=substrate.url)
    return _get_nodes_for_uid(substrate, netuid, block)
