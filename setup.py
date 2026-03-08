from setuptools import setup, find_packages

setup(
    name="resume_tailor",
    version="0.1.0",
    description="Automatically tailor LaTeX resumes to job descriptions",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "anthropic>=0.40.0",
        "openai>=1.50.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "resume-tailor=resume_tailor.cli:main",
        ],
    },
)
