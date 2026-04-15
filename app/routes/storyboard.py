

import asyncio
import logging
import os

from fastapi import APIRouter, HTTPException

from app.models.schemas import Scene, StoryboardRequest, StoryboardResponse
from app.services.ai_provider import AIProvider
from app.services.image_service import generate_image
from app.services.prompt_factory import PromptFactory

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_BEATS = int(os.getenv("MAX_BEATS", "6"))


@router.get("/styles", summary="List available visual styles")
async def list_styles() -> dict:
    return {"styles": PromptFactory.available_styles()}


@router.post(
    "/generate-storyboard",
    response_model=StoryboardResponse,
    summary="Generate a visual storyboard from a narrative paragraph",
)
async def generate_storyboard(request: StoryboardRequest) -> StoryboardResponse:
    """
    Full pipeline:
      narrative text → Visual Beats (LLM) → styled prompts → images → JSON
    """
    provider = AIProvider()

    # ── Step 1: Segment narrative into Visual Beats ──────────────────────────
    try:
        beats, provider_chain = await provider.segment_into_beats(
            request.narrative, request.style, max_beats=MAX_BEATS
        )
    except RuntimeError as exc:
        logger.error("LLM provider chain exhausted: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected LLM error: %s", exc)
        raise HTTPException(status_code=500, detail="Narrative processing failed.")

    # ── Step 2: Apply Prompt Factory (style injection) ───────────────────────
    try:
        factory = PromptFactory(request.style)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    styled_prompts = [factory.build(beat["image_prompt"]) for beat in beats]

    # ── Step 3: Generate images concurrently ─────────────────────────────────
    # asyncio.gather lets all HF calls run in parallel — critical for UX since
    # each call can take 5-30s on the free tier.
    image_tasks = [
        generate_image(prompt, factory.negative_prompt) for prompt in styled_prompts
    ]
    image_results: list[tuple[str, str]] = await asyncio.gather(*image_tasks)

    # ── Step 4: Assemble scenes ───────────────────────────────────────────────
    scenes: list[Scene] = []
    for idx, (beat, prompt, (img_data, img_fmt)) in enumerate(
        zip(beats, styled_prompts, image_results)
    ):
        scenes.append(
            Scene(
                beat_index=idx,
                original_text=beat["original_text"],
                enhanced_prompt=prompt,
                image_data=img_data,
                image_format=img_fmt,
                provider_used=provider_chain[-1],  # The provider that actually succeeded
            )
        )

    return StoryboardResponse(
        style=request.style,
        total_beats=len(scenes),
        scenes=scenes,
        provider_chain=provider_chain,
    )
