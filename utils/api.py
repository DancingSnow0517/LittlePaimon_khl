from typing import List, Optional

from khl_card.accessory import Kmarkdown
from khl_card.modules import Section


class CommandInfo:
    name: str
    aliases: List[str]
    usage: str
    introduce: str

    def __init__(self, name: str, aliases: Optional[List[str]], usage: str, introduce: str) -> None:
        self.name = name
        self.aliases = aliases
        self.usage = usage
        self.introduce = introduce

    def build_kmd(self) -> Section:
        return Section(Kmarkdown(
            f'**{self.name} 命令使用帮助**\n---\n> **别名: **{", ".join(self.aliases) if self.aliases is not None else "无"}\n**描述: **{self.introduce}\n**用法: **{self.usage}\n'))
