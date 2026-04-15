Live: https://the-pitch-visualizer-sxjv.onrender.com/
# 🎬 The Pitch Visualizer

The Pitch Visualizer is a web application that transforms narrative paragraphs into AI-generated visual storyboards seamlessly. It intelligently segments text into distinct visual beats and generates cohesive storyboard images corresponding to each segment, all wrapped in a sleek glassmorphic UI.

## 🚀 Features
- **Intelligent Narrative Segmentation:** Uses LLMs (Gemini as primary / Groq Llama 3 as fallback) to split text into structured, emotionally pivoted visual beats.
- **Concurrent Image Synthesis:** Uses the Hugging Face Inference API (`stabilityai/stable-diffusion-xl-base-1.0`) to generate scenes concurrently.
- **Dynamic Prompt Factory:** Enforces prompt structure and styling consistency with various visual styles (e.g., Cinematic, Cyberpunk, Watercolor).
- **Export Capabilities:** Seamlessly export your generated storyboard to HTML.

## 🛠️ Setup & Execution

### Prerequisites
- Python 3.10+
- `uv` (recommended) or standard `pip/venv`

### 1. Installation
Clone the repository and install the dependencies:
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install fastapi uvicorn httpx huggingface-hub python-dotenv pydantic pillow
```

### 2. API Key Management
Copy the example environment file:
```bash
cp .env.example .env
```
Open `.env` and fill in your keys:
- `GEMINI_API_KEY`: Primary LLM for text segmentation (from Google AI Studio).
- `GROQ_API_KEY`: Fallback LLM just in case Gemini gets rate limited (from Groq).
- `HF_API_TOKEN`: To access the Hugging Face Serverless Inference API.

### 3. Running the Server
Start the application with Uvicorn:
```bash
uvicorn app.main:app --reload
```
Navigate to `http://localhost:8000` in your browser to access the visualizer UI.

## 🧠 Design Choices & Prompt Engineering

- **Robust Architecture:** 
  - Decoupled prompt generation and image synthesis to increase reliability.
  - Image generation runs in parallel via `asyncio.gather()`, dramatically reducing overall storyboard rendering time.
  - An automatic LLM fallback loop guarantees prompt generation succeeds even if the primary provider hits API rate limits.

- **Prompt Engineering Methodology:**
  - **Strict Persona & Formatting:** The LLM is directed as an expert "Storyboard Director" to guarantee a strict JSON array output, isolating specific verbatim story quotes from image prompts.
  - **Structural Prompting:** The prompt dictates a specific architecture: `[Subject & Action] -> [Environment] -> [Cinematography/Lighting]`. The model is explicitly barred from using abstract concepts that don't translate visually (e.g., avoiding terms like "efficiency").
  - **Prompt Factory Design:** A specialized `PromptFactory` dynamically appends high-yield aesthetic and style-specific suffixes (e.g., `octane render, subsurface scattering, 8K`).
  - **Universal Negative Prompt:** A robust `UNIVERSAL_NEGATIVE` prompt string acts as a safety net across all generations to steer the diffusion model away from common artifacts (like extra digits, morphing, and low resolution).
