from setuptools import setup, find_packages

setup(
    name="multiwall",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyGObject",
        "python-i18n",
    ],
    package_data={
        "multiwall": ["translations/*.json"],
    },
    entry_points={
        "console_scripts": [
            "multiwall=multiwall.main:main",
        ],
    },
)