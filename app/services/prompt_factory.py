


STYLE_SUFFIXES: dict[str, str] = {
    "Cinematic": (
        "cinematic photography, anamorphic lens, dramatic lighting, "
        "shallow depth of field, film grain, color graded, 4K"
    ),
    "3D Render": (
        "3D render, octane render, subsurface scattering, studio lighting, "
        "photorealistic materials, ultra-detailed, 8K resolution"
    ),
    "Flat Illustration": (
        "flat design illustration, vector art, bold outlines, limited color palette, "
        "clean geometric shapes, Dribbble style"
    ),
    "Watercolor": (
        "watercolor painting, soft washes, visible paper texture, "
        "loose brushstrokes, pastel tones, artistic"
    ),
    "Pixel Art": (
        "pixel art, 16-bit style, isometric, crisp pixels, "
        "retro game aesthetic, limited palette"
    ),
    "Photorealistic": (
        "hyperrealistic photography, DSLR, natural lighting, "
        "high resolution, photojournalism style"
    ),
    "Cyberpunk": (
        "cyberpunk aesthetic, neon lighting, dark moody atmosphere, "
        "futuristic technology, violet and teal color grade, high contrast"
    ),
    "Minimalist Tech": (
        "minimalist technology aesthetic, apple inspired, clean white spaces, "
        "soft shadows, premium product photography, elegant"
    ),
}

# Negative prompt appended to every call — steers the model away from
# common artifacts regardless of style.
UNIVERSAL_NEGATIVE = (
    "lowres, error, cropped, worst quality, low quality, jpeg artifacts, "
    "out of frame, watermark, signature, text, logo, banner, "
    "extra digits, morphing, blurry, dehydrated, bad anatomy, "
    "bad proportions, extra limbs, cloned face, disfigured, gross proportions, "
    "malformed limbs, missing arms, missing legs, extra arms, extra legs, "
    "fused fingers, too many fingers, long neck, username, nsfw"
)


class PromptFactory:
    """
    Injects a consistent visual style suffix into raw image prompts.

    Example:
        factory = PromptFactory("Cinematic")
        final   = factory.build("A lone astronaut walks on Mars at sunset")
        # → "A lone astronaut walks on Mars at sunset, cinematic photography, ..."
    """

    def __init__(self, style: str):
        if style not in STYLE_SUFFIXES:
            raise ValueError(
                f"Unknown style '{style}'. "
                f"Valid options: {list(STYLE_SUFFIXES.keys())}"
            )
        self.style  = style
        self._suffix = STYLE_SUFFIXES[style]

    def build(self, raw_prompt: str) -> str:
        """Return the final prompt with the style suffix appended."""
        return f"{raw_prompt.rstrip('.')}, {self._suffix}"

    @property
    def negative_prompt(self) -> str:
        return UNIVERSAL_NEGATIVE

    @staticmethod
    def available_styles() -> list[str]:
        return list(STYLE_SUFFIXES.keys())
