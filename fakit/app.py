from .api import create_api
from fastapi import FastAPI
from dataclasses import dataclass


@dataclass
class FakitApp:
    api: FastAPI
    name: str


def create_app(name: str):
    return FakitApp(api=create_api(is_dev=True), name=name)
