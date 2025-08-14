from __future__ import annotations

import asyncio
import os
import logging
from dataclasses import dataclass, field
from typing import AsyncGenerator, Iterable, List, Mapping, Optional

from langchain_core.caches import BaseCache as _LCBaseCache  # type: ignore
from langchain_core.callbacks import Callbacks as _LCCallbacks  # type: ignore
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class LLMConfig:
    """Configuration for AsyncLLMService."""
    model: str = "gemma3:4b"
    base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    temperature: float = 0.2
    max_retries: int = 3
    retry_backoff: float = 0.5  # seconds
    extra_kwargs: Mapping[str, object] = field(default_factory=dict)


class AsyncLLMService:
    """Asynchronous LLM service with retries, streaming, and single-shot completions."""

    def __init__(self, system_prompt: Optional[str] = None, config: Optional[LLMConfig] = None) -> None:
        self.config = config or LLMConfig()
        self.system_prompt = system_prompt or (
            "You are Saba, a Jarvis-like AI assistant. Be direct, proactive, and conversational. "
            "Reply in 1–2 short sentences with natural, friendly responses. "
            "Do not include risk assessments, next steps, or internal analysis in your responses. "
            "Just provide helpful, conversational replies."
        )

        self._llm = self._init_llm()

    def _init_llm(self) -> ChatOllama:
        """Initialize ChatOllama with safe model rebuild handling."""
        try:
            return ChatOllama(
                model=self.config.model,
                base_url=self.config.base_url,
                temperature=self.config.temperature,
                **self.config.extra_kwargs,
            )
        except Exception as e:
            msg = str(e)
            if "not fully defined" in msg or "model_rebuild" in msg or "BaseCache" in msg:
                logger.warning("Rebuilding ChatOllama model schema...")

                # Ensure BaseCache & Callbacks are in ChatOllama's module namespace
                import importlib
                from langchain_core.caches import BaseCache
                from langchain_core.callbacks import Callbacks

                chatollama_mod = importlib.import_module(ChatOllama.__module__)
                setattr(chatollama_mod, "BaseCache", BaseCache)
                setattr(chatollama_mod, "Callbacks", Callbacks)

                try:
                    ChatOllama.model_rebuild(force=True)
                except TypeError:
                    ChatOllama.model_rebuild()

                return ChatOllama(
                    model=self.config.model,
                    base_url=self.config.base_url,
                    temperature=self.config.temperature,
                    **self.config.extra_kwargs,
                )

            raise RuntimeError(
                f"Failed to initialize ChatOllama: {e}. Ensure Ollama is running at {self.config.base_url} "
                f"and model '{self.config.model}' is available."
            ) from e


    def update_system_prompt(self, system_prompt: str) -> None:
        """Update the system prompt for future requests."""
        self.system_prompt = system_prompt or self.system_prompt

    async def acomplete(
        self,
        prompt: str,
        *,
        history: Optional[Iterable[Mapping[str, str]]] = None,
        **kwargs,
    ) -> str:
        """Generate a single-shot completion asynchronously with retries."""
        messages = self._compose_messages(prompt, history)

        async def _call():
            result = await self._llm.ainvoke(messages, **kwargs)
            return getattr(result, "content", str(result))

        return await self._retry(_call, action="completion")

    async def astream(
        self,
        prompt: str,
        *,
        history: Optional[Iterable[Mapping[str, str]]] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream the model's response tokens asynchronously with retries."""
        messages = self._compose_messages(prompt, history)

        async def _gen():
            async for chunk in self._llm.astream(messages, **kwargs):
                text = getattr(chunk, "content", None)
                if text:
                    yield text

        # Wrapping async generator in retry
        for attempt in range(self.config.max_retries):
            try:
                async for token in _gen():
                    yield token
                break
            except Exception as e:
                if not self._should_retry(e, attempt):
                    self._raise_llm_error(e)
                delay = self.config.retry_backoff * (2**attempt)
                logger.warning(f"Retrying stream in {delay:.2f}s after error: {e}")
                await asyncio.sleep(delay)

    def _compose_messages(
        self,
        prompt: str,
        history: Optional[Iterable[Mapping[str, str]]],
    ) -> List[object]:
        """Build LangChain messages with deduplication of system prompts."""
        messages: List[object] = []
        history_msgs = self._convert_history(history) if history else []
        if not any(isinstance(m, SystemMessage) for m in history_msgs):
            messages.append(SystemMessage(self.system_prompt))
        messages.extend(history_msgs)
        messages.append(HumanMessage(prompt))
        return messages

    @staticmethod
    def _convert_history(history: Iterable[Mapping[str, str]]) -> List[object]:
        """Convert role/content dicts to LangChain message objects."""
        role_map = {
            "system": SystemMessage,
            "user": HumanMessage,
            "assistant": AIMessage,
        }
        converted: List[object] = []
        for item in history:
            role = (item.get("role") or "").lower()
            content = item.get("content") or ""
            if content and role in role_map:
                converted.append(role_map[role](content))
        return converted

    async def _retry(self, func, *, action: str):
        """Retry wrapper for non-streaming calls."""
        for attempt in range(self.config.max_retries):
            try:
                return await func()
            except Exception as e:
                if not self._should_retry(e, attempt):
                    self._raise_llm_error(e)
                delay = self.config.retry_backoff * (2**attempt)
                logger.warning(f"Retrying {action} in {delay:.2f}s after error: {e}")
                await asyncio.sleep(delay)
        raise RuntimeError(f"{action.capitalize()} failed after {self.config.max_retries} retries.")

    def _should_retry(self, e: Exception, attempt: int) -> bool:
        """Decide whether to retry based on error type and attempt count."""
        if attempt >= self.config.max_retries - 1:
            return False
        transient_errors = ("Connection refused", "Timeout", "Temporary failure")
        return any(err.lower() in str(e).lower() for err in transient_errors)

    def _raise_llm_error(self, e: Exception) -> None:
        raise RuntimeError(
            f"LLM request failed: {e}. Verify Ollama is running at {self.config.base_url} "
            f"and model '{self.config.model}' is available."
        ) from e
