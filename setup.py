from setuptools import setup
from pathlib import Path


with open(Path(__file__).parent / "README.md") as f:
    long_description = f.read()

setup(
    name="func_argparse",
    description="Generate CLI ArgumentParser from a function signature.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gwenzek/func_argparse",
    version="1.0.3",
    author="gwenzek",
    packages=["func_argparse"],
    license="BSD",
    install_requires=[],
    # Mark the package as compatible with types.
    # https://mypy.readthedocs.io/en/latest/installed_packages.html#making-pep-561-compatible-packages
    package_data={"func_argparse": ["py.typed"]},
    zip_safe=False,
)
