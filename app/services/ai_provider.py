

import os
import json
import logging
import httpx

logger = logging.getLogger(__name__)

# ── API endpoints & model IDs ────────────────────────────────────────────────
GEMINI_MODEL    = "gemini-2.5-flash"
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

GROQ_MODEL    = "llama-3.1-8b-instant"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


# ── Shared prompt template ───────────────────────────────────────────────────
def _build_system_prompt(max_beats: int, style: str, input_text: str) -> str:
    return f"""You are an expert Storyboard Director and Senior Concept Artist. 
Your task is to deconstruct a narrative into exactly {max_beats} key 'Visual Beats' and translate them into professional-grade image generation prompts.

### OUTPUT FORMAT:
Return ONLY a valid JSON array. No markdown, no preamble. 
Shape:
[
  {{
    "original_text": "...",
    "image_prompt": "..."
  }}
]

### RULES FOR VISUAL BEATS:
1. SEGMENTATION: Identify the 'emotional pivot' of the story. Group sentences that share the same location/action. Ensure the sequence tells the full story from beginning to end.
2. VERBATIM: The 'original_text' field must contain the exact words from the source.
3. PROMPT ARCHITECTURE: Each 'image_prompt' must follow this structure:
   - [Subject & Action]: Detailed description of characters and movement.
   - [Environment]: Specific setting details, textures, and atmospheric depth.
   - [Cinematography]: Camera angle (e.g., Wide Shot, Low Angle), Lighting (e.g., Volumetric, Golden Hour), and Lens (e.g., 35mm, Macro).
   - [Global Style]: Apply the style '{style}' consistently to every prompt.

### PROMPT CONSTRAINTS:
- Avoid abstract words (e.g., 'efficiency', 'future'). Instead, use visual substitutes (e.g., 'blue fiber-optic lines', 'shimmering glass panels').
- Maintain character consistency: If a person is described, use the same physical traits in every beat.
- No 'nested' JSON; just the flat array.

Input Narrative: {input_text}"""


class AIProvider:
    """
    LLM gateway with automatic primary to fallback switching.

  
    """

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.groq_key   = os.getenv("GROQ_API_KEY", "")
        # Tracks every provider attempted in a single request lifecycle.
        self._chain: list[str] = []

    # ── Public interface ─────────────────────────────────────────────────────

    async def segment_into_beats(
        self, narrative: str, style: str, max_beats: int = 6
    ) -> tuple[list[dict], list[str]]:
        """
        Returns (beats, provider_chain).
        beats = [{"original_text": ..., "image_prompt": ...}, ...]
        provider_chain = ordered list of providers tried.
        """
        self._chain = []
        system_prompt = _build_system_prompt(max_beats, style, narrative)
        user_message  = f"Narrative:\n\n{narrative}"

        # ── Attempt 1: Gemini ────────────────────────────────────────────────
        if self.gemini_key:
            try:
                beats = await self._call_gemini(system_prompt, user_message)
                self._chain.append("gemini-1.5-flash")
                return beats, self._chain
            except Exception as exc:
                # Log the reason and proceed to fallback — never crash here.
                logger.warning("Gemini failed (%s). Falling back to Groq.", exc)
                self._chain.append(f"gemini-failed:{type(exc).__name__}")
        else:
            logger.info("GEMINI_API_KEY not set; skipping primary provider.")

        # ── Attempt 2: Groq / Llama-3 (fallback) ────────────────────────────
        if self.groq_key:
            try:
                beats = await self._call_groq(system_prompt, user_message)
                self._chain.append("groq-llama3-8b")
                return beats, self._chain
            except Exception as exc:
                logger.error("Groq also failed (%s). No providers available.", exc)
                self._chain.append(f"groq-failed:{type(exc).__name__}")
        else:
            logger.info("GROQ_API_KEY not set; skipping fallback provider.")

        raise RuntimeError(
            "All LLM providers failed. Check API keys and rate limits. "
            f"Provider chain: {self._chain}"
        )

    # ── Gemini implementation ────────────────────────────────────────────────

    async def _call_gemini(self, system_prompt: str, user_message: str) -> list[dict]:
        """
        Calls the Gemini REST API (no SDK dependency — plain httpx).
        Gemini uses a 'contents' array; system instructions go in a separate field.
        """
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_message}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048,
            },
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                GEMINI_ENDPOINT,
                params={"key": self.gemini_key},
                json=payload,
            )

        # Surface HTTP errors as exceptions so the fallback logic triggers.
        if resp.status_code == 429:
            raise RuntimeError("Gemini rate limit exceeded (HTTP 429).")
        resp.raise_for_status()

        raw_text = (
            resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        )
        return self._parse_beats(raw_text)

    # ── Groq implementation ──────────────────────────────────────────────────

    async def _call_groq(self, system_prompt: str, user_message: str) -> list[dict]:
        """
        Calls the Groq API — it is OpenAI-compatible, making the client trivial.
        """
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(GROQ_ENDPOINT, headers=headers, json=payload)

        if resp.status_code == 429:
            raise RuntimeError("Groq rate limit exceeded (HTTP 429).")
        resp.raise_for_status()

        raw_text = resp.json()["choices"][0]["message"]["content"].strip()
        return self._parse_beats(raw_text)

    # ── JSON parsing ─────────────────────────────────────────────────────────

    @staticmethod
    def _parse_beats(raw_text: str) -> list[dict]:
        """
        Safely parse the LLM output into a list of beat dicts.
        Strips any accidental markdown fences before parsing.
        """
        cleaned = raw_text.strip()
        # Strip ```json ... ``` fences if the model ignores our instruction.
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        beats: list[dict] = json.loads(cleaned)

        # Validate minimal structure.
        for b in beats:
            if "original_text" not in b or "image_prompt" not in b:
                raise ValueError(f"Malformed beat object: {b}")

        return beats
