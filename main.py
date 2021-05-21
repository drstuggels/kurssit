# -*- coding: utf-8 -*-

import datetime
import os
import re
import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor, as_completed

import pause
import requests
from bs4 import BeautifulSoup as bs
from consolemenu import SelectionMenu
from progress.bar import ShadyBar
from progress.spinner import PieSpinner as Spinner
from stdiomask import getpass
from termcolor import colored


def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')


# Default Wilma url
wilma_url = "https://yvkoulut.inschool.fi"


def magic():
    global wilma_url

    clearScreen()
    custom_url = input(
        f"Käytetään wilma-osoitetta \"{wilma_url}\".\nPaina Enter jos tämä kelpaa. Jos ei kelpaa, kirjoita oma: ")
    if custom_url.strip() != "":
        wilma_url = custom_url

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

        master = tk.Tk()
        master.resizable(False, False)
        master.title('Haluamasi kurssit')
        master.eval('tk::PlaceWindow . center')

        def getInput():
            globals()["courses_input"] = textarea.get("1.0", "end-1c")
            master.after(1, master.destroy())

        title = tk.Label(
            master, text="Liitä tähän kaikki haluamasi kurssit.\nVoit erottaa ne miten tahansa (pilkut, rivivälit, jne.)")
        title.grid(row=0, column=0)

        textarea = tk.Text(master,
                           height=30, width=38)
        textarea.grid(row=1,
                      column=0)

        btn = tk.Button(master, text="Done.", justify="center",
                        command=getInput)
        btn.grid(row=2, column=0)
        master.mainloop()

        course_regex = r"([A-z0-9öÖäÄåÅ]+[\.0-9]+)"
        courses = [course.group(0) for course in re.finditer(course_regex, globals()[
            "courses_input"], re.MULTILINE)]
        courses = [{"name": course, "id": "", "selected": False}
                   for course in courses]

        print(colored(f"{len(courses)} kurssin nimeä tunnistettu", "green"))

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
        success = list(filter(lambda course: course["id"] != "", courses))

        bar.finish()

        if len(failed) != 0:
            print(colored("Nämä kurssit eivät löytyneet:", "red"))
            for fail in failed:
                print(fail["name"])

            cont = input(
                "\nJatketaanko silti?\nPaina Enter jatkakseen ja jotain muuta lopetakseen: ")
            if cont != "":
                print(colored("\nOhjelma suljetaan.", "red"))
                exit()

        else:
            print(
                colored(f"Kaikki {len(success)} kurssia löydetty!\n", "green"))

        thetime = input(
            "\nMihin aikaan kurssivalinnat alkavat?\nJos haluat, että kurssit valitaan heti, paina Enter.\nMuuten, kirjoita muodossa \"16.00\": ")
        if thetime.strip() != "":
            (hours, minutes) = [int(t)
                                for t in thetime.strip().replace(".", ":").split(":")]
            fire = datetime.datetime.now().replace(hour=hours, minute=minutes, second=1)
            print(colored(f"Nyt odotetaan {thetime} asti...\n", "green"))
            pause.until(fire)
        else:
            print(colored("Aloitetaan heti!\n", "green"))
            time.sleep(0.5)

        clearScreen()

        start = time.time()

        bar = ShadyBar("Valitaan kurssit", max=(len(success)))

        with ThreadPoolExecutor(max_workers=30) as ex:
            futures = [ex.submit(select, r, {
                "message": "pick-group",
                "target": course["id"],
                "formkey": token,
            }) for course in success]

            for fut in as_completed(futures):
                fut.result()
                bar.next()

        bar.finish()

        print(colored("Kaikki kurssit valittu {0:0.1f} sekunnissa.".format(
            time.time() - start), "green"))


def select(session: requests.Session, data: dict):
    return session.post(f"{wilma_url}/selection/postback", data)


if __name__ == "__main__":
    try:
        magic()
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        print(e)
