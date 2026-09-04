from typing import Protocol


class AIProvider(Protocol):

    name: str

    def complete(
        self,
        system: str,
        user: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str | None:
        ...
