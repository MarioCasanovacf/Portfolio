"""Smoke tests for the synthetic data generator."""

import importlib

import pytest


@pytest.mark.unit
def test_data_generator_importable() -> None:
    module = importlib.import_module("data_generator")
    assert module is not None
