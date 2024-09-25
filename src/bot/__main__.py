import asyncio
import logging
import os

import sentry_sdk
from dotenv import load_dotenv

from bot.core import formatter

load_dotenv()
formatter.install(__name__, "INFO")
logger = logging.getLogger(__name__)

sentry_url = os.environ.get("SENTRY_URL")
_env = os.environ.get("ENV")

if sentry_url and _env == "production":
    logger.info("Initializing Sentry in production")

    sentry_sdk.init(
        dsn=sentry_url,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

from bot import main

asyncio.run(main())
