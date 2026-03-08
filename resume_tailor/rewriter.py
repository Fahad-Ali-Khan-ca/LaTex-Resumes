"""LLM-powered resume rewriting for ATS optimization.

Rewrites the summary, work experience bullets, and project descriptions
to align with a target job description while preserving truthfulness.
"""

import copy
import re

from .keyword_analyzer import get_emphasis_keywords, get_keyword_gaps
from .llm_client import LLMClient
from .models import (
    JobDescription,
    JobExperience,
    ProjectEntry,
    ResumeData,
    SummarySection,
)

SYSTEM_PROMPT = """\
You are an expert resume writer specializing in ATS optimization.
You rewrite resume content to align with job descriptions while:
1. Preserving truthfulness — never fabricate experiences or skills
2. Using exact keywords from the job description where they honestly apply
3. Maintaining professional tone and conciseness
4. Keeping LaTeX formatting commands intact (\\textbf{}, \\%, etc.)
5. Never adding experiences or skills the candidate doesn't have
6. Outputting ONLY the requested content — no explanations, no markdown fences
"""


def rewrite_resume(
    resume: ResumeData,
    jd: JobDescription,
    llm: LLMClient,
) -> ResumeData:
    """Rewrite resume sections to align with the job description."""
    tailored = copy.deepcopy(resume)

    print("  Rewriting summary...")
    tailored.summary = _rewrite_summary(resume, jd, llm)

    for i, exp in enumerate(tailored.experiences):
        print(f"  Rewriting bullets for: {exp.title_and_company}...")
        tailored.experiences[i] = _rewrite_experience(exp, jd, llm)

    for i, proj in enumerate(tailored.projects):
        print(f"  Rewriting project: {proj.title}...")
        tailored.projects[i] = _rewrite_project(proj, jd, llm)

    return tailored


def _rewrite_summary(
    resume: ResumeData,
    jd: JobDescription,
    llm: LLMClient,
) -> SummarySection:
    """Fully rewrite the summary to target the specific role."""
    gaps = get_keyword_gaps(jd)
    emphasis = get_emphasis_keywords(jd)

    prompt = f"""\
Rewrite this resume summary to target the following job.

CURRENT SUMMARY:
{resume.summary.raw_latex if resume.summary else ""}

JOB TITLE: {jd.title or "Not specified"}
JOB DESCRIPTION (excerpt):
{jd.raw_text[:2000]}

KEYWORDS TO EMPHASIZE (already in resume):
{", ".join(kw.keyword for kw in emphasis[:15])}

KEYWORDS TO NATURALLY INCORPORATE (if honestly applicable):
{", ".join(kw.keyword for kw in gaps[:10])}

RULES:
- Output ONLY the summary paragraph text with LaTeX formatting
- Keep it to 2-3 sentences maximum
- Use \\textbf{{}} to bold key technical terms
- Do NOT include \\section*{{Summary}} or any header
- Do NOT fabricate skills or experience
- Preserve the candidate's actual background and experience level
"""

    rewritten = llm.generate(prompt, system=SYSTEM_PROMPT)
    rewritten = _clean_llm_output(rewritten)

    return SummarySection(text=rewritten, raw_latex=rewritten)


def _rewrite_experience(
    exp: JobExperience,
    jd: JobDescription,
    llm: LLMClient,
) -> JobExperience:
    """Rewrite bullet points for a single work experience entry."""
    bullets_text = "\n".join(f"- {b}" for b in exp.bullet_latex)

    prompt = f"""\
Rewrite these resume bullet points to better align with the target job.

JOB TITLE & COMPANY: {exp.title_and_company}
DATE: {exp.date_range}

CURRENT BULLETS:
{bullets_text}

TARGET JOB DESCRIPTION (excerpt):
{jd.raw_text[:1500]}

RULES:
- Output exactly {len(exp.bullet_latex)} bullets, one per line, starting with "- "
- Preserve LaTeX formatting: use \\textbf{{}} for technologies and metrics
- Use \\% for percentage signs (LaTeX requirement)
- Emphasize keywords from the job description where they honestly apply
- Keep each bullet to 1-2 lines maximum
- Start with strong action verbs
- Quantify impact where possible
- Do NOT fabricate experiences or metrics — preserve the core truth of each bullet
"""

    rewritten = llm.generate(prompt, system=SYSTEM_PROMPT)
    rewritten = _clean_llm_output(rewritten)

    new_bullets = _parse_bullet_list(rewritten)

    # Fallback: if parsing failed, keep originals
    if not new_bullets:
        return exp

    return JobExperience(
        title_and_company=exp.title_and_company,
        date_range=exp.date_range,
        bullets=[_strip_basic_latex(b) for b in new_bullets],
        bullet_latex=new_bullets,
        raw_latex=exp.raw_latex,
    )


def _rewrite_project(
    proj: ProjectEntry,
    jd: JobDescription,
    llm: LLMClient,
) -> ProjectEntry:
    """Rewrite a project description to align with the JD."""
    prompt = f"""\
Rewrite this project description to better align with the target job.

PROJECT: {proj.title}
CURRENT DESCRIPTION: {proj.description_latex}

TARGET JOB DESCRIPTION (excerpt):
{jd.raw_text[:1500]}

RULES:
- Output ONLY the description text (1-2 sentences)
- Use LaTeX formatting where appropriate (\\textbf{{}}, etc.)
- Emphasize relevant technologies and skills from the job description
- Do NOT fabricate capabilities
- Keep it concise — this fits in a single tabularx cell
"""

    rewritten = llm.generate(prompt, system=SYSTEM_PROMPT)
    rewritten = _clean_llm_output(rewritten)

    return ProjectEntry(
        title=proj.title,
        github_url=proj.github_url,
        description=_strip_basic_latex(rewritten),
        description_latex=rewritten,
        raw_latex=proj.raw_latex,
    )


def _clean_llm_output(text: str) -> str:
    """Remove markdown code fences and extra whitespace from LLM output."""
    text = re.sub(r"```(?:latex|tex)?\n?", "", text)
    text = text.strip()
    # Escape bare LaTeX special chars that LLMs sometimes forget
    # (but don't double-escape existing ones)
    text = re.sub(r"(?<!\\)%", r"\\%", text)
    return text


def _parse_bullet_list(text: str) -> list[str]:
    """Parse a bullet list from LLM output."""
    bullets: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            bullets.append(line[2:].strip())
        elif line.startswith("\\item "):
            bullets.append(line[6:].strip())
        elif line.startswith("* "):
            bullets.append(line[2:].strip())
    return bullets


def _strip_basic_latex(text: str) -> str:
    """Lightweight LaTeX stripping for the plain-text field."""
    text = re.sub(r"\\textbf\{(.+?)\}", r"\1", text)
    text = re.sub(r"\\textit\{(.+?)\}", r"\1", text)
    text = text.replace("\\%", "%")
    return text
