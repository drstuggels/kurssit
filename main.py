# -*- coding: utf-8 -*-

import logging
import os
import time

import requests
from bs4 import BeautifulSoup as bs
from consolemenu import *
from consolemenu.items import *
from progress.bar import ShadyBar
from progress.spinner import PieSpinner as Spinner
from stdiomask import getpass
from termcolor import colored


def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')


logging.basicConfig(filename="log.log",
                    filemode="a",
                    level=logging.DEBUG)


# Supply the names of the courses you want
courses = ["ENA04.1", "MAA05.1", "ÄI04.1", "RUB103.2", "FY04.1", "YH02.5", "KE03.2", "MAA06.2", "MU02.3", "KE07", "LI10.1", "FY05.1", "RUB104.2", "ENA05.2",
           "MAA07.1", "FY09", "BI02.4", "BI04.2", "MAA17.1", "MAA08.2", "KE04.1", "BI06.2", "ÄI05.5", "ÄI06.2", "ENA06.2", "FY06.2", "MAA12.2", "RUB105.4", "BI05.2", "LI02.4"]

# Default Wilma url
wilma_url = "https://yvkoulut.inschool.fi"


def magic():
    global courses, wilma_url

    courses = [{"name": course, "id": "", "selected": False}
               for course in courses]

    custom_url = input(
        f"Käytetään wilma-osoitetta \"{wilma_url}\".\nPaina enter jos tämä kelpaa. Jos ei kelpaa, kirjoita oma: ")
    if custom_url != "":
        wilma_url = custom_url

    clearScreen()

    clearScreen()
    print(colored("Sinun on kirjauduttava Wilmaan!", "yellow"))
    username = input("Käyttäjätunnuksesi: ").strip()
    password = getpass(prompt="Salasanasi: ")
    clearScreen()

    with requests.Session() as r:

        spinner = Spinner("Kirjaudutaan... ")

        g = r.get(wilma_url)
        spinner.next()
        soup = bs(g.text, "html.parser")
        spinner.next()
        token = soup.select_one("input[name=SESSIONID]").get("value")
        spinner.next()

        data = {
            "Login": username,
            "Password": password,
            "SESSIONID": token,
        }
        p = r.post(f"{wilma_url}/login", data=data)
        if "loginfailed" in p.url:
            print(colored("\nKirjautuminen epäonnistui", "red"))
            exit()
        spinner.next()
        spinner.finish()

        print(colored("Kirjautuminen onnistui!\n", "green"))

        try:
            spinner = Spinner("Hankitaan API-tokeni... ")

            g = r.get(wilma_url)
            spinner.next()
            soup = bs(g.text, "html.parser")
            spinner.next()
            token = soup.select_one("input[name=formkey]").get("value")
            spinner.next()
            spinner.finish()

            print(colored("Tokeni löytyi!\n", "green"))
        except:
            print(colored("Tokenin haku mokas.", "red"))
            exit()

        g = r.get(f"{wilma_url}/selection/view")
        soup = bs(g.text, "html.parser")
        parent = soup.select_one("#own-schools")
        years = []
        for index, child in enumerate(parent.find_all("h4")):
            years.append(
                {
                    "title": child.text.strip(),
                    "periods": [link["href"] for link in parent.find_all("ul")[index].find_all("a")]
                }
            )

        selection_menu = SelectionMenu([year["title"] for year in years], "Lukuvuosi",
                                       "Valitse oikea lukuvuosi, josta löytyy haluamasi kurssit.", show_exit_option=False)
        selection_menu.show()

        periods = years[selection_menu.selected_option]["periods"]

        bar = ShadyBar("Etsitään kurssit", max=(
            len(courses)*len(periods)), suffix="%(percent)d%%")

        for period in periods:
            g = r.get(f"{wilma_url}/selection/{period}")
            soup = bs(g.text, "html.parser")

            for course in courses:
                try:
                    id = soup.find("a", string=course["name"])["href"]
                    course["id"] = id
                except:
                    pass
                finally:
                    bar.next()

        failed = list(filter(lambda course: course["id"] == "", courses))

        bar.finish()

        if len(failed) != 0:
            print(colored("Nämä kurssit eivät löytyneet:", "red"))
            for fail in failed:
                print(fail["name"])
            print(colored("\nOhjelma suljetaan.", "red"))
            exit()
        else:
            print(
                colored(f"Kaikki {len(courses)} kurssia löydetty!\n", "green"))

        start = time.time()

        bar = ShadyBar("Valitaan kurssit", max=(len(courses)))

        for course in courses:
            id = course["id"]

            g = r.post(f"{wilma_url}/selection/postback", data={
                "message": "pick-group",
                "target": id,
                "formkey": token,
            })
            logging.info(f"id: {id}, response: {g.text}")
            bar.next()

        bar.finish()

        print(colored("Kaikki kurssit valittu {0:0.1f} sekunnissa.".format(
            time.time() - start), "green"))


if __name__ == "__main__":
    try:
        magic()
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        print(e)
