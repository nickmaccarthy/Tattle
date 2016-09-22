import os
import logging
import logging.handlers as logging_handler

TATTLE_HOME = os.environ.get('TATTLE_HOME')

import tattle.config
log_cfg = tattle.config.load_configs().get('logging')

''' main logger class '''
class logger(object):
    def get_logger(self, name='tattle'):
        if log_cfg.get('log_directory'):
            if '$TATTLE_HOME' in log_cfg.get('log_directory'):
                parts = log_cfg.get('log_directory').split('/')
                parts = [ x for x in parts if x != '' ] # remove any empty elements
                if '$TATTLE_HOME' in parts[0]: del(parts[0])
                log_dir = os.path.join(TATTLE_HOME, *parts)
            else:
                log_dir = log_cfg.log_directory
        else:
            log_dir = os.path.join(TATTLE_HOME, 'var', 'log')


        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_cfg.get('level', 'WARN').upper()))

        LOG_FILENAME = os.path.join(log_dir, 'tattle.log')

        # clear any built up log handlers
        if self.logger.handlers:
            self.logger.handlers = []

        handler = logging_handler.RotatingFileHandler(LOG_FILENAME, maxBytes=log_cfg.get('max_bytes', 10002400), backupCount=log_cfg.get('backup_count', 5))
        log_format = logging.Formatter("%(asctime)s [%(levelname)-s] - [%(name)s] - [%(module)s] - [%(funcName)s] - %(message)s")
        handler.setFormatter(log_format)
        self.logger.addHandler(handler)

        return self.logger
