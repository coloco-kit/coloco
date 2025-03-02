from contextlib import asynccontextmanager
from asyncio import iscoroutinefunction
from fastapi import FastAPI

lifespan_wrappers = []


@asynccontextmanager
async def execute_lifespan(app: FastAPI):
    contexts = []

    for lifespan_handler in lifespan_wrappers:
        generator = lifespan_handler(app)
        contexts.append(generator)
        if hasattr(generator, "__aenter__"):
            await generator.__aenter__()
        else:
            next(generator)

    yield

    while contexts and (generator := contexts.pop()):
        if hasattr(generator, "__aexit__"):
            await generator.__aexit__(None, None, None)
        else:
            next(generator)


def register_lifespan(handler):
    lifespan_wrappers.append(handler)
