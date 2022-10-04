from setuptools import setup

requirements = [
    'Flask',
    'Flask-Cors'
]

setup(
    name='enc_sec',
    version='1.0.0',
    packages=['conf', 'commons', 'commons.utils', 'commons.connectors', 'commons.repositories',
              'commons.repositories.sql', 'github_to_ldap'],
    url='https://github.com/despegar/enc_sec',
    license='MIT',
    author='AppSec',
    author_email='AppSec@despegar.com',
    description='',
    install_requires=requirements
)
