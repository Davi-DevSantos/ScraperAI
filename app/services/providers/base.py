from typing import Protocol


class AIProvider(Protocol):
    """Contrato que todo provedor de IA deve implementar."""

    name: str

    def complete(
        self,
        system: str,
        user: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str | None:
        """Executa completion e retorna string (JSON) ou None."""
        ...
