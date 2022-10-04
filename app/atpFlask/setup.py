#!/usr/bin/env python3

from distutils.core import setup


setup(name='atp_flask',
      version='1.0',
      description='Helper to use ATP from a flask application',
      author='Sebastian Waisbrot',
      author_email='sebastian.waisbrot@despegar.com',
      url='https://github.com/despegar/atpFlask',
      packages=['atp_flask'],
      install_requires=['flask', 'requests', 'python-jose'],
     )
