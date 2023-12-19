import os
import re
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TOKEN")
prefix = "-"
guild_id = int(os.getenv("GUILD_ID"))
owners = os.getenv("OWNERS").split(",")

url_regex = re.compile(
    r"(https?):\/\/(?:ww(?:w|\d+)\.)?((?:[\w_-]+(?:\.[\w_-]+)+)[\w.,@?^=%&:\/~+#-]*[\w@?^=%&~+-])"
)

channel_ids = [
    997291314389467146,  # add-links
    1085450217907814412,  # non-eng thread
    1000235624315498546,  # tested-links
    997292029056925808,  # nsfw-tested-links
    1099381748011380909,  # unknown??
]
managing_roles = [956006107564879880, 956006107577454603]

rss_chan_ids = [int(i) for i in os.getenv("RSS_CHANNEL_IDS").split(",")]
rss_feed_urls = os.getenv("RSS_FEED_URLS").split(",")
db_uri = os.getenv("db_uri")
