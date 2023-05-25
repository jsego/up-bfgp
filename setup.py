#!/usr/bin/env python3
import subprocess

from setuptools import setup  # type: ignore
from setuptools.command.build_py import build_py  # type: ignore
from setuptools.command.develop import develop  # type: ignore
import os
import urllib
import shutil


BFGP_dst = "./up_bfgp/bfgp_pp"
BFGP_PUBLIC = "bfgp-pp"
COMPILE_CMD = './scripts/compile.sh'
BFGP_TAG = "main"
BFGP_REPO = "https://github.com/jsego/bfgp-pp"
PKG_NAME = "up_bfgp"

def install_BFGP():
    shutil.rmtree(BFGP_dst, ignore_errors=True)
    subprocess.run(["git", "clone", "-b", BFGP_TAG, BFGP_REPO])
    shutil.move(BFGP_PUBLIC, BFGP_dst)
    curr_dir = os.getcwd()
    os.chdir(BFGP_dst)
    subprocess.run(COMPILE_CMD, shell=True)
    os.chdir(curr_dir)


class InstallBFGP(build_py):
    """Custom installation command."""

    def run(self):
        install_BFGP()
        build_py.run(self)


class InstallBFGPdevelop(develop):
    """Custom installation command."""

    def run(self):
        install_BFGP()
        develop.run(self)


setup(
    name=PKG_NAME,
    version='0.0.1',
    description=PKG_NAME,
    author="Javier Segovia-Aguas, Sergio Jiménez and Anders Jonsson",
    author_email="javier.segovia@upf.edu",
    packages=[PKG_NAME],
    package_data={
        "": ['bfgp_pp/main.bin',
             'bfgp_pp/preprocess/pddl_translator.py']
    },
    cmdclass={"build_py": InstallBFGP, "develop": InstallBFGPdevelop},
    license="GNUv3",
)