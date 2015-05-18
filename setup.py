import os
import subprocess
import sys
from setuptools import setup, find_packages
from setuptools.command.install import install

with open('README.rst', 'r') as infile:
    read_me = infile.read()

def caller():
    install_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'katutil',
            'install.py',
        )
    subprocess.call((sys.executable, install_script,), shell=True)


class AutoInstall(install):
    def run(self):
        install.run(self)
        self.execute(caller)


setup(
    name='katutil',
    version='0.7',
    description='utilities for automating tasks on KickassTorrents',
    long_description=read_me,
    author='Ofek Lev',
    author_email='ofekmeister@gmail.com',
    maintainer='Ofek Lev',
    maintainer_email='ofekmeister@gmail.com',
    url='https://github.com/Ofekmeister/katutil',
    license='MIT',
    platforms=None,

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

    setup_requires=['selenium==2.45.0'],
    install_requires=['selenium==2.45.0'],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'katutil = katutil.katutil:main',
        ],
    },
    cmdclass={'install': AutoInstall},
)
