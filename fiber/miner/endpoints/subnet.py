"""
THIS IS AN EXAMPLE FILE OF A SUBNET ENDPOINT!

PLEASE IMPLEMENT YOUR OWN :)
"""

from fastapi import Depends
from fastapi.routing import APIRouter
from pydantic import BaseModel

from fiber.miner.dependencies import blacklist_low_stake, verify_request


class ExampleSubnetRequest(BaseModel):
    hi: str


async def example_subnet_request(example_body: ExampleSubnetRequest):
    return {"status": "Example request received"}


def factory_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route(
        "/example-subnet-request",
        example_subnet_request,
        tags=["Example"],
        dependencies=[Depends(blacklist_low_stake), Depends(verify_request)],
        methods=["POST"],
    )
    return router
