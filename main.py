from bs4 import BeautifulSoup
import requests
import csv, time, threading, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.robotparser import RobotFileParser
import os
from datetime import datetime
import configparser

seed_url = "https://www.ccsu.edu"

# Define the custom User-Agent
user_agent = "CCSUprogramscrawler"

headers = {
    "User-Agent": user_agent,
    "Cache-Control": "no-cache"
}

last_request_time = 0
lock = threading.Lock()
num_threads = 1
min_interval = 0.1

# ------------------------------------------------------------
# main()
# Entry point for crawling the program URL.
# Fetches main page, extracts programs, writes CSV.
# @author Kavitha Sridhar
# ------------------------------------------------------------
def main(programURL, session):

    global seed_url, user_agent, num_threads, min_interval
    seed_url, user_agent, num_threads, min_interval = loadConfig()
    try:
        response = politeGet(session, programURL, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        logging.error(f"HTTP error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        logging.error(f"Connection error: {errc}")
    except requests.exceptions.Timeout as errt:
        logging.error(f"Timeout error: {errt}")
    except requests.exceptions.RequestException as err:
        logging.error(f"Something went wrong: {err}")

    soup = BeautifulSoup(response.content, "html.parser")
    programs = []

    logging.info("Extraction is in progress....\n")
    extractPrograms(soup, programs, session)
    logging.info(f"Total programs crawled: {len(programs)}")

    writeToCSV(programs)
    logging.info("Extraction is completed\n")


    # Load data into local dict and display
    program_dict = parseCSV()
    for i in program_dict:
        print(i)

# ------------------------------------------------------------
# loadConfig()
# Loads crawler configuration values from config.ini file.
# author Kavitha Sridhar
# ------------------------------------------------------------
def loadConfig():
    config = configparser.ConfigParser()
    config.read("config.ini")

    seed_url = config["CRAWLER"].get("seed_url")
    user_agent = config["CRAWLER"].get("user_agent", "DefaultCrawlerAgent")
    num_threads = config["CRAWLER"].getint("num_threads", 10)
    min_request_interval = config["CRAWLER"].getfloat("min_request_interval", 0.5)

    return seed_url, user_agent, num_threads, min_request_interval

# ------------------------------------------------------------
# writeToCSV()
# Writes extracted program data to programs.csv.
# @author Kavitha Sridhar
# ------------------------------------------------------------
def writeToCSV(programs):
    csv_filename = "programs.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Category", "Program Name", "URL", "Description"])
        writer.writeheader()
        writer.writerows(programs)

# ------------------------------------------------------------
# parseCSV()
# Reads stored CSV data and loads it into a searchable data structure
# @author Sean Dunn
# ------------------------------------------------------------
def parseCSV():
    with open("programs.csv", "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader
# ------------------------------------------------------------
# extractPrograms()
# Extracts program categories and programs using BeautifulSoup.
# Uses multithreading to fetch descriptions concurrently.
# author Kavitha Sridhar
# ------------------------------------------------------------
def extractPrograms(soup, programs, session):
    categories = soup.find_all("h3")
    
    tasks = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for category in categories:
            for program in category.find_next_siblings():
                if program.name == "h3":
                    break

                for pgm in program.select(".views-row a"):
                    suburl = pgm["href"]
                    category_text = category.text.strip()
                    program_name = pgm.text.strip()

                    future = executor.submit(getDescription, suburl, session)
                    tasks.append((future, category_text, program_name, suburl))
        
        for future, category_text, program_name, suburl in tasks:
            try:
                description_text = future.result()
            except Exception as e:
                logging.error(f"Error fetching description for {suburl}: {e}")
                description_text = ""
            
            programs.append({
                "Category": category_text,
                "Program Name": program_name,
                "URL": suburl,
                "Description": description_text
            })


# ------------------------------------------------------------
# getDescription()
# Fetches program page and extracts "Program Features" section.
# Returns extracted text or empty string if not found.
# author Kavitha Sridhar
# ------------------------------------------------------------
def getDescription(suburl, session):
    desc_response = politeGet(session, seed_url + suburl, headers=headers)
    desc_soup = BeautifulSoup(desc_response.content, "html.parser")

    h2 = desc_soup.find("h2", string="Program Features")
    if not h2:
        return ""

    ul = h2.find_next("ul")
    if not ul:
        return ""

    features = [li.get_text(strip=True) for li in ul.find_all("li")]
    description_text = " ".join(features)

    return description_text


# ------------------------------------------------------------
# validateURLInRobotFile()
# Verifies robots.txt permissions for this crawler.
# Logs whether crawling is allowed.
# author Kavitha Sridhar
# ------------------------------------------------------------
def validateURLInRobotFile(seed_url, headers, program_URL):
    rp = RobotFileParser()
    rp.set_url(seed_url + "/robots.txt")
    rp.read()

    if rp.can_fetch("CCSUProgramsCrawler", program_URL):
        logging.info(f"CCSUProgramsCrawler is allowed to crawl: {program_URL}")
    else:
        logging.info(f"CCSUProgramsCrawler is NOT allowed to crawl: {program_URL}")


# ------------------------------------------------------------
# politeGet()
# Makes a GET request with enforced delay between requests.
# Ensures thread-safe rate limiting.
# author Kavitha Sridhar
# ------------------------------------------------------------
def politeGet(session, url, headers, min_interval=min_interval):
    global last_request_time

    with lock:
        elapsed = time.time() - last_request_time
        delay = max(0, min_interval - elapsed)
        last_request_time = time.time() + delay

    if delay > 0:
        time.sleep(delay)

    response = session.get(url, headers=headers, timeout=10)
    logging.info("Get :" + url)

    return response


# ------------------------------------------------------------
# initializeLog()
# Initializes logging with timestamped log files.
# Creates logs directory if missing.
# author Kavitha Sridhar
# ------------------------------------------------------------
def initializeLog():
    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        filename=f"logs/crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(threadName)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

# ------------------------------------------------------------
# print_elements()
# Prints all elements in dict
# Used in testing
# author Sean Dunn
# ------------------------------------------------------------
def print_elements(program_dict):
    print(program_dict.keys())


# ------------------------------------------------------------
# Program Entry Point
# ------------------------------------------------------------
if __name__ == "__main__":
    program_URL = seed_url + "/programs"
    initializeLog()
    validateURLInRobotFile(seed_url, headers, program_URL)

    reuseSession = requests.Session()
    reuseSession.headers.update(headers)

    main(program_URL, reuseSession)
