import os
import platform
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile

if sys.version[0] == '2':
    from urllib2 import urlopen
    input = raw_input
elif sys.version[0] == '3':
    from urllib.request import urlopen


class PhantomJSInstaller:
    def __init__(self):

        self.debian_deps = (
            'build-essential', 'g++', 'flex', 'bison', 'gperf', 'ruby', 'perl',
            'libsqlite3-dev', 'libfontconfig1-dev', 'libicu-dev', 'libfreetype6',
            'libssl-dev', 'libpng-dev', 'libjpeg-dev', 'ttf-mscorefonts-installer'
        )
        self.fedora_deps = (
            'gcc', 'gcc-c++', 'make', 'flex', 'bison', 'gperf', 'ruby',
            'openssl-devel', 'freetype-devel', 'fontconfig-devel',
            'libicu-devel', 'sqlite-devel', 'libpng-devel', 'libjpeg-devel'
        )
        self.build_cmds = (
            ('git', 'clone', 'git://github.com/ariya/phantomjs.git',),
            ('cd', 'phantomjs',),
            ('git', 'checkout', '2.0',),
            ('./build.sh',),
        )

        self.temp_dir = os.path.join(tempfile.gettempdir(), 'PhantomJS_install')
        try:
            os.mkdir(self.temp_dir)
        except:
            shutil.rmtree(self.temp_dir)
            os.mkdir(self.temp_dir)
        os.chdir(self.temp_dir)
        self.archive_path = os.path.join(self.temp_dir, 'phantomjs.zip')
        self.executable_path = None
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.url = None
        self.install_deps_cmd = []


        if os.name == 'nt' or platform.system() == 'Windows':
            self.url = 'https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.0.0-windows.zip'
            self.executable_path = os.path.join(self.base_dir, 'phantomjs.exe')
        elif os.name == 'mac' or platform.system() == 'Darwin':
            self.url = 'https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.0.0-macosx.zip'
            self.executable_path = os.path.join(self.base_dir, 'phantomjs')
        elif os.name == 'posix' or platform.system() == 'Linux':
            linux_name = platform.linux_distribution()[0]
            self.executable_path = os.path.join(self.base_dir, 'phantomjs')
            if linux_name in ('debian', 'Ubuntu',):
                self.install_deps_cmd.extend(('sudo', 'apt-get', 'install',))
                self.install_deps_cmd.extend(self.debian_deps)
            elif linux_name in ('fedora', 'redhat',):
                self.install_deps_cmd.extend(('sudo', 'yum', '-y', 'install',))
                self.install_deps_cmd.extend(self.fedora_deps)

        try:
            os.remove(self.executable_path)
        except:
            pass

    def fetch_archive(self):
        print('\n\nFetching archive...\n')

        req = urlopen(self.url)
        with open(self.archive_path, 'wb') as archive:
            while True:
                chunk = req.read(1024)
                if chunk:
                    archive.write(chunk)
                    archive.flush()
                else:
                    break

    def extract_archive(self):
        print('\nExtracting executable from archive...\n')

        with ZipFile(self.archive_path) as archive,\
                open(self.executable_path, 'wb') as executable:
            for name in archive.namelist():
                if '/bin/phantomjs' in name:
                    executable.write(archive.read(name))
                    break

    def install_deps(self):
        print('\n\nInstalling dependencies...\n')
        subprocess.call(self.install_deps_cmd)

    def build(self):
        print('\nCompiling...\n')

        for cmd in self.build_cmds:
            print('\n>>> Running command: {}\n\n'.format(' '.join(cmd)))
            if cmd[0] == 'cd':
                os.chdir(cmd[1])
                continue
            subprocess.call(cmd)

    def cleanup(self):
        try:
            os.chdir(os.path.dirname(self.executable_path))
            shutil.rmtree(self.temp_dir)
        except:
            pass

    def run(self):
        s = ('\n\nTo see how to manually install PhantomJS, please go to\n'
             'https://github.com/Ofekmeister/katutil\n\n')

        choice = input('\n\nAutomatically install PhantomJS? (y/n) ')
        if choice in ('n', 'no'):
            print(s)
            return

        try:
            if self.executable_path is not None:
                if self.url is not None:
                    self.fetch_archive()
                    self.extract_archive()
                else:
                    self.install_deps()
                    self.build()
                    shutil.move('bin/phantomjs', self.executable_path)
            else:
                input('\nUnknown operating system, automatic installation '
                      'failed.{}'.format(s))
            self.cleanup()
        except:
            input('\nAn error occurred, automatic installation '
                  'failed.{}'.format(s))
            self.cleanup()
            raise


if __name__ == '__main__':
    inst = PhantomJSInstaller()
    inst.run()




