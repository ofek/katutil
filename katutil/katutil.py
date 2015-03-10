import re
import sys
import os
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if sys.version[0] == '2':
    _input = raw_input
elif sys.version[0] == '3':
    _input = input


def getInput(raw_string, message):

    temp = 0
    while not temp:

        temp = _input(message)

        if not re.match(raw_string, temp):
            temp = 0
        else:
            return temp


def getLines(tempFile, lineNum):
    with open(tempFile, 'r') as f:
        lines = f.readlines()
    if lineNum == 'a':
        return lines
    elif lineNum == 't':
        try:
            return [x.strip() for x in lines[4:] if x not in ('', '\n')]
        except:
            return None
    else:
        try:
            return lines[lineNum - 1]
        except:
            return None


def writeFile(tempFile, text, linePosition):
    if os.path.exists(tempFile):
        lines = getLines(tempFile, 'a')
        numLines = len(lines)
        with open(tempFile, 'w') as f:
            if linePosition == 't':
                f.write(''.join(lines[:4]))
                for line in text:
                    f.write('{}\n'.format(line))
            else:
                length = numLines if numLines > linePosition else linePosition
                linePosition -= 1
                for i in range(length):
                    if i == linePosition:
                        f.write('{}\n'.format(text))
                    else:
                        f.write('{}'.format(lines[i]))
    else:
        with open(tempFile, 'w') as f:
            length = linePosition
            linePosition -= 1
            for i in range(length):
                if i == linePosition:
                    f.write('{}\n'.format(text))
                else:
                    f.write('\n')


def getDriver(tempFile):
    path = None

    try:

        if os.path.exists(tempFile):
            path = getLines(tempFile, 1)
            path = None if path is None else path.strip()
            if getInput(
                r'^(y|n|)$', '\n\nIs path "{}" correct (y/n)? '.format(path)
            ) == 'n':
                path = None

        if path is None:
            path = getInput(
                r'^[a-zA-Z0-9\\/:\-\'\.\(\)!&_ ]+$',
                '\n\nEnter path to executable. Examples:\n\n'
                '\t==> Windows - "C:\\phantomjs\\phantomjs.exe"\n'
                '\t==> OS X - "/bin/phantomjs"\n'
                '\t==> Linux - "phantomjs"\n\n'
            )
            writeFile(tempFile, path, 1)

        driver = webdriver.PhantomJS(path)

    except:
        input('\n\nError loading phantomjs on path "{}". Press enter to quit...'.format(path))
        sys.exit()

    driver.set_window_size(1920, 1080) # For reliable element loading
    return driver


def getDomain(tempFile, driver):
    validDomain = r'^[a-zA-Z0-9.\-_]+$'
    mainTitleText = 'KickassTorrents'
    domain = None
    previousDomain = getLines(tempFile, 2)
    if previousDomain is not None:
        previousDomain = previousDomain.strip()

    while domain is None:
        domain = 'kickass.to' if previousDomain is None else previousDomain
        t = getInput(r'^(y|n|)$', '\n\nIs KAT domain still "{}" (y/n)? '.format(domain))
        if t == 'n':
            domain = getInput(validDomain, '\n\nEnter new domain: ')
        print('\n\nChecking domain...\n')

        driver.get('https://{}/'.format(domain))
        if mainTitleText not in driver.title:
            t = getInput(r'^(y|n)$', '\n\nUnverified domain, try another (y/n)? ')
            if t == 'y':
                domain = None
                continue
            else:
                driver.quit()
                input('\n\nPress enter to quit...')
                sys.exit()

    if domain != previousDomain:
        writeFile(tempFile, domain, 2)
    return domain


def getUser(tempFile, driver, domain, timeout):
    validUser = r'^[a-zA-Z0-9\[\]$.\-_]+$'
    uploadUrl = 'https://{}/usearch/user:{{}}/'.format(domain)
    user = None
    previousUser = getLines(tempFile, 3)
    if previousUser is not None:
        previousUser = previousUser.strip()

    while user is None:
        user = 'change_me' if previousUser is None else previousUser
        t = getInput(r'^(y|n|)$', '\n\nIs username "{}" (y/n)? '.format(user))
        if t == 'n':
            user = getInput(validUser, '\n\nEnter new user: ')
        print('\n\nValidating user...\n')

        driver.get(uploadUrl.format(user))
        mainArea = WebDriverWait(driver, timeout).until(lambda x:x
            .find_element_by_class_name('mainpart')
            .find_elements_by_tag_name('td')
        )[0]

        try:
            errorText = mainArea.find_element_by_class_name('errorpage').text
            if 'by {}'.format(user) in errorText:
                t = getInput(r'^(y|n)$', '\n\nUser has no uploads, try another (y/n)? ')
                if t == 'y':
                    user = None
                    continue
                else:
                    driver.quit()
                    input('\n\nPress enter to quit...')
                    sys.exit()
            else:
                t = getInput(r'^(y|n)$', '\n\nUnregistered user, try another (y/n)? ')
                if t == 'y':
                    user = None
                    continue
                else:
                    driver.quit()
                    input('\n\nPress enter to quit...')
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

    if user != previousUser:
        writeFile(tempFile, user, 3)
    return user


