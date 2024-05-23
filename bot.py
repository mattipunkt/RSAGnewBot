import logging
import sys
from util import *
from bs4 import BeautifulSoup
import requests
import re
import multiprocessing
import threading
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

TOKEN = os.getenv("TOKEN")
dp = Dispatcher()
DB_FILE = r'database.db'
connection = create_connection(DB_FILE)


# RECEIVE AND PARSE INTERRUPTIONS FROM RSAG SITE
def parsestoerungen():
    nsite = requests.get('https://www.rsag-online.de/?id=1093')
    # nsite = codecs.open("test.html", 'r')
    site = re.sub(r'(\r\n|\n|\r)+', ' ', str(nsite.text))
    soup = BeautifulSoup(site, 'html.parser')
    stoerungen = soup.find_all('div', {"class": "container-fluid stoerungsmeldung"})
    return stoerungen


def getUsers():
    query = execute_read_query(connection, "SELECT telegramid FROM user")
    users = []
    for row in query:
        users.append(row[0])
    return users


# write interruptions to database, if they not exist
def writestoerungen_to_db():
    # send_new_stoerung("Test")
    print("[STOERER]    Starte Störungsschreiber")
    stoerungen = parsestoerungen()
    clear_stoerungen()
    for stoerung in stoerungen:
        headline = stoerung.find('h3').text
        alltext = stoerung.find_all('p')
        time_text = alltext[0].text.strip()
        description = alltext[1].text.strip()
        exists = execute_read_query(connection,
                                    "SELECT headline FROM stoerung WHERE headline LIKE '%" + str(headline) + "%'")
        if exists:
            print("[STOERER]    Keine neuen Störungen gefunden")
            threading.Timer(1800.0, writestoerungen_to_db).start()
            return
        else:
            print("[STOERER]    Neue Störung gefunden: " + str(headline))
            send_new_stoerung(str(headline))
            execute_query(connection, "INSERT INTO stoerung (headline, content, time) VALUES (?, ?, ?)",
                          (headline, description, time_text))
            threading.Timer(1800.0, writestoerungen_to_db).start()


def clear_stoerungen():
    stoerungen = parsestoerungen()
    liste_neu = []
    for stoerung in stoerungen:
        headline = stoerung.find('h3').text
        # print(headline)
        liste_neu.append(headline)
    liste_alt = []
    query = execute_read_query(connection, "SELECT id from stoerung")
    for stoerung in query:
        headline = execute_read_query(connection, "SELECT headline FROM stoerung WHERE id=" + str(stoerung[0]) + "")
        headline = headline[0]
        headline = str(headline[0])
        # print(headline)
        liste_alt.append(headline)
    for stoerung in liste_alt:
        if stoerung not in liste_neu:
            print('[STOERER]    Störung ' + str(stoerung) + ' ist nicht mehr vorhanden!')
            execute_query(connection, "DELETE FROM stoerung WHERE headline LIKE '%" + stoerung + "%'")


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    adduser(str(message.from_user.id), message.from_user.username)
    await message.answer(f"Hallo Matrose, *" + message.from_user.full_name + "*!\nDu wurdest erfolgreich"
                                                                             "in die Datenbank eingetragen und "
                                                                             "bekommst ab jetzt Benachrichtungen,"
                                                                             "falls es neue Störungen bei der RSAG "
                                                                             "gibt.\n\n"
                                                                             "*Weitere Commands:*\n/stoerungen - "
                                                                             "Zeigt alle"
                                                                             "aktuellen Störungen an. \n"
                                                                             "/stop - Du bekommst keine weiteren "
                                                                             "Nachrichten. ")


@dp.message(Command("stoerungen"))
async def send_stoerungen(message: Message):
    await message.answer(
        "Ahoi, Matrose!\n"
        "Hier sind die aktuellen Meldungen:\n\n"
    )
    query = execute_read_query(connection, "SELECT id from stoerung")
    for stoerung in query:
        headline = execute_read_query(connection, "SELECT headline FROM stoerung WHERE id=" + str(stoerung[0]) + "")
        headline = headline[0]
        await message.answer(
            str(headline[0])
        )


def send_new_stoerung(headline):
    query = execute_read_query(connection, "SELECT telegramid from user")
    ids = []
    for i in query:
        ids.append(str(i[0]))
    for i in ids:
        # await bot.send_message(chat_id=i, text="*Es gibt eine neue Meldung!*" + headline)
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={i}&text={"**Es gibt eine neue Meldung!**\n" + 
                                                                                  headline}"
        print(requests.get(url).json())  # this sends the message


def adduser(userid, username):
    exists = execute_read_query(connection, "SELECT telegramid FROM user WHERE telegramid LIKE '%" + userid + "%'")
    if exists:
        return
    else:
        execute_query(connection, "INSERT OR IGNORE INTO user (telegramid, username) VALUES (?, ?)", (userid, username))


async def main() -> None:
    setup_db(connection, DB_FILE)
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    process = multiprocessing.Process(target=writestoerungen_to_db())
    process.start()
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
