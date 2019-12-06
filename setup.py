#!/usr/bin/env python

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = [
    "aarghparse==0.2.0",
    "cached-property",
    "beautifulsoup4",
    "requests",
]

setup_requirements = ["pytest-runner", ]

test_requirements = ["pytest>=3", ]

setup(
    author="Jazeps Basko",
    author_email="jazeps.basko@gmail.com",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="GM standings and fixtures parser",
    install_requires=requirements,
    license="BSD license",
    long_description=readme,
    include_package_data=True,
    keywords="unicorner",
    name="unicorner",
    packages=find_packages(include=["unicorner", "unicorner.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/zilupe/unicorner",
    version="0.3.2",
    zip_safe=False,
)