def getUrls(driver, domain, user, timeout):
    uploadUrl = 'https://{}/usearch/user:{}/'.format(domain, user)
    if driver.current_url != uploadUrl:
        driver.get(uploadUrl)

    try:
        numPages = int(WebDriverWait(driver, timeout).until(
            lambda x:x.find_element_by_class_name('pages').find_elements_by_tag_name('a')
        )[-1].text)
    except:
        numPages = 1

    print('\n\nFetching all torrent urls, this may take a while...\n')
    urls = []

    for i in range(1, numPages + 1):
        driver.get('{}{}/?field=time_add&sorder=desc'.format(uploadUrl, i))
        links = WebDriverWait(driver, timeout).until(lambda x:x.find_elements_by_class_name('cellMainLink'))
        urls.extend(['{}#technical'.format(x.get_attribute('href')) for x in links])
        print('\nFound {} url(s)...'.format(len(urls)))

    return urls


def refreshTrackers(driver, urls, numTorrents, timeout):
    errors = []
    print('\n\nRefreshing torrents, this may take a while...\n\n')

    for i, url in enumerate(urls):
        time.sleep(3)
        try:
            text = '{}/{} - {}'.format(i + 1, numTorrents, url)
            print(text)

            driver.get(url)

            refreshButton = WebDriverWait(driver, timeout).until(lambda x:x
                .find_element_by_id('trackerBox')
                .find_element_by_class_name('buttonsline')
                .find_element_by_tag_name('button')
            )
            refreshButton.click()
        except:
            errors.append(text)

    numErrors = len(errors)
    numSuccessful = numTorrents - numErrors

    print('\n\nTorrents refreshed: {}\nErrors: {}\n\n'.format(numSuccessful, numErrors))
    if numErrors > 0:
        t = getInput(r'^(y|n|)$', 'Unable to refresh {} torrents. See which ones (y/n)? '.format(numErrors))
        if t != 'n':
            for error in errors:
                print('\n{}'.format(error))


def getTrackers(tempFile):
    validTracker = r'^[a-zA-Z0-9./:\-_]+$'
    previousTrackers = getLines(tempFile, 't')
    trackers = list(previousTrackers)
    prompt = ('\n\nPlease choose an option:\n\n'
              '\t1 - Add a tracker\n'
              '\t2 - Remove a tracker\n'
              '\t3 - Remove all trackers\n'
              '\t4 - Restore previous trackers\n\n'
              '\t==>  ')

    t = 'n'
    while t == 'n':
        if len(trackers) > 0:
            t = getInput(r'^(y|n|)$', '\n\n{}\n\nUse above trackers (y/n)? '.format('\n'.join(trackers)))
        if t == 'n':
            choice = getInput(r"^(1|2|3|4)$", prompt)

            if choice == '1':
                tracker = getInput(validTracker, '\n\nEnter one new tracker: ')
                trackers.append(tracker)
            elif choice == '2':
                if len(trackers) == 0:
                    print('\n\nNo trackers')
                else:
                    s = '\n'.join(['{} - {}'.format(x + 1, y) for x, y in enumerate(trackers)])
                    num = getInput(
                        r'^({})$'.format('|'.join([str(i + 1) for i in range(len(trackers))])),
                        '\n\n{}\n\nRemove which tracker? '.format(s)
                    )
                    trackers.pop(int(num) - 1)
            elif choice == '3':
                trackers.clear()
            elif choice == '4':
                trackers = list(previousTrackers)

    if trackers != previousTrackers:
        writeFile(tempFile, trackers, 't')
    return '\n'.join(trackers)


