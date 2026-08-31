from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstracción de proveedores LLM. Fase 1: OpenAI. Fase posterior: otros."""

    @abstractmethod
    def generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
    ) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError


class AINotConfiguredError(RuntimeError):
    pass
