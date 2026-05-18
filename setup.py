from setuptools import setup, find_packages
from multiwall import __version__

setup(
    name="multiwall",
    version=__version__,
    packages=find_packages(),
    install_requires=[
        "PyGObject",
        "Pillow",
        "pyyaml",
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