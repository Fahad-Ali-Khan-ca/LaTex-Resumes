"""Regex-based LaTeX parser for the resume template.

Parses FahadAliKhan_Resume.tex into a structured ResumeData object.
This parser is specific to the template's patterns (joblong env, tabularx projects, etc.)
and is NOT a general LaTeX parser.
"""

import re
from pathlib import Path

from .models import (
    ContactInfo,
    EducationEntry,
    JobExperience,
    ProjectEntry,
    ResumeData,
    SkillLine,
    SummarySection,
)


def parse_resume(tex_path: Path) -> ResumeData:
    """Parse a .tex resume file into structured ResumeData."""
    source = tex_path.read_text(encoding="utf-8")
    resume = ResumeData(raw_source=source)

    resume.preamble = _extract_preamble(source)
    resume.header = _parse_header(source)

    sections = _split_sections(source)
    resume.summary = _parse_summary(sections)
    resume.education = _parse_education(sections)
    resume.skills = _parse_skills(sections)
    resume.experiences = _parse_experiences(sections)
    resume.projects = _parse_projects(sections)

    return resume


def _extract_preamble(source: str) -> str:
    """Extract everything from start up to and including \\begin{document} and \\pagestyle{empty}."""
    match = re.search(
        r"^(.*?\\begin\{document\}\s*\n\\pagestyle\{empty\})",
        source,
        re.DOTALL,
    )
    return match.group(1) if match else ""


def _parse_header(source: str) -> ContactInfo:
    """Extract the header tabularx block containing name and contact links."""
    # The header uses {C} column (centered), appears before first \section
    pattern = r"(\\begin\{tabularx\}\{\\linewidth\}\{@\{\}C@\{\}\}.*?\\end\{tabularx\})"
    match = re.search(pattern, source, re.DOTALL)
    if not match:
        return ContactInfo(raw_latex="")

    block = match.group(1)

    name_match = re.search(r"\\Huge\{(.+?)\}", block)
    name = name_match.group(1) if name_match else ""

    github = _extract_href_url(block, "github.com")
    linkedin = _extract_href_url(block, "linkedin.com")

    email_match = re.search(r"\\href\{mailto:([^}]+)\}", block)
    email = email_match.group(1) if email_match else None

    phone_match = re.search(r"\\faMobile\\?\s*(.+?)(?:\n|\}|$)", block)
    phone = phone_match.group(1).strip().rstrip("}") if phone_match else None

    return ContactInfo(
        name=name,
        github=github,
        linkedin=linkedin,
        email=email,
        phone=phone,
        raw_latex=block,
    )


def _extract_href_url(text: str, domain: str) -> str | None:
    """Extract a URL from \\href{url}{...} matching a domain."""
    pattern = rf"\\href\{{(https?://[^}}]*{re.escape(domain)}[^}}]*)\}}"
    match = re.search(pattern, text)
    return match.group(1) if match else None


def _split_sections(source: str) -> dict[str, str]:
    """Split the document body into {section_name: raw_content} pairs."""
    # Extract body between \pagestyle{empty} and \end{document}
    body_match = re.search(
        r"\\pagestyle\{empty\}(.*?)\\end\{document\}",
        source,
        re.DOTALL,
    )
    if not body_match:
        return {}

    body = body_match.group(1)

    # Find all \section*{Name} and \section{Name} markers
    section_pattern = r"\\section\*?\{(.+?)\}"
    markers = [
        (m.start(), m.group(1).strip(), m.end())
        for m in re.finditer(section_pattern, body)
    ]

    sections: dict[str, str] = {}
    for i, (_, name, content_start) in enumerate(markers):
        end = markers[i + 1][0] if i + 1 < len(markers) else len(body)
        sections[name] = body[content_start:end].strip()

    return sections


def _parse_summary(sections: dict[str, str]) -> SummarySection | None:
    """Parse the Summary section (raw paragraph text)."""
    raw = sections.get("Summary")
    if raw is None:
        return None
    raw = _strip_comment_blocks(raw)
    plain = _latex_to_plain(raw)
    return SummarySection(text=plain, raw_latex=raw)


def _parse_education(sections: dict[str, str]) -> list[EducationEntry]:
    """Parse the Education section."""
    raw = sections.get("Education")
    if not raw:
        return []
    raw = _strip_comment_blocks(raw)

    # The education section has: \textbf{Degree} \hfill Date \\ Institution \hfill honors
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    entries: list[EducationEntry] = []

    if len(lines) >= 2:
        entries.append(
            EducationEntry(
                degree=_latex_to_plain(lines[0].split(r"\hfill")[0]) if r"\hfill" in lines[0] else _latex_to_plain(lines[0]),
                institution=_latex_to_plain(lines[1].split(r"\hfill")[0]) if len(lines) > 1 else "",
                graduation_date=lines[0].split(r"\hfill")[-1].strip() if r"\hfill" in lines[0] else "",
                honors=lines[1].split(r"\hfill")[-1].strip() if len(lines) > 1 and r"\hfill" in lines[1] else None,
                raw_latex=raw,
            )
        )
    elif lines:
        entries.append(EducationEntry(raw_latex=raw))

    return entries


