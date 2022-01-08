import logging.config
import os
import pathlib

cwd = pathlib.Path(__file__).parent.parent.resolve()
logging.config.fileConfig(
    os.path.join(cwd, "logging.conf"), disable_existing_loggers=True
)
logger = logging.getLogger("kpm")
logger.info("loglevel=" + logging.getLevelName(logger.getEffectiveLevel()))
