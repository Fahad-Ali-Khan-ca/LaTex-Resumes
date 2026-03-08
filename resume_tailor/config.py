"""Configuration loading from environment variables and .env files."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    llm_provider: str
    llm_api_key: str
    llm_model: str
    resume_path: Path
    output_dir: Path
    lualatex_cmd: str


def load_config(
    resume_path: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Config:
    """Load configuration from environment variables and .env file."""
    from dotenv import load_dotenv

    load_dotenv()

    provider = os.getenv("LLM_PROVIDER", "anthropic")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", _default_model(provider))

    return Config(
        llm_provider=provider,
        llm_api_key=api_key,
        llm_model=model,
        resume_path=Path(resume_path) if resume_path else _find_resume(),
        output_dir=Path(output_dir) if output_dir else Path("output"),
        lualatex_cmd=os.getenv("LUALATEX_CMD", "lualatex"),
    )


def _default_model(provider: str) -> str:
    defaults = {
        "anthropic": "claude-sonnet-4-20250514",
        "openai": "gpt-4o",
    }
    return defaults.get(provider, "")


def _find_resume() -> Path:
    """Auto-detect .tex file in current directory."""
    tex_files = list(Path(".").glob("*.tex"))
    if len(tex_files) == 1:
        return tex_files[0]
    if len(tex_files) == 0:
        raise FileNotFoundError("No .tex files found. Specify --resume path.")
    raise FileNotFoundError(
        f"Multiple .tex files found: {[str(f) for f in tex_files]}. "
        "Specify --resume path."
    )
