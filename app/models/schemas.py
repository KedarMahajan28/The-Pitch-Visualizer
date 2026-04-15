
from pydantic import BaseModel, Field
from typing import Literal, Optional


# ── Supported visual styles ──────────────────────────────────────────────────
StyleType = Literal[
    "Cinematic",
    "3D Render",
    "Flat Illustration",
    "Watercolor",
    "Pixel Art",
    "Photorealistic",
    "Cyberpunk",
    "Minimalist Tech"
]


class StoryboardRequest(BaseModel):
    """Payload the client sends to /generate-storyboard."""
    narrative: str = Field(
        ...,
        min_length=20,
        max_length=3000,
        description="The paragraph/narrative to visualize.",
    )
    style: StyleType = Field(
        default="Cinematic",
        description="Visual style applied uniformly to every generated image.",
    )


class Scene(BaseModel):
    """A single Visual Beat — one card in the storyboard grid."""
    beat_index: int = Field(..., description="0-based position in the storyboard.")
    original_text: str = Field(..., description="The raw narrative segment.")
    enhanced_prompt: str = Field(..., description="Style-injected image prompt.")
    image_data: Optional[str] = Field(
        None,
        description="Base64-encoded PNG or a public image URL.",
    )
    image_format: Literal["base64", "url", "placeholder"] = "base64"
    provider_used: str = Field(
        ...,
        description="Which LLM generated the prompt (gemini / groq-llama3 / fallback).",
    )


class StoryboardResponse(BaseModel):
    """Full storyboard returned to the client."""
    style: str
    total_beats: int
    scenes: list[Scene]
    provider_chain: list[str] = Field(
        description="Ordered list of providers attempted during this request."
    )
