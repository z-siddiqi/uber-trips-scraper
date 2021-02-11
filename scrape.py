import sys
import os
import pandas as pd

from lxml import html
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def main():
    load_dotenv()
    url = "https://drivers.uber.com/p3/payments/performance-hub"  # base url
    driver = configure_driver()
    driver.get(url)

    try:
        # email
        email = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//input[@id="useridInput"]'))
        )
        email.send_keys(os.getenv("EMAIL"))
        next_button = driver.find_element_by_class_name("push-small--right")
        next_button.click()

        # password
        password = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//input[@id="password"]'))
        )
        password.send_keys(os.getenv("PASSWORD"))
        next_button = driver.find_element_by_class_name("push-small--right")
        next_button.click()
    except TimeoutException as e:
        sys.exit("Timed out logging in!")

    # grab trip ids
    df = pd.read_csv("statement.csv", parse_dates=[3], index_col=3)
    df = df.sort_index()
    trip_ids = df["Trip ID"].values  # list of trip ids

    from_address = []
    to_address = []
    distance = []

    # loop through trips
    for id in trip_ids:
        url = f"https://drivers.uber.com/p3/payments/v2/trips/{id}"
        driver.get(url)

        html_tree = html.fromstring(driver.page_source)
        addresses = html_tree.xpath('//div[@class="b1 ay b2 b3 ao b4 b5 b6 b7"]/div[2]')
        distances = html_tree.xpath('//div[@class="cq cr"]')

        if not distances:
            distances = html_tree.xpath('//div[@class="bw bx"]')

        from_address.append(addresses[0].text_content())
        to_address.append(addresses[1].text_content())
        distance.append(distances[1].text_content())

    # add new columns
    df["From"] = from_address
    df["To"] = to_address
    df["Distance"] = distance

    # format df
    df = df.drop(["Phone number", "Driver name", "Email", "Type"], 1)
    df = df[
        [
            "Trip ID",
            "From",
            "To",
            "Distance",
            "Fare Distance",
            "Fare Drop Off Fee",
            "Fare Minimum Fare Supplement",
            "Fare Pick Up Fee",
            "Fare Surge",
            "Service Fee",
            "Promotion Boost",
            "Tip",
            "Total",
        ]
    ]

    # save df
    df.to_csv("output.csv")


def configure_driver():
    firefox_options = FirefoxOptions()
    driver = webdriver.Firefox(options=firefox_options)
    return driver


if __name__ == "__main__":
    main()
