import logging
import os
import re

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)


def _get(variable: str) -> str:
    val = os.environ.get(variable)
    if not val:
        message = f"{variable!r} not set in .env file. Set it."
        log.error(message)
        raise ValueError(message)
    return val


def _get_int_list(variable: str):
    val = _get(variable)
    return [int(x) for x in val.split(",")]


prefix = "-"
TOKEN = _get("TOKEN")
GUILD_ID = _get("GUILD_ID")
OWNERS = _get_int_list("OWNERS")
RSS_CHANNELS = _get("RSS_CHANNEL_IDS")
FEEDS = _get("RSS_FEED_URLS")
MKSWT_KEY = _get("MKSWT_KEY")
DB = os.environ.get("DB_URI")

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

disallowed_channel_ids = [
    988133247575810059,  # dead-sites
    986617857133649921,  # removed-sites
]

# Automatic thread creation
auto_thread_mappings = {
    "976770662205104150": "956006107564879873",  # free-stuff channel
    "1089999083856470016": None,  # secret-guides channel
}

managing_roles = [956006107564879880, 956006107577454603]

news_forum = 1289918731811553283
news_tag = 1289925916360704111
rss_feed_urls = FEEDS.split(",")
