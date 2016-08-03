import os
import logging
import logging.handlers as logging_handler

class logger(object):
    def get_logger(self, name='tattle'):

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        #self.logger.setLevel(logging.INFO)

        TATTLE_HOME = os.environ.get('TATTLE_HOME')
        #print os.environ
        LOG_FILENAME = os.path.join(TATTLE_HOME, 'var', 'log', 'tattle.log')

        # clear any built up log handlers
        if self.logger.handlers:
            self.logger.handlers = []

        handler = logging_handler.RotatingFileHandler(LOG_FILENAME, maxBytes=10002400, backupCount=5)
        log_format = logging.Formatter("%(asctime)s [%(levelname)-s] - [%(name)s] - [%(module)s] - [%(funcName)s] - %(message)s")
        handler.setFormatter(log_format)
        self.logger.addHandler(handler)

        return self.logger
