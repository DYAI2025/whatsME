"""Placeholder for future persistence models."""


class ActivationRecord:
    """Represents a stored activation event in persistence layer."""

    def __init__(self, data: dict):
        self.data = data

    def as_dict(self) -> dict:
        return self.data
