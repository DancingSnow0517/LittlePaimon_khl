import sys

from utils.config import config
from utils.logger import ColoredLogger, patch_get_logger

log = ColoredLogger('LittlePaimon', level=config.log_level)

if __name__ == '__main__':
    patch_get_logger(log)
    log.info('正在启动 LittlePaimon')
    from bot import main
    sys.exit(main())
