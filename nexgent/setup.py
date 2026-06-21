import os
import shutil
from pathlib import Path
from setuptools import setup, find_packages
from setuptools.command.install import install


class PostInstall(install):
    """Copy default config templates to ~/.nexgent/ on first install."""

    def run(self):
        install.run(self)
        dest = Path.home() / ".nexgent"
        dest.mkdir(exist_ok=True)
        pkg_root = Path(__file__).resolve().parent
        for src_name, dst_name in [
            (".env.example", ".env"),
            ("models.json.example", "models.json"),
        ]:
            src = pkg_root / src_name
            dst = dest / dst_name
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
                print(f"[nexgent] Installed default config: {dst}")


setup(
    name="nexgent",
    version="0.5.0",
    description="A production-grade model-agnostic AI agent harness, following Claude Code architecture patterns",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Agent Learning Hub",
    url="https://github.com/csxq0605/Nexgent",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
        "requests>=2.28.0",
        "tiktoken>=0.5.0",
        "prompt_toolkit>=3.0.0",
        "rich>=13.0.0",
        "textual>=0.40.0",
        "pyyaml>=6.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "nexgent=nexgent.cli:main",
        ],
    },
    cmdclass={"install": PostInstall},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
