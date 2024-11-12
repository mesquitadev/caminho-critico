# -*- encoding: utf-8 -*-
# Source: https://packaging.python.org/guides/distributing-packages-using-setuptools/
import configparser
import io
import os
import re

from setuptools import find_packages, setup

dev_requirements = [
    'bandit',
    'flake8',
    'isort',
    'pytest',
]
unit_test_requirements = [
    'pytest',
    'fastapi',
    'requests',
    'sqlalchemy',
    'pytest-mock',
    'pytest-cov',
]
integration_test_requirements = [
    'pytest',
]
run_requirements = [
    'anytree',
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


# Função para carregar variáveis de ambiente do pytest.ini
def load_env_from_pytest_ini():
    config = configparser.ConfigParser()
    config.read('pytest.ini')
    if 'pytest' in config:
        for key, value in config['pytest'].items():
            if key.startswith('env_'):
                env_var = key[4:].upper()
                os.environ[env_var] = value


# Carregar variáveis de ambiente do pytest.ini
load_env_from_pytest_ini()

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
    python_requires='>=3.6',
    classifiers=[
        'Intended Audience :: Information Technology',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6'
    ],
    keywords=(),
    entry_points={
        'console_scripts': [
            'sgs_caminho_critico = sgs_caminho_critico.__main__:start'
        ],
    },
)
