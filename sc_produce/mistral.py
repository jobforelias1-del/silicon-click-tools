"""A thin, testable client for the Mistral chat-completions API.

This is the only module in ``sc_produce`` that talks to the network. It is kept
deliberately small: build a request, post it, and pull the assistant's text back
out of the response. Every failure mode -- a dropped connection, a non-2xx
status, or an unexpected JSON shape -- is funnelled into a single
:class:`~sc_produce.errors.MistralAPIError` so callers (and the ``compose``
command) present one readable message instead of a raw traceback.

Testability hinges on the ``session`` injection point: :class:`MistralClient`
posts through a :class:`requests.Session` (or anything exposing a compatible
``.post``), so tests can pass a tiny fake that returns a canned response with no
real HTTP and without the ``responses`` library.
"""

from __future__ import annotations

import os

import requests

from .errors import MistralAPIError

#: The default Mistral model used for authoring briefs.
DEFAULT_MODEL = "mistral-large-latest"

#: The default chat-completions endpoint.
DEFAULT_BASE_URL = "https://api.mistral.ai/v1/chat/completions"

#: The default per-request timeout, in seconds. Authoring a full arrangement is
#: a large generation, so this is generous.
DEFAULT_TIMEOUT = 120.0


class MistralClient:
    """A minimal client for Mistral's chat-completions endpoint.

    Attributes:
        api_key: The Mistral API key sent as a bearer token.
        model: The model name posted with every request.
        base_url: The chat-completions URL to POST to.
        timeout: Per-request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        session: requests.Session | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialise the client.

        Args:
            api_key: The Mistral API key.
            model: The model to request (default :data:`DEFAULT_MODEL`).
            base_url: The endpoint to POST to (default :data:`DEFAULT_BASE_URL`).
            session: A pre-built :class:`requests.Session` (or compatible object
                exposing ``.post``); a fresh session is created when omitted.
                This is the seam the test suite injects a fake through.
            timeout: Per-request timeout in seconds (default
                :data:`DEFAULT_TIMEOUT`).
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self._session = session or requests.Session()

    @classmethod
    def from_env(cls, **kwargs: object) -> MistralClient:
        """Build a client from the ``MISTRAL_API_KEY`` environment variable.

        Args:
            **kwargs: Forwarded to :meth:`__init__` (e.g. ``model``,
                ``base_url``, ``session``, ``timeout``).

        Returns:
            A configured :class:`MistralClient`.

        Raises:
            MistralAPIError: If ``MISTRAL_API_KEY`` is unset or empty.
        """
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise MistralAPIError("MISTRAL_API_KEY is not set")
        return cls(api_key, **kwargs)  # type: ignore[arg-type]

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        """Send a single prompt and return the assistant's text reply.

        Args:
            prompt: The user prompt (typically a rendered authoring brief).
            system: An optional system message prepended to the conversation.

        Returns:
            The assistant message content as a string.

        Raises:
            MistralAPIError: If the network call fails, the response status is
                not 2xx, or the response JSON does not have the expected shape.
        """
        messages: list[dict[str, str]] = []
        if system is not None:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": self.model, "messages": messages}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = self._session.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise MistralAPIError(f"Mistral request failed: {exc}") from exc

        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            body = (getattr(resp, "text", "") or "").strip()
            detail = f": {body}" if body else ""
            raise MistralAPIError(f"Mistral returned an error status: {exc}{detail}") from exc

        try:
            return resp.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise MistralAPIError("unexpected Mistral response shape") from exc
