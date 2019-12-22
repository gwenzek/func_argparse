from pathlib import Path

from setuptools import setup

with open(Path(__file__).parent / "README.md") as f:
    long_description = f.read()

setup(
    name="func_argparse",
    description="Generate CLI ArgumentParser from a function signature.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gwenzek/func_argparse",
    version="1.1.1",
    author="gwenzek",
    packages=["func_argparse"],
    license="BSD",
    install_requires=[],
    # Mark the package as compatible with types.
    # https://mypy.readthedocs.io/en/latest/installed_packages.html#making-pep-561-compatible-packages
    package_data={"func_argparse": ["py.typed"]},
    zip_safe=False,
    extras_require={"dev": ["mypy>=0.730", "pytest", "black", "isort"]},
)
