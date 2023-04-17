from logging import getLogger, StreamHandler, FileHandler, DEBUG, Formatter, Logger
import random
import string
from typing import Optional


def get_file_logger(path: str, identifier: str, name: Optional[str] = None):

    tmp = ("bcil_dcm_convert." if name is None else name + ".") + identifier
    while tmp in Logger.manager.loggerDict:
        tmp = get_random_id("bcil_dcm_convert.", 15)
    logger = getLogger(tmp)
    logger.setLevel(DEBUG)
    fh = FileHandler(filename=path, mode='a', encoding='utf-8')
    fh.setFormatter(Formatter("%(asctime)s : %(message)s"))
    logger.addHandler(fh)
    return logger


def get_stream_logger(identifier: str, name: Optional[str] = None):

    tmp = ("bcil_dcm_convert." if name is None else name + ".") + identifier
    while tmp in Logger.manager.loggerDict:
        tmp = get_random_id("bcil_dcm_convert_print.", 15)
    # console log
    logger = getLogger(tmp)
    logger.setLevel(DEBUG)
    sh = StreamHandler()
    sh.setLevel(DEBUG)
    sh.setFormatter(Formatter("%(message)s"))
    logger.addHandler(sh)
    return logger


def disposal_logger(logger):
    if logger is not None:
        while len(logger.handlers) > 0:
            logger.removeHandler(logger.handlers[0])
        name = logger.name
        del Logger.manager.loggerDict[name]
    return None


def get_random_id(keyword: str, n: int):
    return keyword + ''.join(random.choices(string.ascii_letters + string.digits, k=n))
