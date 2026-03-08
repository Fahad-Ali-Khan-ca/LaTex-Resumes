"""CLI entry point for resume_tailor."""

import argparse
import os
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="resume-tailor",
        description="Tailor your LaTeX resume to match a specific job description.",
    )

    # Job description input (mutually exclusive)
    jd_group = parser.add_mutually_exclusive_group(required=True)
    jd_group.add_argument(
        "--jd-file", type=str, help="Path to a text file containing the job description"
    )
    jd_group.add_argument(
        "--jd-text", type=str, help="Job description as direct text"
    )
    jd_group.add_argument(
        "--jd-url", type=str, help="URL of the job posting to scrape"
    )

    # Resume input
    parser.add_argument(
        "--resume", type=str, default=None,
        help="Path to the .tex resume file (auto-detected if omitted)",
    )

    # Output options
    parser.add_argument(
        "--output-dir", type=str, default="output",
        help="Directory for tailored output (default: output/)",
    )
    parser.add_argument(
        "--no-compile", action="store_true",
        help="Skip PDF compilation (output .tex only)",
    )

    # LLM options (override env vars)
    parser.add_argument(
        "--provider", type=str, default=None,
        help="LLM provider: anthropic, openai (overrides LLM_PROVIDER env var)",
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="LLM model name (overrides LLM_MODEL env var)",
    )

    # Analysis options
    parser.add_argument(
        "--keywords-only", action="store_true",
        help="Only show keyword gap analysis, don't rewrite",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed progress and keyword analysis",
    )

    args = parser.parse_args()

    try:
        _run(args)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _run(args: argparse.Namespace) -> None:
    """Main execution pipeline."""
    from .compiler import compile_to_pdf
    from .config import load_config
    from .job_parser import parse_job_description
    from .keyword_analyzer import (
        analyze_keywords,
        get_keyword_gaps,
        suggest_skill_reorder,
    )
    from .latex_generator import write_tailored_resume
    from .latex_parser import parse_resume
    from .llm_client import create_llm_client
    from .rewriter import rewrite_resume

    # Override env vars with CLI args
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
    if args.model:
        os.environ["LLM_MODEL"] = args.model

    # 1. Load configuration
    config = load_config(
        resume_path=args.resume,
        output_dir=args.output_dir,
    )
    print(f"Resume:   {config.resume_path}")
    print(f"Provider: {config.llm_provider} ({config.llm_model})")
    print()

    # 2. Parse the resume
    print("Parsing resume...")
    resume = parse_resume(config.resume_path)
    print(
        f"  {len(resume.experiences)} experiences, "
        f"{len(resume.projects)} projects, "
        f"{len(resume.skills)} skill categories"
    )

    # 3. Parse the job description
    print("Parsing job description...")
    jd = parse_job_description(
        text=args.jd_text,
        file_path=args.jd_file,
        url=args.jd_url,
    )
    print(f"  Job:     {jd.title or 'Unknown title'}")
    print(f"  Company: {jd.company or 'Unknown'}")

    # 4. Analyze keywords
    print("\nAnalyzing keywords...")
    jd = analyze_keywords(jd, resume)
    gaps = get_keyword_gaps(jd)

    if args.verbose or args.keywords_only:
        print(f"  Total JD keywords:    {len(jd.keywords)}")
        print(f"  Already in resume:    {len(jd.keywords) - len(gaps)}")
        print(f"  Gaps to address:      {len(gaps)}")
        if gaps:
            print("\n  Top keyword gaps:")
            for kw in gaps[:15]:
                print(f"    - {kw.keyword} ({kw.category.value}, {kw.frequency}x in JD)")

    if args.keywords_only:
        print("\nDone (keywords-only mode).")
        return

    # 5. Verify LLM API key
    if not config.llm_api_key:
        print(
            "\nError: LLM_API_KEY not set. "
            "Set it in .env file or as an environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 6. Rewrite with LLM
    print("\nRewriting resume with LLM...")
    llm = create_llm_client(config)
    tailored = rewrite_resume(resume, jd, llm)

    # 7. Reorder/augment skills
    print("\nOptimizing skills section...")
    tailored.skills = suggest_skill_reorder(tailored.skills, jd)

    # 8. Generate tailored .tex
    print("Generating tailored LaTeX...")
    tex_path = write_tailored_resume(
        tailored,
        config.output_dir,
        job_title=jd.title,
        company=jd.company,
    )
    print(f"  Written to: {tex_path}")

    # 9. Compile to PDF
    if not args.no_compile:
        print("\nCompiling PDF...")
        try:
            pdf_path = compile_to_pdf(tex_path, config.lualatex_cmd)
            print(f"  PDF generated: {pdf_path}")
        except Exception as e:
            print(f"  PDF compilation failed: {e}")
            print("  The .tex file was saved — fix errors and compile manually.")
    else:
        print("  Skipping PDF compilation (--no-compile)")

    print("\nDone!")


if __name__ == "__main__":
    main()
