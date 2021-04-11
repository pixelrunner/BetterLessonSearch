from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import telegram_send

#TODO: start every x minutes

# To add a new leisure centre to the search you need to do the following:
# 1) add the search strings under static config
# 2) create a dictionary with the id, name, and url in static config area
# 3) add the dictionary to the LeisureCentreList in return of static config

def UserConfig():
    # What do you want to search on? Weekends only or everyday?
    # (Every day is mainly used for testing as there are usually at least one space available during the week)
    # SystemCheck will show every session regardless of day or amount of spaces
    WeekendOnly = True
    SystemCheck = True
    return WeekendOnly, SystemCheck

def StaticConfig():
    # Grab the user config variables from the top function
    WeekendOnly, SystemCheck = UserConfig()

    # set urls
    if WeekendOnly and SystemCheck == False:
        # Weekend only search
        wfurl = 'https://www.betterlessons.org.uk/onlinejoining/classes-results?filter=%7B%22region%22:11,%22courseGroupCategory%22:%5B1%5D,%22courseType%22:1,%22levelGroup1%22:%5B262%5D,%22level262%22:%5B845%5D,%22centre%22:15,%22dayOfWeek%22:%5B0,6%5D,%22showFullCourses%22:true%7D'
        laqurl = 'https://www.betterlessons.org.uk/onlinejoining/classes-results?filter=%7B%22centre%22:119,%22courseGroupCategory%22:%5B1%5D,%22showFullCourses%22:true,%22courseType%22:1,%22levelGroup1%22:%5B262%5D,%22level262%22:%5B845%5D,%22dayOfWeek%22:%5B0,6%5D%7D'
        lsurl = 'https://www.betterlessons.org.uk/onlinejoining/classes-results?filter=%7B%22centre%22:13,%22courseGroupCategory%22:%5B1%5D,%22showFullCourses%22:true,%22courseType%22:1,%22levelGroup1%22:%5B262%5D,%22dayOfWeek%22:%5B6,0%5D%7D'
    else:
        # Every-day search
        wfurl = 'https://www.betterlessons.org.uk/onlinejoining/classes-results?filter=%7B%22region%22:11,%22courseGroupCategory%22:%5B1%5D,%22courseType%22:1,%22levelGroup1%22:%5B262%5D,%22level262%22:%5B845%5D,%22centre%22:15,%22dayOfWeek%22:%5B%5D,%22showFullCourses%22:true%7D'
        laqurl = 'https://www.betterlessons.org.uk/onlinejoining/classes-results?filter=%7B%22centre%22:119,%22courseGroupCategory%22:%5B1%5D,%22showFullCourses%22:true,%22courseType%22:1,%22levelGroup1%22:%5B262%5D,%22level262%22:%5B845%5D%7D'
        lsurl = 'https://www.betterlessons.org.uk/onlinejoining/classes-results?filter=%7B%22centre%22:13,%22courseGroupCategory%22:%5B1%5D,%22showFullCourses%22:true,%22courseType%22:1,%22levelGroup1%22:%5B262%5D%7D'

    wf = {"id": "wf", "name": "Waltham Forest Feel Good Centre", "url": wfurl}
    ls = {"id": "ls", "name": "Leytonstone", "url": lsurl}
    laq = {"id": "laq", "name": "London Aquatic Centre", "url": laqurl}

    return [wf, ls, laq], SystemCheck

def SetBaseMessage(SystemCheck):
    if SystemCheck:
        message = '****** All Swimming Lessons ******\n'
    else:
        message = '**** Open Swimming Lessons! ****\n'

    message += '************************************\n'
    return message

def SearchLeisureCentres(LessonsWithSpaces, LeisureCentreList):
    for LeisureCentre in LeisureCentreList:
        # For each leisure centre in the list create a headless instance of firefox with the search url,
        # wait 10 seconds for the javascript to run, then check if there are any classes with free spaces.
        # If there are spaces then save the session details

        print('Checking ' + LeisureCentre['name'])

        options = Options()
        options.headless = True

        driver = webdriver.Firefox(options=options)
        driver.get(LeisureCentre["url"])

        time.sleep(10)
        html = driver.execute_script("return document.documentElement.outerHTML")
        sel_soup = BeautifulSoup(html, "lxml")

        sessions = sel_soup.findAll('div', {"class": "row m-0"})

        for session in sessions:
            spacesleft = int(session.contents[3].contents[3].contents[3].contents[0].string.strip())
            daytime = str((session.contents[1].contents[3].contents[3].contents[1].contents[0]).strip())

            if spacesleft > 0 or SystemCheck:
                # if there are spaces on a course found then add a dictionary of the session to the 'LessonsWithSpaces' list

                LessonsWithSpaces.append({"CentreID": LeisureCentre["id"],
                                    "CentreName": LeisureCentre["name"],
                                    "daytime": daytime,
                                    "spacesleft": spacesleft})

        # close the instance of firefox
        driver.quit()

    return LessonsWithSpaces

if __name__ == "__main__":
    try:
        # build list of leisure centres to from user/static variables above and grab SystemCheck variable
        LeisureCentreList, SystemCheck = StaticConfig()

        # create blank list to append the lessons found that have spaces
        LessonsWithSpaces = []
        LessonsWithSpaces = SearchLeisureCentres(LessonsWithSpaces, LeisureCentreList)

        if len(LessonsWithSpaces) > 0:
            # build text message to send via telegram
            message = SetBaseMessage(SystemCheck)

            for OpenLesson in LessonsWithSpaces:
                message += '\n' + OpenLesson['CentreName'] + ':'
                message += '\n' + OpenLesson['daytime'] + '\nSpaces available: ' + str(OpenLesson['spacesleft']) + '\n'

            # send telegram message
            telegram_send.send(messages=[message])

        # print('Script completed successfully')

    except:
        telegram_send.send(messages='An error occurred when running the search script')
        # print('An error occurred')
