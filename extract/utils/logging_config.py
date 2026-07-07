import logging


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logging.getLogger("snowflake.connector").setLevel(logging.ERROR)
    logging.getLogger("snowflake.connector.vendored.urllib3").setLevel(logging.ERROR)


logger = logging.getLogger("extract")
