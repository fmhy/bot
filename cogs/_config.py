import logging
import os
import re
from typing import TYPE_CHECKING

from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

prefix = "-"
TOKEN = os.getenv("TOKEN", None)
GUILD_ID = os.getenv("GUILD_ID", None)
OWNERS = os.getenv("OWNERS").split(",")
RSS_CHANNELS = os.getenv("RSS_CHANNEL_IDS", None)
FEEDS = os.getenv("RSS_FEED_URLS", None)
DB = os.getenv("db_uri")

if not TOKEN:
    message = "Couldn't find the `TOKEN` environment variable."
    log.warning(message)
    raise ValueError(message)

if not GUILD_ID:
    message = "Couldn't find the `GUILD_ID` environment variable."
    log.warning(message)
    raise ValueError(message)

if not OWNERS:
    message = "Couldn't find the `OWNERS` environment variable."
    log.warning(message)
    raise ValueError(message)

# so pyright won't complain of None
if TYPE_CHECKING:
    OWNERS: list[str]
    FEEDS: str
    RSS_CHANNELS: str
    TOKEN: str

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

# Automatic thread creation
auto_thread_channels = [
    976770662205104150 # free-stuff channel
]
auto_thread_roles = [
    956006107564879873 # free-stuff notif role
]
managing_roles = [956006107564879880, 956006107577454603]

rss_chan_ids = [int(i) for i in RSS_CHANNELS.split(",")]
rss_feed_urls = FEEDS.split(",")
