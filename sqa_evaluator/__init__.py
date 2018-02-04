# package declaration
__all__ = ['tgm_evaluator']

# logging
import logging as log


def get_logger(name, debug=False):
    logger = log.getLogger(name)
    handler = log.StreamHandler()
    formatter = log.Formatter('%(name)s %(levelname)s: %(message)s')
    level = log.DEBUG if debug else log.WARN

    handler.setLevel(level)
    handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
