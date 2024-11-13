# -*- encoding: utf-8 -*-
# Source: https://packaging.python.org/guides/distributing-packages-using-setuptools/

import io
import re

from setuptools import find_packages, setup

dev_requirements = [
    'bandit',
    'flake8',
    'isort',
    'pytest',
    'mock~=5.0.2',
    'mock-alchemy',

]
unit_test_requirements = [
    'pytest',
    'pytest-mock',
    'pytest-cov',
    'mock~=5.0.2',
    'mock-alchemy',

]
integration_test_requirements = [
    'pytest',
    'pytest-mock',
    'pytest-cov',
    'mock~=5.0.2',
    'mock-alchemy',

]
run_requirements = [
    'httpx~=0.25.1',
    'psycopg2-binary~=2.9.9',
    'urllib3~=2.2.0',
    'appdynamics~=24.7.0.6967',
    'fastapi[all]~=0.111.0',
    'fastapi-cli~=0.0.4',
    'networkx~=2.7.1',
    'pydantic',
    'pydantic_core',
    'pydantic-settings',
    'python-dotenv~=1.0.1',
    'requests',
    'SQLAlchemy',
]

with io.open('./sgs_caminho_critico/__init__.py', encoding='utf8') as version_f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")

with io.open('README.md', encoding='utf8') as readme:
    long_description = readme.read()

setup(
    name="sgs_caminho_critico",
    version=version,
    author="Banco do Brasil S.A.",
    author_email="ditec@bb.com.br",
    packages=find_packages(exclude='tests'),
    include_package_data=True,
    url="https://fontes.intranet.bb.com.br/sgs/sgs-caminho-critico/sgs-caminho-critico",
    license="COPYRIGHT",
    description="Constroi mapa de rotinas batch",
    long_description=long_description,
    zip_safe=False,
    install_requires=run_requirements,
    extras_require={
         'dev': dev_requirements,
         'unit': unit_test_requirements,
         'integration': integration_test_requirements,
    },
    python_requires='>=3.11',
    classifiers=[
        'Intended Audience :: Information Technology',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.11'
    ],
    keywords=(),
    entry_points={
        'console_scripts': [
            'sgs_caminho_critico = sgs_caminho_critico.__main__:start'
        ],
    },
)
