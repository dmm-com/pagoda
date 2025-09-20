#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name="airone-hello-world-plugin",
    version="1.0.0",
    description="Hello World Plugin for AirOne",
    long_description="""
    A sample plugin demonstrating how to create external plugins for AirOne.
    This plugin provides basic API endpoints and showcases the plugin system capabilities.
    """,
    author="AirOne Development Team",
    author_email="dev@airone.io",
    url="https://github.com/dmm-com/airone",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pagoda-plugin-sdk>=1.0.0",
        "Django>=3.2",
        "djangorestframework>=3.12",
    ],
    entry_points={
        "airone.plugins": [
            "hello-world = airone_hello_world_plugin.plugin:HelloWorldPlugin",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    keywords="airone plugin development api",
    include_package_data=True,
    zip_safe=False,
)
