import errno
import glob
import logging
import os
import subprocess

import setuptools


def get_data_files(dirname, file_pattern="*.*"):
    return (dirname, glob.glob("%s/%s" % (dirname, file_pattern)))


if __name__ == "__main__":
    # Build paths inside the project like this: os.path.join(BASE_DIR, ...)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    setuptools.setup(
        name="pagoda",
        version="1.0.0",
        packages=setuptools.find_packages(),
        data_files=[
            get_data_files("airone/lib"),
        ],
    )
