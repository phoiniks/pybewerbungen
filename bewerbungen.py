#!/usr/bin/python3

import sys
from os.path import splitext, basename
import logging
import sqlite3
from redis import Redis
import csv
import re
from time import strftime
import locale
from collections import UserDict
from pprint import pprint
from jinja2 import Template, Environment, FileSystemLoader


programm = sys.argv[0]

base = splitext(basename(programm))[0].upper()
logbuch = base + ".LOG"
db = base + ".DB"
csvDatei = base + ".CSV"

logging.basicConfig(filename = logbuch, level = logging.DEBUG, format = '%(name)s %(asctime)s %(message)s %(funcName)s %(lineno)d')
log = logging.getLogger("DEBUG")

locale.setlocale(locale.LC_ALL, '')

lokalzeit = strftime('%A_%d_%B_%Y_%H:%M:%S')


class Angebot(dict):
    def __init__(self, bezeichnung, firma, strasse, ort, anrede, ansprechpartner,
                 mail, telefon, website, quelle, ergebnis="steht noch aus"):
        self.bezeichnung = bezeichnung
        self.firma = firma
        self.strasse = strasse
        self.ort = ort
        self.anrede = anrede
        self.ansprechpartner = ansprechpartner
        self.mail = mail
        self.telefon = telefon
        self.website = website
        self.quelle = quelle
        self.ergebnis = ergebnis
        self.tex = self.firma + "_" + lokalzeit + ".tex"
        self.tex = re.sub(" ", "_", self.tex)

        
    def mkSQLite(self):
        con = sqlite3.connect(db)
        cur = con.cursor()
        
        create = """CREATE TABLE IF NOT EXISTS angebote(id INTEGER PRIMARY KEY, bezeichnung TEXT, firma TEXT, strasse TEXT, ort TEXT,
        anrede TEXT, ansprechpartner TEXT, mail TEXT, telefon TEXT, website TEXT, quelle TEXT, ergebnis TEXT, lokalzeit DATE DEFAULT(DATETIME('now', 'localtime')))"""

        cur.execute(create)

        insert = """INSERT INTO angebote (bezeichnung, firma, strasse, ort, anrede, ansprechpartner, mail, telefon, website, quelle, ergebnis)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

        cur.execute(insert, (self.bezeichnung,
                             self.firma,
                             self.strasse,
                             self.ort,
                             self.anrede,
                             self.ansprechpartner,
                             self.mail,
                             self.telefon,
                             self.website,
                             self.quelle,
                             self.ergebnis))

        con.commit()


    def mkCSV(self):
        con = sqlite3.connect(db)
        cur = con.cursor()

        select = "SELECT * FROM angebote"

        cur.execute(select)
        werte = cur.fetchall()

        with open(csvDatei, mode = "w") as csvHandle:
            csvWriter = csv.writer(csvHandle, delimiter = ';', quotechar = "'", quoting = csv.QUOTE_MINIMAL)
            csvWriter.writerows(werte)
        

    def mkRedis(self):
        dictionary = {
            'bezeichnung':self.bezeichnung,
            'firma':self.firma,
            'strasse':self.strasse,
            'ort':self.ort,
            'anrede':self.anrede,
            'ansprechpartner':self.ansprechpartner,
            'mail':self.mail,
            'telefon':self.telefon,
            'website':self.website,
            'quelle':self.quelle,
            'ergebnis':self.ergebnis}

        with open("template.tex") as text:
            templatestring = text.read()
            template = Template(templatestring)

        templatetext = template.render(dictionary)

        templatetext = re.sub(" & Co.", " \& Co.", templatetext)

        with open(self.tex, "w") as ausgabe:
            ausgabe.write(templatetext)

        rds = Redis()

        for key in dictionary.keys():
            rds.hset(self.tex, key, dictionary[key])

        rds.hset(self.tex, 'anschreiben', templatetext)


log.debug("BEGINN")


if __name__ == "__main__":
    bezeichnung = input("BEZEICHNUNG: ")
    firma = input("FIRMA: ")
    strasse = input("STRASSE: ")
    ort = input("ORT: ")
    anrede = input("ANREDE: ")
    ansprechpartner = input("ANSPRECHPARTNER: ")
    mail = input("MAIL: ")
    telefon = input("TELEFON: ")
    website = input("WEBSITE: ")
    quelle = input("QUELLE: ")
    ergebnis = input("ERGEBNIS: ")


    angebot = Angebot(bezeichnung, firma, strasse, ort, anrede, ansprechpartner, mail, telefon, website, quelle)

    angebot.mkSQLite()
    angebot.mkCSV()
    angebot.mkRedis()
    
    log.debug(angebot.bezeichnung)
    log.debug(angebot.firma)
    log.debug(angebot.strasse)
    log.debug(angebot.ort)
    log.debug(angebot.anrede)
    log.debug(angebot.ansprechpartner)
    log.debug(angebot.mail)
    log.debug(angebot.telefon)
    log.debug(angebot.website)
    log.debug(angebot.quelle)
    log.debug(angebot.ergebnis)
    log.debug(angebot.tex)

log.debug("ENDE")
