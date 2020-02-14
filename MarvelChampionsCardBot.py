import RedditBotClass
import config
import os
import json
import requests
from tinydb import TinyDB, Query

if not os.path.exists('db.json'):
    open("db.json", "w+")

database = TinyDB("db.json")
cardQuery = Query()
cardTable = database.table('cards')

response = requests.get("https://marvelcdb.com/api/public/cards/?_format=json")
cards = json.loads(response.text)
for card in cards:
    if card["pack_code"] in config.packs:
        cardCode = card["code"]
        if not cardCode.endswith("b"):
            entry = cardTable.search(cardQuery.code == cardCode)
            if not entry:
                cardTable.insert({'code':cardCode,'visited':False})
                print(cardCode + " doesn't exists yet, so creating")

bot = RedditBotClass.RedditBot(config, database)
bot.run_bot()
