import praw
import time
import re
import requests
import json
import os
import random
import datetime
from datetime import date
from tinydb import TinyDB, Query

class RedditBot(object):
    def __init__(self, config, database):
        self.database = database
        self.started = False
        self.db = TinyDB('db.json')
        self.login(config)

    def login(self, config):
        self.reddit = praw.Reddit(username = config.username,
                            password = config.password,
                            client_id = config.client_id,
                            client_secret = config.client_secret,
                            user_agent = config.user_agent)

    def run_bot(self):
        if (self.started is False):
            self.started = True
            while(self.started is True):
                if (self.__check_for_post_time()):
                    print("Should create new post")
                    cardToVisit = self.__get_latest_card_id()
                    if cardToVisit:
                        print("Visiting card: " + cardToVisit)
                        loadedCardData = self.__load_card_data(cardToVisit)

                        post = self.reddit.subreddit("marvelchampionslcg").submit(self.__format_post_title(loadedCardData), selftext=self.__format_post_description(loadedCardData))
                        for flair in post.flair.choices():
                            print("Flair:" + flair)

                        self.__visit_card_id(cardToVisit)
                    else:
                        print("No card found to visit!")
                
                print("Done with everything. Sleeping")
                time.sleep(3600)

    def __check_for_post_time(self):
        table = self.database.table('posts')
        if len(table) > 0:
            sortedTable = sorted(table, key=lambda k: k["postDate"])
            latestPost = sortedTable[-1]
            latestPostDate = datetime.datetime.strptime(latestPost["postDate"], "%a %b %d %H:%M:%S %Y")
            if (latestPostDate + datetime.timedelta(minutes = 1440) <= datetime.datetime.now()):
                return True
            return False
        else:
            print("No entries found in database")
            return True

    def __get_latest_card_id(self):
        table = self.database.table('cards')
        if len(table) > 0:
            cardQuery = Query()
            nonVisitedCards = table.search(cardQuery.visited == False)
            if (len(nonVisitedCards) > 0):
                random.shuffle(nonVisitedCards)
                return nonVisitedCards[0]["code"]
            else:
                print("No new cards to visit!")
        else:
            print("Cards table is empty")

    def __visit_card_id(self, id):
        cardTable = self.database.table('cards')
        cardQuery = Query()
        cardTable.update({'code': id, 'visited': True}, cardQuery.code == id)

        postsTable = self.database.table('posts')
        postsTable.insert({'postDate': datetime.datetime.now().ctime(), 'cardCode': id})

    def __load_card_data(self, id):
        response = requests.get("https://marvelcdb.com/api/public/card/" + id + ".json")
        if response.status_code == 200:
            data = json.loads(response.text)
            return data
        else:
            print("Response returned invalid status code")

    def __format_post_title(self, cardData):
        msg = "[COTD] "
        msg += cardData["name"]
        if (cardData.get("subname")):
            msg += " - " + cardData["subname"]
        if (cardData.get("linked_card")):
            msg += " - " + cardData["linked_card"]["name"]
        msg += " (" + date.today().strftime("%d/%m/%Y") + ")"
        return msg

    def __format_post_description(self, cardData):
        msg = "[" + cardData["name"] + "](" + cardData["url"] + ")\n\n"
        if (cardData.get("card_set_name")):
            msg += "* **" + cardData["card_set_name"] + "**\n\n"
        else: 
            if (cardData.get("faction_name")):
                msg += "* **" + cardData["faction_name"] + "**\n\n"
        msg += "* **Type:** " + cardData["type_name"] + "\n\n"
        if (cardData.get("traits")):
            msg += "* ***" + cardData["traits"] + "***\n\n"
        if (cardData.get("cost")):
            msg += "* **Cost:** " + str(cardData["cost"]) + "\n\n"
        if (cardData.get("thwart")):
            msg += "* **Thwart:** " + str(cardData["thwart"])
            if (cardData.get("thwart_cost")):
                msg += " [" + str(cardData["thwart_cost"]) + " Consequential Damage]"
            msg += "\n\n"
        if (cardData.get("attack")):
            msg += "* **Attack:** " + str(cardData["attack"])
            if (cardData.get("attack_cost")):
                msg += " [" + str(cardData["attack_cost"]) + " Consequential Damage]"
            msg += "\n\n"
        if (cardData.get("health")):
            msg += "* **Health:** " + str(cardData["health"]) + "\n\n"
        
        resources = []
        if (cardData.get("resource_mental")):
            resources.append(str(cardData["resource_mental"]) + "x Mental")
        if (cardData.get("resource_physical")):
            resources.append(str(cardData["resource_physical"]) + "x Physical")
        if (cardData.get("resource_energy")):
            resources.append(str(cardData["resource_energy"]) + "x Energy")
        if (cardData.get("resource_wild")):
            resources.append(str(cardData["resource_wild"]) + "x Wild")

        if len(resources) > 0:
            msg += "* **Resource:** [ " + ', '.join(resources) + " ]\n\n"

        if (cardData.get("text")):
            msg += cardData["text"].replace("<b>", "**").replace("</b>", "**").replace("<i>", "***").replace("</i>", "***") + "\n\n"

        if (cardData.get("linked_card")):
            msg += "\n\n"
            self.__format_post_description(cardData["linked_card"])
        else:
            msg += cardData["pack_name"] + " #" + str(cardData["position"])
        return msg