def _parse_skills(sections: dict[str, str]) -> list[SkillLine]:
    """Parse the Technical Skills section into category/items pairs."""
    raw = sections.get("Technical Skills")
    if not raw:
        return []
    raw = _strip_comment_blocks(raw)

    lines: list[SkillLine] = []
    for segment in re.split(r"\\\\", raw):
        segment = segment.strip()
        if not segment:
            continue
        cat_match = re.match(r"\\textbf\{(.+?):?\}\s*(.*)", segment, re.DOTALL)
        if cat_match:
            category = cat_match.group(1).rstrip(":")
            items_str = cat_match.group(2).strip()
            items = [i.strip() for i in items_str.split(",") if i.strip()]
            lines.append(
                SkillLine(
                    category_name=category,
                    items=items,
                    raw_latex=segment,
                )
            )
    return lines


def _parse_experiences(sections: dict[str, str]) -> list[JobExperience]:
    """Parse Work Experience section — extract joblong environments."""
    raw = sections.get("Work Experience")
    if not raw:
        return []

    pattern = r"\\begin\{joblong\}\{(.+?)\}\{(.+?)\}(.*?)\\end\{joblong\}"
    experiences: list[JobExperience] = []

    for match in re.finditer(pattern, raw, re.DOTALL):
        title_company = match.group(1)
        date_range = match.group(2)
        body = match.group(3)

        # Extract \item lines
        bullet_latex_list = re.findall(
            r"\\item\s+(.*?)(?=\\item|\\end\{joblong\}|$)",
            body,
            re.DOTALL,
        )
        bullet_latex_list = [b.strip() for b in bullet_latex_list if b.strip()]
        bullets_plain = [_latex_to_plain(b) for b in bullet_latex_list]

        experiences.append(
            JobExperience(
                title_and_company=title_company,
                date_range=date_range,
                bullets=bullets_plain,
                bullet_latex=bullet_latex_list,
                raw_latex=match.group(0),
            )
        )
    return experiences


def _parse_projects(sections: dict[str, str]) -> list[ProjectEntry]:
    """Parse Projects section — extract tabularx blocks."""
    raw = sections.get("Projects")
    if not raw:
        return []

    pattern = r"\\begin\{tabularx\}\{\\linewidth\}\{@\{\}l\s+r@\{\}\}(.*?)\\end\{tabularx\}"
    projects: list[ProjectEntry] = []

    for match in re.finditer(pattern, raw, re.DOTALL):
        block = match.group(1)
        full_block = match.group(0)

        title_match = re.search(r"\\textbf\{(.+?)\}", block)
        title = title_match.group(1) if title_match else ""

        href_match = re.search(r"\\href\{(https?://github\.com/[^}]+)\}", block)
        github = href_match.group(1) if href_match else None

        desc_match = re.search(
            r"\\multicolumn\{2\}\{@\{\}X@\{\}\}\{(.+?)\}\\\\",
            block,
            re.DOTALL,
        )
        desc_latex = desc_match.group(1).strip() if desc_match else ""
        desc_plain = _latex_to_plain(desc_latex)

        projects.append(
            ProjectEntry(
                title=title,
                github_url=github,
                description=desc_plain,
                description_latex=desc_latex,
                raw_latex=full_block,
            )
        )
    return projects


def _strip_comment_blocks(text: str) -> str:
    """Remove LaTeX comment lines (lines starting with %)."""
    lines = text.split("\n")
    return "\n".join(l for l in lines if not l.strip().startswith("%")).strip()


def _latex_to_plain(text: str) -> str:
    """Strip LaTeX formatting commands to produce plain text for analysis."""
    text = re.sub(r"\\textbf\{(.+?)\}", r"\1", text)
    text = re.sub(r"\\textit\{(.+?)\}", r"\1", text)
    text = re.sub(r"\\texttt\{(.+?)\}", r"\1", text)
    text = re.sub(r"\\href\{[^}]+\}\{(.+?)\}", r"\1", text)
    text = re.sub(r"\\emph\{(.+?)\}", r"\1", text)
    # Generic \cmd{content} — catch remaining
    text = re.sub(r"\\[a-zA-Z]+\{(.+?)\}", r"\1", text)
    # Bare commands like \hfill, \item
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    # LaTeX special chars
    text = text.replace("\\%", "%")
    text = text.replace("\\&", "&")
    text = text.replace("\\#", "#")
    text = text.replace("\\$", "$")
    text = re.sub(r"[{}]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
