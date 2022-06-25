import logging
import os.path
import sys

from khl import Bot

from utils.config import Config
from paimon_chat import paimon_chat


class LittlePaimonBot(Bot):

    def __init__(self):
        self.config = Config.load()
        super().__init__(self.config.token)
        logging.basicConfig(level=self.config.log_level,
                            format='[%(asctime)s] [%(module)s] [%(threadName)s/%(levelname)s]: %(message)s')

    async def start(self):
        # 检查数据文件夹是否存在
        if not os.path.exists(self.config.data_path):
            os.mkdir(self.config.data_path)
        elif not os.path.isdir(self.config.data_path):
            raise Exception(f'{self.config.data_path} 不是一个文件夹')
        await self.on_startup()
        await super().start()

    async def on_startup(self):
        await paimon_chat.on_startup(self)
        ...


def main():
    bot = LittlePaimonBot()
    bot.run()
    ...


if __name__ == '__main__':
    sys.exit(main())