def login(tempFile, driver, domain, user, timeout):
    validEmail = r'^[^\s]{1,128}$'
    validPassword = r'^[^\s]{1,128}$'
    loginUrl = 'https://{}/auth/login/'.format(domain)
    aboutUrl = 'https://{}/about/'.format(domain)
    email = None
    previousEmail = getLines(tempFile, 4)
    if previousEmail is not None:
        previousEmail = previousEmail.strip()

    while email is None:
        email = 'change@me.now' if previousEmail is None else previousEmail
        t = getInput(r'^(y|n|)$', '\n\nUse email "{}" (y/n)? '.format(email))
        if t == 'n':
            email = getInput(validEmail, '\n\nEnter new email: ')
        password = getInput(validPassword, '\n\nEnter password (never saved): ')

        try:
            driver.get(loginUrl)
            if driver.current_url == loginUrl:
                try:
                    # sometimes KAT renders regular form
                    emailField = WebDriverWait(driver, timeout).until(
                        EC.element_to_be_clickable((By.ID, 'field_email'))
                    )
                    passwordField = WebDriverWait(driver, timeout).until(
                        EC.element_to_be_clickable((By.ID, 'field_password'))
                    )
                except:
                    # other times KAT renders mobile form
                    emailField = WebDriverWait(driver, timeout).until(
                        EC.element_to_be_clickable((By.NAME, 'email'))
                    )
                    passwordField = WebDriverWait(driver, timeout).until(
                        EC.element_to_be_clickable((By.NAME, 'password'))
                    )
                print('\n\nLogging in, please wait...')
                emailField.send_keys(email)
                passwordField.send_keys(password)
                passwordField.send_keys(Keys.RETURN)
        except:
            t = getInput(r'^(y|n)$', '\n\nError loading login form, try again (y/n)? ')
            if t == 'y':
                email = None
                continue
            else:
                return False

        driver.get(aboutUrl)
        if user not in driver.page_source:
            t = getInput(r'^(y|n)$', '\n\nIncorrent email or password, try another (y/n)? ')
            if t == 'y':
                email = None
                continue
            else:
                return False

    if email != previousEmail:
        writeFile(tempFile, email, 4)
    return True


def editTrackers(driver, urls, numTorrents, trackers, timeout):
    errors = []
    print('\n\nEditing trackers, this may take a while...\n\n')

    for i, url in enumerate(urls):
        time.sleep(3)
        try:
            text = '{}/{} - {}'.format(i + 1, numTorrents, url)

            driver.get(url)

            editButton = WebDriverWait(driver, timeout).until(lambda x:x
                .find_element_by_id('trackerBox')
                .find_element_by_class_name('buttonsline')
                .find_element_by_tag_name('a')
            )
            url = editButton.get_attribute('href')

            text = '{}/{} - {}'.format(i + 1, numTorrents, url)
            print(text)

            driver.get(url)

            trackerField = WebDriverWait(driver, timeout).until(lambda x:x
                .find_element_by_class_name('mainpart')
                .find_element_by_tag_name('textarea')
            )
            trackerField.clear()
            trackerField.send_keys(trackers)
            trackerField.submit()

        except:
            errors.append(text)

    numErrors = len(errors)
    numSuccessful = numTorrents - numErrors

    print('\n\nTorrents edited: {}\nErrors: {}\n\n'.format(numSuccessful, numErrors))
    if numErrors > 0:
        t = getInput(r'^(y|n|)$', 'Unable to edit {} torrents. See which ones (y/n)? '.format(numErrors))
        if t != 'n':
            for error in errors:
                print('\n{}'.format(error))


def main():

    try:
        timeout = int(sys.argv[1])
    except:
        timeout = 20
    tempFile = os.path.join(tempfile.gettempdir(), 'tracker_refresher_6108589.txt')
    driver = getDriver(tempFile)
    domain = getDomain(tempFile, driver)
    user = getUser(tempFile, driver, domain, timeout)
    urls = getUrls(driver, domain, user, timeout)
    numTorrents = len(urls)

    prompt = ('\n\nPlease choose an option:\n\n'
              '\t1 - Refresh all trackers\n'
              '\t2 - Edit all trackers\n'
              '\tq - Quit\n\n'
              '\t==>  ')

    choice = None

    while choice != 'q':
        choice = getInput(r"^(1|2|q)$", prompt)

        if choice == '1':
            refreshTrackers(driver, urls, numTorrents, timeout)
        elif choice == '2':
            loginSucceeded = login(tempFile, driver, domain, user, timeout)
            if loginSucceeded:
                trackers = getTrackers(tempFile)
                editTrackers(driver, urls, numTorrents, trackers, timeout)
            else:
                print('\n\nCannot edit trackers without logging in.')

    driver.quit()


#if __name__ == '__main__': main()
