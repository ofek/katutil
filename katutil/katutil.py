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


import re
import sys
import os
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

if sys.version[0] == '2':
    _input = raw_input
elif sys.version[0] == '3':
    _input = input


def get_input(raw_string, message):
    temp = 0
    while not temp:
        temp = _input(message)
        if not re.match(raw_string, temp):
            temp = 0
        else:
            return temp


def get_lines(temp_file, line_num):
    with open(temp_file, 'r') as f:
        lines = f.readlines()
    if line_num == 'a':
        return lines
    elif line_num == 't':
        return [x.strip() for x in lines[4:] if x not in ('', '\n')]
    else:
        try:
            return lines[line_num - 1]
        except IndexError:
            return None


def write_file(temp_file, text, line_pos):
    if os.path.exists(temp_file):
        lines = get_lines(temp_file, 'a')
        num_lines = len(lines)
        with open(temp_file, 'w') as f:
            if line_pos == 't':
                f.write(''.join(lines[:4]))
                for line in text:
                    f.write('{}\n'.format(line))
            else:
                length = num_lines if num_lines > line_pos else line_pos
                line_pos -= 1
                for i in range(length):
                    if i == line_pos:
                        f.write('{}\n'.format(text))
                    else:
                        f.write('{}'.format(lines[i]))
    else:
        with open(temp_file, 'w') as f:
            length = line_pos
            line_pos -= 1
            for i in range(length):
                if i == line_pos:
                    f.write('{}\n'.format(text))
                else:
                    f.write('\n')


def check_enabled(element):
    if element and element.is_enabled() and element.is_displayed():
        return element
    else:
        return False


