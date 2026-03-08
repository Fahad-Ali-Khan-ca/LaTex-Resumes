"""Reconstruct a complete .tex file from structured ResumeData.

Rebuilds the entire document from the structured representation rather than
doing string replacement on the original. The preamble and header are
preserved verbatim; content sections are regenerated.
"""

import re
import datetime
from pathlib import Path

from .models import (
    JobExperience,
    ProjectEntry,
    ResumeData,
    SkillLine,
)


def generate_latex(resume: ResumeData) -> str:
    """Generate a complete .tex file from structured ResumeData."""
    parts: list[str] = []

    # Preamble (unchanged)
    parts.append(resume.preamble)

    # Header (unchanged)
    parts.append("")
    parts.append(_section_comment("TITLE"))
    parts.append(resume.header.raw_latex)

    # Summary (rewritten)
    parts.append("")
    parts.append(_section_comment("SUMMARY"))
    parts.append(r"\section*{Summary}")
    if resume.summary:
        parts.append(resume.summary.raw_latex)

    # Education (unchanged)
    parts.append("")
    parts.append(_section_comment("EDUCATION"))
    parts.append(r"\section*{Education}")
    for edu in resume.education:
        parts.append(edu.raw_latex)

    # Skills (reordered/augmented)
    parts.append("")
    parts.append(_section_comment("SKILLS"))
    parts.append(r"\section*{Technical Skills}")
    parts.append(_render_skills(resume.skills))

    # Work Experience (rewritten bullets)
    parts.append("")
    parts.append(_section_comment("EXPERIENCE"))
    parts.append(r"\section{Work Experience}")
    parts.append("")
    for i, exp in enumerate(resume.experiences):
        parts.append(_render_experience(exp))
        if i < len(resume.experiences) - 1:
            parts.append("")
            parts.append(r"\vspace{3pt}")
            parts.append("")

    # Projects (rewritten descriptions)
    parts.append("")
    parts.append(r"\vspace{-2pt}")
    parts.append("")
    parts.append(_section_comment("PROJECTS"))
    parts.append(r"\section*{Projects}")
    parts.append("")
    for i, proj in enumerate(resume.projects):
        parts.append(_render_project(proj))
        if i < len(resume.projects) - 1:
            parts.append("")
            parts.append(r"\vspace{-2pt}")
            parts.append("")

    # End document
    parts.append("")
    parts.append(r"\end{document}")

    return "\n".join(parts)


def write_tailored_resume(
    resume: ResumeData,
    output_dir: Path,
    job_title: str | None = None,
    company: str | None = None,
) -> Path:
    """Write the tailored .tex file to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    name_parts: list[str] = []
    if company:
        name_parts.append(_slugify(company))
    if job_title:
        name_parts.append(_slugify(job_title))
    if not name_parts:
        name_parts.append(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))

    filename = "_".join(name_parts) + ".tex"
    output_path = output_dir / filename

    latex_content = generate_latex(resume)
    output_path.write_text(latex_content, encoding="utf-8")

    return output_path


def _section_comment(title: str) -> str:
    """Generate the section divider comment block."""
    line = "%" + "-" * 88
    return f"{line}\n% {title}\n{line}"


def _render_skills(skills: list[SkillLine]) -> str:
    """Render skill lines with proper LaTeX formatting."""
    lines: list[str] = []
    for i, skill in enumerate(skills):
        items_str = ", ".join(skill.items)
        suffix = " \\\\" if i < len(skills) - 1 else ""
        lines.append(rf"\textbf{{{skill.category_name}:}} {items_str}{suffix}")
    return "\n".join(lines)


def _render_experience(exp: JobExperience) -> str:
    """Render a single job experience in joblong environment."""
    lines = [rf"\begin{{joblong}}{{{exp.title_and_company}}}{{{exp.date_range}}}"]
    for bullet in exp.bullet_latex:
        lines.append(rf"\item {bullet}")
    lines.append(r"\end{joblong}")
    return "\n".join(lines)


def _render_project(proj: ProjectEntry) -> str:
    """Render a project entry in tabularx format."""
    lines = [r"\begin{tabularx}{\linewidth}{@{}l r@{}}"]

    if proj.github_url:
        lines.append(
            rf"\textbf{{{proj.title}}} & \hfill "
            rf"\href{{{proj.github_url}}}{{\faGithub}} \\[2pt]"
        )
    else:
        lines.append(rf"\textbf{{{proj.title}}} & \hfill \\[2pt]")

    lines.append(
        rf"\multicolumn{{2}}{{@{{}}X@{{}}}}{{{proj.description_latex}}}\\"
    )
    lines.append(r"\end{tabularx}")
    return "\n".join(lines)


def _slugify(text: str) -> str:
    """Convert text to a safe filename component."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text[:30]
