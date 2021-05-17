# -*- coding: utf-8 -*-

import logging
import os

import requests
from bs4 import BeautifulSoup as bs
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(filename="log.log",
                    filemode='a',
                    level=logging.DEBUG)

wilma_url = "https://yvkoulut.inschool.fi"

# The periods to check
periods = ["7065D7AB_70924", "7065D7AB_70925", "7065D7AB_70926",
           "7065D7AB_70927", "7065D7AB_70928", "7065D7AB_72689"]

# Supply the names of the courses you want
courses = []


with requests.Session() as r:

    print("Hankitaan tokeni.")

    g = r.get(wilma_url)
    soup = bs(g.text, 'html.parser')
    token = soup.select_one('input[name=SESSIONID]').get('value')

    print(f"Tokeni löytyi: {token}")

    username = os.getenv("username")
    password = os.getenv("password")
    print(f"Kirjaudutaan käyttäjään {username}")

    data = {
        "Login": username,
        "Password": password,
        "SESSIONID": token,
    }
    r.post(f'{wilma_url}/login', data=data)

    print("Onnistui!")

    print("Hankitaan formkey.")

    g = r.get(wilma_url)
    soup = bs(g.text, 'html.parser')
    token = soup.select_one('input[name=formkey]').get('value')

    print(f"Formkey löytyi: {token}")

    course_ids = []

    for period in periods:
        g = r.get(f"{wilma_url}/selection/{period}")
        soup = bs(g.text, 'html.parser')

        for course in courses:
            print(f"Yritetään löytää kurssi {course} jaksosta {period}")
            try:
                id = soup.find("a", string=course)["href"]
                course_ids.append(id)
                print("Löytyi!")
            except:
                print("Ei löytynyt, siirrytään eteenpäin!")
                pass

    for id in course_ids:
        print(f"Valitaan kurssi id:llä {id}")
        g = r.post(f"{wilma_url}/selection/postback", data={
            "message": "pick-group",
            "target": id,
            "formkey": token,
        })
        logging.info(f"id: {id}, response: {g.text}")
        print(f"Statuskoodi: {g.status_code}. Siirrytään seuraavaan.")

    print(f"Kaikki valmiit. {len(course_ids)} kurssia valittu.")
