import requests
import robotsparser
import threading
import schedule
from bs4 import BeautifulSoup


def main():
    name = "CCSU_Project_Bot"
    baseURL = "https://www.ccsu.edu/programs"
    robotsURL = "https://www.ccsu.edu/robots.txt"

    #init a request to visit the ccsu site
    #parse robots.txt
    #scrape program names, proceed to attached url, copy program details, save in map, increment size and reference program name
    #possibly menu to allow user to search up specific major

if __name__ == '__main__':
    main()