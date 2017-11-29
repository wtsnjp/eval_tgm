import logging as log

def get_logger(name):
    logger    = log.getLogger(name)
    handler   = log.StreamHandler()
    formatter = log.Formatter('%(name)s %(levelname)s: %(message)s')

    handler.setLevel(log.DEBUG)
    handler.setFormatter(formatter)

    logger.setLevel(log.DEBUG)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
