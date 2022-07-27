from typing import List

from khl_card.accessory import _BaseText, Kmarkdown
from khl_card.card import Card
from khl_card.modules import Section, Header
from khl_card.types import ThemeTypes


class CommandInfo:
    name: str
    aliases: List[str]
    usage: _BaseText
    introduce: _BaseText

    def __init__(self, name: str, aliases: List[str], usage: _BaseText, introduce: _BaseText) -> None:
        self.name = name
        self.aliases = aliases
        self.usage = usage
        self.usage.content = "用法：" + self.usage.content
        self.introduce = introduce
        self.introduce.content = "描述：" + self.introduce.content

    def build_card(self) -> Card:
        return Card(
            Header(f'{self.name} 命令使用帮助'),
            Section(Kmarkdown(f'别名：{self.aliases}')),
            Section(self.usage),
            Section(self.introduce),
            theme=ThemeTypes.INFO
        )
