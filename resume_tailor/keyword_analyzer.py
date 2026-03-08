"""ATS keyword extraction, gap analysis, and skill optimization."""

import re
from collections import Counter

from .models import (
    JobDescription,
    JobKeyword,
    ResumeData,
    SkillCategory,
    SkillLine,
)

# Predefined keyword banks for categorization
TECHNICAL_SKILLS = {
    "python", "java", "javascript", "typescript", "c#", "c++", "c", "go",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
    "react", "angular", "vue", "svelte", "next.js", "nuxt",
    "node.js", "express", "django", "flask", "fastapi", "spring",
    "asp.net", ".net", "rails",
    "sql", "nosql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch",
    "dynamodb", "cassandra", "sqlite",
    "html", "css", "sass", "tailwind", "bootstrap",
    "graphql", "rest", "grpc", "websocket",
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "microservices", "monolith", "serverless", "event-driven",
    "data structures", "algorithms", "system design",
    "linux", "unix", "bash", "powershell",
}

SOFT_SKILLS = {
    "communication", "leadership", "collaboration", "teamwork",
    "problem-solving", "analytical", "critical thinking", "mentoring",
    "stakeholder", "cross-functional", "presentation", "negotiation",
    "time management", "self-motivated", "detail-oriented", "adaptable",
    "creative", "innovative", "strategic", "proactive",
}

TOOLS = {
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "github actions", "gitlab ci", "circleci", "travis ci",
    "jira", "confluence", "slack", "notion", "trello",
    "splunk", "cloudwatch", "datadog", "grafana", "prometheus",
    "figma", "postman", "swagger", "insomnia",
    "pytest", "junit", "selenium", "cypress", "jest", "mocha",
    "webpack", "vite", "babel", "eslint", "prettier",
    "git", "svn", "mercurial",
    "nginx", "apache", "caddy",
    "rabbitmq", "kafka", "sqs", "sns",
    "ec2", "lambda", "s3", "rds", "ecs", "fargate",
    "vercel", "netlify", "heroku", "render",
}

METHODOLOGIES = {
    "agile", "scrum", "kanban", "waterfall", "lean",
    "tdd", "bdd", "ci/cd", "devops", "sre", "gitops",
    "domain-driven", "test-driven", "behavior-driven",
    "pair programming", "code review", "mob programming",
    "sprint", "retrospective", "standup",
}


def analyze_keywords(jd: JobDescription, resume: ResumeData) -> JobDescription:
    """Extract keywords from JD, categorize them, and check against resume."""
    jd_text_lower = jd.raw_text.lower()
    resume_text = _flatten_resume_text(resume).lower()

    keywords = _extract_keywords(jd_text_lower)

    jd_keywords: list[JobKeyword] = []
    for kw, freq in keywords.items():
        category = _categorize_keyword(kw)
        found = kw in resume_text
        jd_keywords.append(
            JobKeyword(
                keyword=kw,
                category=category,
                frequency=freq,
                found_in_resume=found,
            )
        )

    # Sort: most frequent first, gaps before matches
    jd_keywords.sort(key=lambda k: (-k.frequency, k.found_in_resume))
    jd.keywords = jd_keywords
    return jd


def get_keyword_gaps(jd: JobDescription) -> list[JobKeyword]:
    """Return keywords in JD but missing from resume."""
    return [kw for kw in jd.keywords if not kw.found_in_resume]


def get_emphasis_keywords(jd: JobDescription) -> list[JobKeyword]:
    """Return keywords present in both JD and resume."""
    return [kw for kw in jd.keywords if kw.found_in_resume]


def suggest_skill_reorder(
    current_skills: list[SkillLine],
    jd: JobDescription,
) -> list[SkillLine]:
    """Reorder skill lines by JD relevance and inject missing keywords."""
    import copy

    skills = copy.deepcopy(current_skills)
    gaps = get_keyword_gaps(jd)

    # Score each skill line by JD keyword overlap
    scored: list[tuple[int, SkillLine]] = []
    for skill_line in skills:
        items_lower = {item.lower() for item in skill_line.items}
        score = sum(
            kw.frequency
            for kw in jd.keywords
            if kw.keyword in items_lower
        )
        scored.append((score, skill_line))

    scored.sort(key=lambda x: -x[0])
    reordered = [sl for _, sl in scored]

    # Inject missing technical/tool keywords into the best-matching category
    for gap_kw in gaps:
        if gap_kw.category in (SkillCategory.TECHNICAL, SkillCategory.TOOLS):
            best_line = _find_best_category(reordered, gap_kw)
            if best_line and gap_kw.keyword not in [i.lower() for i in best_line.items]:
                best_line.items.append(gap_kw.keyword)

    return reordered


def _extract_keywords(text: str) -> dict[str, int]:
    """Extract meaningful technical terms from text."""
    all_known = TECHNICAL_SKILLS | SOFT_SKILLS | TOOLS | METHODOLOGIES
    found: Counter[str] = Counter()

    for term in all_known:
        # Use word boundary matching for single words, substring for multi-word
        if " " in term:
            count = text.count(term)
        else:
            count = len(re.findall(rf"\b{re.escape(term)}\b", text))
        if count > 0:
            found[term] = count

    return dict(found)


def _categorize_keyword(keyword: str) -> SkillCategory:
    kl = keyword.lower()
    if kl in TECHNICAL_SKILLS:
        return SkillCategory.TECHNICAL
    if kl in SOFT_SKILLS:
        return SkillCategory.SOFT
    if kl in TOOLS:
        return SkillCategory.TOOLS
    if kl in METHODOLOGIES:
        return SkillCategory.METHODOLOGIES
    return SkillCategory.OTHER


def _flatten_resume_text(resume: ResumeData) -> str:
    """Concatenate all resume text for keyword matching."""
    parts: list[str] = []
    if resume.summary:
        parts.append(resume.summary.text)
    for exp in resume.experiences:
        parts.extend(exp.bullets)
    for proj in resume.projects:
        parts.append(proj.description)
    for skill in resume.skills:
        parts.extend(skill.items)
    return " ".join(parts)


def _find_best_category(skills: list[SkillLine], kw: JobKeyword) -> SkillLine | None:
    """Find the skill line that best matches this keyword's category."""
    category_map: dict[SkillCategory, list[str]] = {
        SkillCategory.TECHNICAL: ["programming", "languages", "web", "backend"],
        SkillCategory.TOOLS: ["cloud", "devops", "testing", "qa", "tools"],
        SkillCategory.METHODOLOGIES: ["ways of working", "process", "methodologies"],
    }
    target_names = category_map.get(kw.category, [])
    for sl in skills:
        if any(t in sl.category_name.lower() for t in target_names):
            return sl
    return skills[0] if skills else None
