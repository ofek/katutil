from setuptools import setup, find_packages

setup(
    name='katutil',
    version='1.1',
    description='utilities for automating tasks on KickassTorrents',
    author='Ofek Lev',
    author_email='ofekmeister@gmail.com',
    maintainer='Ofek Lev',
    maintainer_email='ofekmeister@gmail.com',
    url='https://github.com/Ofekmeister/katutil',

    install_requires=['selenium==2.44.0'],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'katutil = katutil.katutil:main',
        ],
    }
)
