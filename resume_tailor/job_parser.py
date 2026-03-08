"""Parse job descriptions from text, files, or URLs."""

import re
from pathlib import Path
from typing import Optional

from .models import JobDescription


def parse_job_description(
    text: Optional[str] = None,
    file_path: Optional[str] = None,
    url: Optional[str] = None,
) -> JobDescription:
    """Parse a job description from one of three input sources."""
    if text:
        raw = text
    elif file_path:
        raw = Path(file_path).read_text(encoding="utf-8")
    elif url:
        raw = _scrape_url(url)
    else:
        raise ValueError("Must provide text, file_path, or url")

    title = _extract_job_title(raw)
    company = _extract_company(raw)
    requirements = _extract_requirements(raw)
    responsibilities = _extract_responsibilities(raw)

    return JobDescription(
        raw_text=raw,
        title=title,
        company=company,
        requirements=requirements,
        responsibilities=responsibilities,
    )


def _scrape_url(url: str) -> str:
    """Fetch and extract text from a job posting URL."""
    import requests
    from bs4 import BeautifulSoup

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove noise elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Try common job board selectors
    selectors = [
        ".job-description",
        ".description__text",
        "#job-description",
        '[data-testid="job-description"]',
        ".posting-page",
        ".job-details",
        ".jobsearch-JobComponent-description",
        "article",
        "main",
    ]
    for selector in selectors:
        element = soup.select_one(selector)
        if element and len(element.get_text(strip=True)) > 100:
            return element.get_text(separator="\n", strip=True)

    # Fallback: body text
    return soup.get_text(separator="\n", strip=True)


def _extract_job_title(text: str) -> Optional[str]:
    """Heuristically extract the job title from JD text."""
    patterns = [
        r"(?:Job\s*Title|Position|Role)\s*[:\-]\s*(.+)",
        r"^(.+?(?:Engineer|Developer|Analyst|Manager|Designer|Architect|Consultant|Specialist).+?)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            title = match.group(1).strip()
            if len(title) < 100:
                return title

    # Fallback: first non-empty short line
    for line in text.split("\n"):
        line = line.strip()
        if 5 < len(line) < 80:
            return line
    return None


def _extract_company(text: str) -> Optional[str]:
    """Heuristically extract the company name from JD text."""
    patterns = [
        r"(?:Company|Employer|Organization)\s*[:\-]\s*(.+)",
        r"(?:About|Join)\s+(.+?)(?:\n|\.)",
        r"(?:at|@)\s+(.+?)(?:\n|\.|\s{2,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) < 60:
                return company
    return None


def _extract_requirements(text: str) -> list[str]:
    """Extract bullet points from requirements/qualifications sections."""
    return _extract_section_bullets(
        text,
        [
            "requirements",
            "qualifications",
            "what you'll need",
            "what we're looking for",
            "must have",
            "required skills",
            "minimum qualifications",
        ],
    )


def _extract_responsibilities(text: str) -> list[str]:
    """Extract bullet points from responsibilities/duties sections."""
    return _extract_section_bullets(
        text,
        [
            "responsibilities",
            "what you'll do",
            "duties",
            "role description",
            "about the role",
            "key responsibilities",
        ],
    )


def _extract_section_bullets(text: str, section_headers: list[str]) -> list[str]:
    """Extract bullet points following a section header."""
    lines = text.split("\n")
    capturing = False
    bullets: list[str] = []

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        # Check if this is a target section header
        if any(h in lower for h in section_headers):
            capturing = True
            continue

        # Stop at the next section header
        if (
            capturing
            and stripped
            and not stripped.startswith(("-", "*", ".", "\u2022", "\u25e6", "o "))
            and stripped.endswith(":")
            and len(stripped) < 60
        ):
            break

        # Capture bullet lines
        if capturing and stripped:
            cleaned = re.sub(r"^[\-\*\.\u2022\u25e6]\s*", "", stripped)
            if cleaned and len(cleaned) > 5:
                bullets.append(cleaned)

    return bullets
