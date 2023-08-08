import os
import sys
import logging
import logging.handlers


def create_logger(project="", debug=False, level="DEBUG"):
    """通用日志类生成模块

    Args:
        project(str, optional): 日志项目名称. Defaults to "".
        debug (bool, optional): 调试模式启用/关闭. Defaults to False.
        level (str, optional): 日志等级. Defaults to "DEBUG".
    Returns:
        logger (): 日志实例
    """

    if not debug:
        pwd = os.path.dirname(__file__)
        if not os.path.exists(os.path.join(pwd, "log")):
            os.makedirs(os.path.join(pwd, "log"))

        log_filename = os.path.join(pwd, "log/running.log")
        handler = logging.handlers.RotatingFileHandler(
            log_filename, maxBytes=1024*1024*10, backupCount=10
        )
        logging.basicConfig(
            format='[%(levelname)-8s] %(asctime)s %(filename)s[%(funcName)s-line:%(lineno)d] %(message)s',
            datefmt='%a, %Y-%m-%d %H:%M:%S',
            level=level.upper(),
            handlers=[handler]
        )
        logger = logging.getLogger(project)
    else:
        logger = logging.getLogger(__name__)
        logger.setLevel(level.upper())
        handler = logging.StreamHandler(sys.stdout)
        logformat = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(logformat)
        logger.addHandler(handler)
    logger.info(f"Starting {project}...")

    return logger