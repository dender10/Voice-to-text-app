"""OpenAI GPT formatter for text cleanup."""

import os
from typing import Optional


class GPTFormatter:
    """Formats text using OpenAI GPT API."""

    def __init__(
        self,
        enabled: bool = True,
        model: str = "gpt-4o-mini",
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
    ):
        self.enabled = enabled
        self.model = model
        self.max_retries = max_retries
        self.system_prompt = system_prompt or (
            "Fix grammar and punctuation. Capitalize appropriately. "
            "Maintain meaning. Return only corrected text."
        )
        self._client = None

    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()
        return self._client

    def format(self, text: str) -> str:
        """
        Format text using OpenAI GPT.

        Args:
            text: Raw transcribed text

        Returns:
            Formatted text (or original if formatting fails/disabled)
        """
        if not text or not text.strip():
            return text

        if not self.enabled:
            return text

        # Check for API key
        if not os.environ.get("OPENAI_API_KEY"):
            print("Warning: OPENAI_API_KEY not set, skipping formatting")
            return text

        for attempt in range(self.max_retries):
            try:
                client = self._get_client()

                response = client.chat.completions.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": text}
                    ],
                )

                # Extract text from response
                if response.choices and len(response.choices) > 0:
                    formatted = response.choices[0].message.content.strip()
                    if formatted:
                        return formatted

            except Exception as e:
                print(f"OpenAI API error (attempt {attempt + 1}/{self.max_retries}): {e}")

        # Return original text if all retries failed
        return text

    def is_available(self) -> bool:
        """Check if GPT formatting is available."""
        return self.enabled and bool(os.environ.get("OPENAI_API_KEY"))
