from datetime import datetime

import certifi
import discord
import feedparser
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from bot.core.config import DB, rss_feed_urls

ca = certifi.where()
client = MongoClient(DB, server_api=ServerApi("1"))
import base64

mydb = client["fmby"]
mycol = mydb["sent_articles"]


def cembed(title, description, **kwargs):
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green(),
        timestamp=datetime.now(),
        **kwargs,
    )


EMOJI = "\U0001f4f0"


def fetch_feed():
    # Load the seen IDs from the file, or create an empty dictionary
    sent_articles = list(mycol.find().sort("_id", -1))

    for rss_feed_url in rss_feed_urls:
        # Parse the RSS feed
        feed = feedparser.parse(rss_feed_url)

        # Check if the feed was parsed successfully
        if feed.bozo:
            print(f"Error parsing RSS feed: {feed.bozo_exception}")
            print(f"{rss_feed_url}")
            continue

        last_entry = feed.entries[0]

        x = list(mycol.find({"link": last_entry.link}))

        if len(x) == 0:
            article_title = last_entry.title
            article_link = last_entry.link
            mycol.insert_one({"link": last_entry.link})

            # print(f"New article: {article_title}")
            # print(f"Link: {article_link}")

            yield f"{EMOJI}  |  {article_title}\n\n{article_link}"

        # print(f"Parsing complete for {rss_feed_url}")


def split_discord_message(response, char_limit=1900):
    m_ls = []
    if len(response) > char_limit:
        # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
        if "```" in response:
            # Split the response if the code block exists
            parts = response.split("```")

            for i in range(len(parts)):
                if i % 2 == 0:  # indices that are even are not code blocks
                    m_ls.append(parts[i])

                else:  # Odd-numbered parts are code blocks
                    code_block = parts[i].split("\n")
                    formatted_code_block = ""
                    for line in code_block:
                        while len(line) > char_limit:
                            # Split the line at the 50th character
                            formatted_code_block += line[:char_limit] + "\n"
                            line = line[char_limit:]
                        formatted_code_block += (
                            line + "\n"
                        )  # Add the line and seperate with new line

                    # Send the code block in a separate message
                    if len(formatted_code_block) > char_limit + 100:
                        code_block_chunks = [
                            formatted_code_block[i : i + char_limit]
                            for i in range(0, len(formatted_code_block), char_limit)
                        ]
                        for chunk in code_block_chunks:
                            m_ls.append(f"```{chunk}```")

                    else:
                        m_ls.append(f"```{formatted_code_block}```")

        else:
            response_chunks = [
                response[i : i + char_limit] for i in range(0, len(response), char_limit)
            ]
            for chunk in response_chunks:
                m_ls.append(chunk)
    else:
        m_ls.append(response)

    return m_ls


def words_from_content(content: str):
    for word in content.replace("\n", " ").split(" "):
        if word.startswith("`") and word.endswith("`"):
            to = (word[1:-1]).strip()
            if to != "":
                yield to
        elif "`" in word:
            to = (word).strip()
            if to != "":
                yield to
        else:
            to = (word.replace("`", " ")).strip()
            if to != "":
                yield to


def b64decode(s, from_msg=False):
    s = s.replace("=", "")
    try:
        x = base64.urlsafe_b64decode((s + "==").encode()).decode()
        if (base64.urlsafe_b64encode(x.encode()).decode().replace("=", "") == s) or (
            base64.b64encode(x.encode()).decode().replace("=", "") == s
        ):
            if from_msg:
                return x if len(x) > 10 else None
            return x
        else:
            return None
    except Exception:
        return None


emoji_map = {
    0: "0️⃣",
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
    10: "🔟",
}

string_num = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "keycap_ten": "10",
}


emoji_num = {
    "0️⃣": 0,
    "1️⃣": 1,
    "2️⃣": 2,
    "3️⃣": 3,
    "4️⃣": 4,
    "5️⃣": 5,
    "6️⃣": 6,
    "7️⃣": 7,
    "8️⃣": 8,
    "9️⃣": 9,
    "🔟": 10,
}


def b64encode(content):
    return base64.urlsafe_b64encode(content.encode()).decode()
