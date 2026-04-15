

import os
import io
import base64
import logging
import asyncio
from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)

HF_API_TOKEN  = os.getenv("HF_API_TOKEN", "")
HF_MODEL      = "stabilityai/stable-diffusion-xl-base-1.0"


async def generate_image(prompt: str, negative_prompt: str = "") -> tuple[str, str]:
    """
    Generate an image for the given prompt.

    Returns:
        (image_data, format) where format is "base64", "url", or "placeholder".
    """
    if not HF_API_TOKEN:
        logger.warning("HF_API_TOKEN not set. Returning placeholder.")
        return _placeholder_svg(prompt), "placeholder"

    try:
        client = InferenceClient(
            provider="nscale",
            api_key=HF_API_TOKEN,
        )

        logger.info("Generating image with Hugging Face InferenceClient...")
        # run synchronous call in a thread to prevent blocking
        image = await asyncio.to_thread(
            client.text_to_image,
            prompt,
            negative_prompt=negative_prompt,
            model=HF_MODEL,
        )

        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return image_b64, "base64"

    except Exception as exc:
        logger.error("Image generation failed: %s", exc)
        return _placeholder_svg(prompt), "placeholder"


def _placeholder_svg(prompt: str) -> str:
    """
    Returns a base64-encoded SVG placeholder so the UI always has something
    to render, even when image generation is unavailable.
    """
    label = (prompt[:60] + "…") if len(prompt) > 60 else prompt
    label = label.replace('"', "'")  # Escape for SVG attribute safety
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512"
  viewBox="0 0 512 512">
  <rect width="512" height="512" fill="#1a1a2e"/>
  <rect x="20" y="20" width="472" height="472" rx="8"
        fill="none" stroke="#4a4a8a" stroke-width="2" stroke-dasharray="8 4"/>
  <text x="256" y="220" text-anchor="middle" fill="#6a6aaa"
        font-family="monospace" font-size="48">🎬</text>
  <text x="256" y="270" text-anchor="middle" fill="#8a8aca"
        font-family="monospace" font-size="13">[ Image Placeholder ]</text>
  <foreignObject x="40" y="300" width="432" height="160">
    <div xmlns="http://www.w3.org/1999/xhtml"
         style="color:#6a6aaa;font-size:11px;font-family:monospace;
                text-align:center;padding:8px;word-wrap:break-word;">
      {label}
    </div>
  </foreignObject>
</svg>"""
    return base64.b64encode(svg.encode()).decode("utf-8")