def get_driver(temp_file):
    path = None

    try:

        if os.path.exists(temp_file):
            path = get_lines(temp_file, 1)
            path = None if path is None else path.strip()
            if get_input(
                r'^(y|n|)$', '\n\nIs path "{}" correct (y/n)? '.format(path)
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
        _input('\n\nError loading phantomjs on path "{}". Press enter to quit...'.format(path))
        sys.exit()

    write_file(temp_file, path, 1)
    driver.set_window_size(1920, 1080)  # For reliable element loading
    return driver


def get_domain(temp_file, driver):
    valid_domain = r'^[a-zA-Z0-9.\-_]+$'
    main_title_text = 'KickassTorrents'
    domain = None
    previous_domain = get_lines(temp_file, 2)
    if previous_domain is not None:
        previous_domain = previous_domain.strip()

    while domain is None:
        domain = 'kickass.to' if previous_domain is None else previous_domain
        t = get_input(r'^(y|n|)$', '\n\nIs KAT domain still "{}" (y/n)? '.format(domain))
        if t == 'n':
            domain = get_input(valid_domain, '\n\nEnter new domain: ')
        print('\n\nChecking domain...\n')

        driver.get('https://{}/'.format(domain))
        if main_title_text not in driver.title:
            t = get_input(r'^(y|n)$', '\n\nUnverified domain, try another (y/n)? ')
            if t == 'y':
                domain = None
                continue
            else:
                driver.quit()
                _input('\n\nPress enter to quit...')
                sys.exit()

    if domain != previous_domain:
        write_file(temp_file, domain, 2)
    return domain


def get_user(temp_file, driver, domain, timeout):
    valid_user = r'^[a-zA-Z0-9\[\]$.\-_]+$'
    upload_url = 'https://{}/usearch/user:{{}}/'.format(domain)
    user = None
    previous_user = get_lines(temp_file, 3)
    if previous_user is not None:
        previous_user = previous_user.strip()

    while user is None:
        user = 'change_me' if previous_user is None else previous_user
        t = get_input(r'^(y|n|)$', '\n\nIs username "{}" (y/n)? '.format(user))
        if t == 'n':
            user = get_input(valid_user, '\n\nEnter new user: ')
        print('\n\nValidating user...\n')

        driver.get(upload_url.format(user))
        main_area = WebDriverWait(driver, timeout).until(
            lambda x:
                check_enabled(
                    x.find_element_by_class_name('mainpart')
                    .find_elements_by_tag_name('td')[0]
                )
        )

        try:
            error_text = main_area.find_element_by_class_name('errorpage').text
            if 'by {}'.format(user) in error_text:
                t = get_input(r'^(y|n)$', '\n\nUser has no uploads, try another (y/n)? ')
                if t == 'y':
                    user = None
                    continue
                else:
                    driver.quit()
                    _input('\n\nPress enter to quit...')
                    sys.exit()
            else:
                t = get_input(r'^(y|n)$', '\n\nUnregistered user, try another (y/n)? ')
                if t == 'y':
                    user = None
                    continue
                else:
                    driver.quit()
                    _input('\n\nPress enter to quit...')
                    sys.exit()
        except SystemExit:
            sys.exit()
        except NoSuchElementException:
            pass

    if user != previous_user:
        write_file(temp_file, user, 3)
    return user


def get_urls(driver, domain, user, timeout):
    upload_url = 'https://{}/usearch/user:{}/'.format(domain, user)
    if driver.current_url != upload_url:
        driver.get(upload_url)

    try:
        num_pages = int(WebDriverWait(driver, timeout).until(
            lambda x:
                check_enabled(
                    x.find_element_by_class_name('pages')
                    .find_elements_by_tag_name('a')[-1]
                )
        ).text)
    except TimeoutException:
        num_pages = 1

    print('\n\nFetching all torrent urls, this may take a while...\n')
    urls = []

    for i in range(1, num_pages + 1):
        driver.get('{}{}/?field=time_add&sorder=desc'.format(upload_url, i))
        links = WebDriverWait(driver, timeout).until(
            lambda x: x.find_elements_by_class_name('cellMainLink')
        )
        urls.extend(['{}#technical'.format(x.get_attribute('href')) for x in links])
        print('\nFound {} url(s)...'.format(len(urls)))

    return urls


def refresh_trackers(driver, urls, num_torrents, timeout):
    errors = []
    text = ''
    print('\n\nRefreshing torrents, this may take a while...\n\n')

    for i, url in enumerate(urls):
        time.sleep(1)
        try:
            text = '{}/{} - {}'.format(i + 1, num_torrents, url)
            print(text)

            driver.get(url)

            refresh_button = WebDriverWait(driver, timeout).until(
                lambda x:
                    check_enabled(
                        x.find_element_by_id('trackerBox')
                        .find_element_by_class_name('buttonsline')
                        .find_element_by_tag_name('button')
                    )
            )
            refresh_button.click()
        except TimeoutException:
            errors.append(text)

    num_errors = len(errors)
    num_successful = num_torrents - num_errors

    print('\n\nTorrents refreshed: {}\nErrors: {}\n\n'.format(num_successful, num_errors))
    if num_errors > 0:
        t = get_input(r'^(y|n|)$', 'Unable to refresh {} torrents. See which ones (y/n)? '.format(num_errors))
        if t != 'n':
            for error in errors:
                print('\n{}'.format(error))


def get_trackers(temp_file):
    valid_tracker = r'^[a-zA-Z0-9./:\-_]+$'
    previous_trackers = get_lines(temp_file, 't')
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
            t = get_input(r'^(y|n|)$', '\n\n{}\n\nUse above trackers (y/n)? '.format('\n'.join(trackers)))
        if t == 'n':
            choice = get_input(r"^(1|2|3|4)$", prompt)

            if choice == '1':
                tracker = get_input(valid_tracker, '\n\nEnter one new tracker: ')
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

    if trackers != previous_trackers:
        write_file(temp_file, trackers, 't')
    return '\n'.join(trackers)


def login(temp_file, driver, domain, user, timeout):
    valid_email = r'^[^\s]{1,128}$'
    valid_password = r'^[^\s]{1,128}$'
    login_url = 'https://{}/auth/login/'.format(domain)
    about_url = 'https://{}/about/'.format(domain)
    email = None
    previous_email = get_lines(temp_file, 4)
    if previous_email is not None:
        previous_email = previous_email.strip()

    while email is None:
        email = 'change@me.now' if previous_email is None else previous_email
        t = get_input(r'^(y|n|)$', '\n\nUse email "{}" (y/n)? '.format(email))
        if t == 'n':
            email = get_input(valid_email, '\n\nEnter new email: ')
        password = get_input(valid_password, '\n\nEnter password (never saved): ')

        try:
            driver.get(login_url)
            if driver.current_url == login_url:
                try:  # sometimes KAT renders regular form
                    email_field = WebDriverWait(driver, timeout).until(
                        lambda x:
                            check_enabled(
                                x.find_element_by_id('field_email')
                            )
                    )
                    password_field = WebDriverWait(driver, timeout).until(
                        lambda x:
                            check_enabled(
                                x.find_element_by_id('field_password')
                            )
                    )
                except TimeoutException:  # other times KAT renders mobile form
                    email_field = WebDriverWait(driver, timeout).until(
                        lambda x:
                            check_enabled(
                                x.find_element_by_name('email')
                            )
                    )
                    password_field = WebDriverWait(driver, timeout).until(
                        lambda x:
                            check_enabled(
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
                return False

        driver.get(about_url)
        if user not in driver.page_source:
            t = get_input(r'^(y|n)$', '\n\nIncorrent email or password, try another (y/n)? ')
            if t == 'y':
                email = None
                continue
            else:
                return False

    if email != previous_email:
        write_file(temp_file, email, 4)
    return True


def edit_trackers(driver, urls, num_torrents, trackers, timeout):
    errors = []
    text = ''
    print('\n\nEditing trackers, this may take a while...\n\n')

    for i, url in enumerate(urls):
        time.sleep(1)
        try:
            text = '{}/{} - {}'.format(i + 1, num_torrents, url)

            driver.get(url)

            edit_button = WebDriverWait(driver, timeout).until(
                lambda x:
                    check_enabled(
                        x.find_element_by_id('trackerBox')
                        .find_element_by_class_name('buttonsline')
                        .find_element_by_tag_name('a')
                    )
            )
            url = edit_button.get_attribute('href')

            text = '{}/{} - {}'.format(i + 1, num_torrents, url)
            print(text)

            driver.get(url)

            tracker_field = WebDriverWait(driver, timeout).until(
                lambda x:
                    check_enabled(
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
    num_successful = num_torrents - num_errors

    print('\n\nTorrents edited: {}\nErrors: {}\n\n'.format(num_successful, num_errors))
    if num_errors > 0:
        t = get_input(r'^(y|n|)$', 'Unable to edit {} torrents. See which ones (y/n)? '.format(num_errors))
        if t != 'n':
            for error in errors:
                print('\n{}'.format(error))


def main():

    try:
        timeout = int(sys.argv[1])
    except IndexError:
        timeout = 20
    temp_file = os.path.join(tempfile.gettempdir(), 'katutil_temp_6108589.txt')
    driver = get_driver(temp_file)
    domain = get_domain(temp_file, driver)
    user = get_user(temp_file, driver, domain, timeout)
    urls = get_urls(driver, domain, user, timeout)
    num_torrents = len(urls)

    prompt = ('\n\nPlease choose an option:\n\n'
              '\t1 - Refresh all trackers\n'
              '\t2 - Edit all trackers\n'
              '\tq - Quit\n\n'
              '\t==>  ')

    choice = None

    while choice != 'q':
        choice = get_input(r"^(1|2|q)$", prompt)

        if choice == '1':
            refresh_trackers(driver, urls, num_torrents, timeout)
        elif choice == '2':
            login_succeeded = login(temp_file, driver, domain, user, timeout)
            if login_succeeded:
                trackers = get_trackers(temp_file)
                edit_trackers(driver, urls, num_torrents, trackers, timeout)
            else:
                print('\n\nCannot edit trackers without logging in.')

    driver.quit()
