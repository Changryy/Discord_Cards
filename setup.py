#!/usr/bin/python
# -*- encoding: utf-8 -*-
from setuptools import setup, find_packages
import sys

version = '0.0.0'

if __name__ == '__main__':
    setup(
        name='discord-cards',
        version=version,
        description="discord bot for card games",
        long_description=open("README.md").read(),
        author='Sebastian Brox',
        author_email='c@changry.no',
        install_requires=['discord.py', 'emoji']
    )
