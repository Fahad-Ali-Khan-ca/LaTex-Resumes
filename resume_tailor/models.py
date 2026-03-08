"""Data models for structured resume and job description representation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SkillCategory(Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    TOOLS = "tools"
    METHODOLOGIES = "methodologies"
    OTHER = "other"


@dataclass
class ContactInfo:
    name: str = ""
    github: Optional[str] = None
    linkedin: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    raw_latex: str = ""


@dataclass
class SummarySection:
    text: str = ""
    raw_latex: str = ""


@dataclass
class EducationEntry:
    degree: str = ""
    institution: str = ""
    graduation_date: str = ""
    honors: Optional[str] = None
    raw_latex: str = ""


@dataclass
class SkillLine:
    category_name: str = ""
    items: list[str] = field(default_factory=list)
    raw_latex: str = ""


@dataclass
class JobExperience:
    title_and_company: str = ""
    date_range: str = ""
    bullets: list[str] = field(default_factory=list)
    bullet_latex: list[str] = field(default_factory=list)
    raw_latex: str = ""


@dataclass
class ProjectEntry:
    title: str = ""
    github_url: Optional[str] = None
    description: str = ""
    description_latex: str = ""
    raw_latex: str = ""


@dataclass
class ResumeData:
    preamble: str = ""
    header: ContactInfo = field(default_factory=ContactInfo)
    summary: Optional[SummarySection] = None
    education: list[EducationEntry] = field(default_factory=list)
    skills: list[SkillLine] = field(default_factory=list)
    experiences: list[JobExperience] = field(default_factory=list)
    projects: list[ProjectEntry] = field(default_factory=list)
    raw_source: str = ""


@dataclass
class JobKeyword:
    keyword: str = ""
    category: SkillCategory = SkillCategory.OTHER
    frequency: int = 1
    found_in_resume: bool = False


@dataclass
class JobDescription:
    raw_text: str = ""
    title: Optional[str] = None
    company: Optional[str] = None
    keywords: list[JobKeyword] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
