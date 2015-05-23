# The MIT License (MIT)
#
# Copyright (c) 2015 Ofek Lev
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time
from .install import PhantomJSInstaller
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

if sys.version[0] == '2':
    input = raw_input


def get_input(raw_string, message):
    temp = 0
    while not temp:
        temp = input(message)
        if not re.match(raw_string, temp):
            temp = 0
        else:
            return temp


class KATInterface:
    def __init__(self, timeout=20, temp_file=None):
        self.timeout = timeout or 20
        self.temp_file = temp_file or os.path.join(tempfile.gettempdir(), 'katutil_temp_6108589.txt')
        self.saved_data = dict()
        self.driver = None
        self.domain = None
        self.user = None
        self.is_authenticated = False
        self.urls = []
        self.num_torrents = 0

        self.valid_domain = r'^[a-zA-Z0-9.\-_]+$'
        self.valid_user = r'^[a-zA-Z0-9\[\]$.\-_]+$'
        self.valid_email = r'^[^\s]{1,128}$'
        self.valid_password = r'^[^\s]{1,128}$'
        self.valid_tracker = r'^[a-zA-Z0-9./:\-_]+$'
        self.base_upload_url = 'https://{}/usearch/user:{{}}/'
        self.base_login_url = 'https://{}/auth/login/'
        self.base_about_url = 'https://{}/about/'

    def connect(self):
        self.load_saved_data()
        self.get_phantomjs()
        self.get_domain()
        self.get_user()
        self.get_urls()

    def get_phantomjs(self):

        here = os.path.dirname(os.path.abspath(__file__))
        auto_install_path = None
        for file in os.listdir(here):
            if 'phantomjs' in file:
                auto_install_path = os.path.join(here, file)

        previous_path = self.saved_data.get('phantomjs')
        path = None
        driver = None

        while path is None:
            try:
                path = previous_path or auto_install_path

                if get_input(
                    r'^(y|n|)$', '\n\nIs path "{}" correct? (y/n) '.format(path)
                ) == 'n':
                    path = None

                if path is None:
                    path = get_input(
                        r'^[a-zA-Z0-9\\/:\-\'\.\(\)!&_ ]+$',
                        '\n\nEnter path to executable. Examples:\n\n'
                        '\t==> Windows - "C:\\phantomjs\\phantomjs.exe"\n'
                        '\t==> OS X - "/bin/phantomjs"\n'
                        '\t==> Linux - "phantomjs"\n\n'
                    )

                driver = webdriver.PhantomJS(path)

            except WebDriverException:
                t = get_input(
                    r'^(y|n)$',
                    '\n\nError loading phantomjs on path "{}".'
                    ' Try again? (y/n) '.format(path)
                )
                if t == 'y':
                    path = None
                    continue
                else:
                    input('\n\nPress enter to quit...')
                    sys.exit()

        self.saved_data['phantomjs'] = path
        self.update_saved_data()
        self.driver = driver
        self.driver.set_window_size(1920, 1080)  # For reliable element loading

    def get_domain(self):
        previous_domain = self.saved_data.get('domain')
        domain = None

        while domain is None:
            t = get_input(r'^(y|n|)$', '\n\nIs KAT domain still "{}"? (y/n) '.format(previous_domain))
            if t == 'n':
                domain = get_input(self.valid_domain, '\n\nEnter new domain: ')
            else:
                domain = previous_domain
            print('\n\nChecking domain...\n')

            self.driver.get('https://{}/'.format(domain))
            if not self.has_kat_keywords(self.driver.title):
                t = get_input(r'^(y|n)$', '\n\nUnverified domain, try another? (y/n) ')
                if t == 'y':
                    domain = None
                    continue
                else:
                    self.quit()
                    input('\n\nPress enter to quit...')
                    sys.exit()

        if domain != previous_domain:
            self.saved_data['domain'] = domain
            self.update_saved_data()
        self.domain = domain

    def get_user(self):
        upload_url = self.base_upload_url.format(self.domain)
        previous_user = self.saved_data.get('user')
        user = None

        while user is None:
            t = get_input(r'^(y|n|)$', '\n\nIs username "{}" (y/n)? '.format(previous_user))
            if t == 'n':
                user = get_input(self.valid_user, '\n\nEnter new user: ')
            else:
                user = previous_user
            print('\n\nValidating user...\n')

            self.driver.get(upload_url.format(user))
            main_area = WebDriverWait(self.driver, self.timeout).until(
                lambda x:
                    self.check_enabled(
                        x.find_element_by_class_name('mainpart')
                        .find_elements_by_tag_name('td')[0]
                    )
            )

            try:
                error_text = main_area.find_element_by_class_name('errorpage').text
                if 'by {}'.format(user) in error_text:
                    t = get_input(r'^(y|n)$', '\n\nUser has no uploads, try another? (y/n) ')
                    if t == 'y':
                        user = None
                        continue
                    else:
                        self.driver.quit()
                        input('\n\nPress enter to quit...')
                        sys.exit()
                else:
                    t = get_input(r'^(y|n)$', '\n\nUnregistered user, try another (y/n)? ')
                    if t == 'y':
                        user = None
                        continue
                    else:
                        self.driver.quit()
                        input('\n\nPress enter to quit...')
                        sys.exit()
            except SystemExit:
                sys.exit()
            except NoSuchElementException:
                pass

        if user != previous_user:
            self.saved_data['user'] = user
            self.update_saved_data()
        self.user = user

    def get_urls(self):
        upload_url = self.base_upload_url.format(self.domain).format(self.user)
        if self.driver.current_url != upload_url:
            self.driver.get(upload_url)

        try:
            num_pages = int(WebDriverWait(self.driver, self.timeout).until(
                lambda x:
                    self.check_enabled(
                        x.find_element_by_class_name('pages')
                        .find_elements_by_tag_name('a')[-1]
                    )
            ).text)
        except TimeoutException:
            num_pages = 1

        print('\n\nFetching all torrent urls, this may take a while...\n')
        urls = []

        for i in range(1, num_pages + 1):
            self.driver.get('{}{}/?field=time_add&sorder=desc'.format(upload_url, i))
            links = WebDriverWait(self.driver, self.timeout).until(
                lambda x: x.find_elements_by_class_name('cellMainLink')
            )
            urls.extend(['{}#technical'.format(x.get_attribute('href')) for x in links])
            print('\nFound {} url(s)...'.format(len(urls)))

        self.urls = urls
        self.num_torrents = len(urls)

    def refresh_trackers(self):
        errors = []
        text = ''
        print('\n\nRefreshing torrents, this may take a while...\n\n')

        for i, url in enumerate(self.urls):
            time.sleep(1)
            try:
                text = '{}/{} - {}'.format(i + 1, self.num_torrents, url)
                print(text)

                self.driver.get(url)

                refresh_button = WebDriverWait(self.driver, self.timeout).until(
                    lambda x:
                        self.check_enabled(
                            x.find_element_by_id('trackerBox')
                            .find_element_by_class_name('buttonsline')
                            .find_element_by_tag_name('button')
                        )
                )
                refresh_button.click()
            except TimeoutException:
                errors.append(text)

        num_errors = len(errors)
        num_successful = self.num_torrents - num_errors

        print('\n\nTorrents refreshed: {}\nErrors: {}\n\n'.format(num_successful, num_errors))
        if num_errors > 0:
            t = get_input(r'^(y|n|)$', 'Unable to refresh {} torrents. See which ones (y/n)? '.format(num_errors))
            if t != 'n':
                for error in errors:
                    print('\n{}'.format(error))

    def login(self):
        login_url = self.base_login_url.format(self.domain)
        about_url = self.base_about_url.format(self.domain)
        previous_email = self.saved_data.get('email')
        email = None

        while email is None:
            t = get_input(r'^(y|n|)$', '\n\nUse email "{}" (y/n)? '.format(previous_email))
            if t == 'n':
                email = get_input(self.valid_email, '\n\nEnter new email: ')
            else:
                email = previous_email
            password = get_input(self.valid_password, '\n\nEnter password (never saved): ')

            try:
                self.driver.get(login_url)
                if self.driver.current_url == login_url:
                    try:  # sometimes KAT renders regular form
                        email_field = WebDriverWait(self.driver, self.timeout).until(
                            lambda x:
                                self.check_enabled(
                                    x.find_element_by_id('field_email')
                                )
                        )
                        password_field = WebDriverWait(self.driver, self.timeout).until(
                            lambda x:
                                self.check_enabled(
                                    x.find_element_by_id('field_password')
                                )
                        )
                    except TimeoutException:  # other times KAT renders mobile form
                        email_field = WebDriverWait(self.driver, self.timeout).until(
                            lambda x:
                                self.check_enabled(
                                    x.find_element_by_name('email')
                                )
                        )
                        password_field = WebDriverWait(self.driver, self.timeout).until(
                            lambda x:
                                self.check_enabled(
                                    x.find_element_by_name('password')
                                )
                        )
                    print('\n\nLogging in, please wait...')
                    email_field.send_keys(email)
                    password_field.send_keys(password)
                    password_field.submit()
            except TimeoutException:
                t = get_input(r'^(y|n)$', '\n\nError loading login form, try again (y/n)? ')
                if t == 'y':
                    email = None
                    continue
                else:
                    self.is_authenticated = False
                    return

            self.driver.get(about_url)
            if self.user not in self.driver.page_source:
                t = get_input(r'^(y|n)$', '\n\nIncorrent email or password, try another (y/n)? ')
                if t == 'y':
                    email = None
                    continue
                else:
                    self.is_authenticated = False
                    return

        if email != previous_email:
            self.saved_data['email'] = email
            self.update_saved_data()
        self.is_authenticated = True

    def get_trackers(self):
        previous_trackers = self.saved_data.get('trackers', [])
        trackers = list(previous_trackers)
        prompt = ('\n\nPlease choose an option:\n\n'
                  '\t1 - Add a tracker\n'
                  '\t2 - Remove a tracker\n'
                  '\t3 - Remove all trackers\n'
                  '\t4 - Restore previous trackers\n\n'
                  '\t==>  ')

        t = 'n'
        while t == 'n':
            if len(trackers) > 0:
                t = get_input(r'^(y|n|)$', '\n\n{}\n\nUse above trackers? (y/n) '.format('\n'.join(trackers)))
            if t == 'n':
                choice = get_input(r"^(1|2|3|4)$", prompt)

                if choice == '1':
                    tracker = get_input(self.valid_tracker, '\n\nEnter one new tracker: ')
                    trackers.append(tracker)
                elif choice == '2':
                    if len(trackers) == 0:
                        print('\n\nNo trackers')
                    else:
                        s = '\n'.join(['{} - {}'.format(x + 1, y) for x, y in enumerate(trackers)])
                        num = get_input(
                            r'^({})$'.format('|'.join([str(i + 1) for i in range(len(trackers))])),
                            '\n\n{}\n\nRemove which tracker? '.format(s)
                        )
                        trackers.pop(int(num) - 1)
                elif choice == '3':
                    trackers.clear()
                elif choice == '4':
                    trackers = list(previous_trackers)

        self.saved_data['trackers'] = trackers
        self.update_saved_data()

    def edit_trackers(self):
        self.get_trackers()
        trackers = self.saved_data['trackers']
        errors = []
        text = ''
        print('\n\nEditing trackers, this may take a while...\n\n')

        for i, url in enumerate(self.urls):
            time.sleep(1)
            try:
                text = '{}/{} - {}'.format(i + 1, self.num_torrents, url)

                self.driver.get(url)

                edit_button = WebDriverWait(self.driver, self.timeout).until(
                    lambda x:
                        self.check_enabled(
                            x.find_element_by_id('trackerBox')
                            .find_element_by_class_name('buttonsline')
                            .find_element_by_tag_name('a')
                        )
                )
                url = edit_button.get_attribute('href')

                text = '{}/{} - {}'.format(i + 1, self.num_torrents, url)
                print(text)

                self.driver.get(url)

                tracker_field = WebDriverWait(self.driver, self.timeout).until(
                    lambda x:
                        self.check_enabled(
                            x.find_element_by_class_name('mainpart')
                            .find_element_by_tag_name('textarea')
                        )
                )
                tracker_field.clear()
                tracker_field.send_keys(trackers)
                tracker_field.submit()

            except TimeoutException:
                errors.append(text)

        num_errors = len(errors)
        num_successful = self.num_torrents - num_errors

        print('\n\nTorrents edited: {}\nErrors: {}\n\n'.format(num_successful, num_errors))
        if num_errors > 0:
            t = get_input(r'^(y|n|)$', 'Unable to edit {} torrents. See which ones (y/n)? '.format(num_errors))
            if t != 'n':
                for error in errors:
                    print('\n{}'.format(error))

    def load_saved_data(self):
        try:
            with open(self.temp_file, 'r') as f:
                self.saved_data.update(json.load(f))
        except:
            pass

    def update_saved_data(self):
        with open(self.temp_file, 'w') as f:
            json.dump(self.saved_data, f)

    def has_kat_keywords(self, s):
        if re.search(r"kat|kickass|torrent", s, re.I):
            return True
        else:
            return False

    def check_enabled(self, element):
        if element and element.is_enabled() and element.is_displayed():
            return element
        else:
            return False

    def quit(self):
        self.update_saved_data()
        self.driver.quit()


def install():
    inst = PhantomJSInstaller()
    inst.run()
    sys.exit()

def save_executable():
    here = os.path.dirname(os.path.abspath(__file__))
    for file in os.listdir(here):
        if 'phantomjs' in file:
            shutil.move(
                os.path.join(here, file),
                os.path.join(tempfile.gettempdir(), 'katutil_temp_6108589_{}'.format(file))
            )
    sys.exit()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--timeout', type=int, default=None)
    parser.add_argument('--install', action='store_const', const='install')
    parser.add_argument('--save', action='store_const', const='save')
    c_args = vars(parser.parse_args())

    if c_args['install'] is not None:
        install()
    elif c_args['save'] is not None:
        save_executable()

    ki = KATInterface(c_args['timeout'])
    ki.connect()

    prompt = ('\n\nPlease choose an option:\n\n'
              '\t1 - Refresh all trackers\n'
              '\t2 - Edit all trackers\n'
              '\tq - Quit\n\n'
              '\t==>  ')

    choice = None

    while choice != 'q':
        choice = get_input(r"^(1|2|q)$", prompt)

        if choice == '1':
            ki.refresh_trackers()
        elif choice == '2':
            ki.login()
            if ki.is_authenticated:
                ki.edit_trackers()
            else:
                print('\n\nCannot edit trackers without logging in.')

    ki.quit()
