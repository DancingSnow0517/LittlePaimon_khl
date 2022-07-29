import enum
from typing import List, Optional

from khl import Message, Bot
from khl_card.accessory import Kmarkdown
from khl_card.modules import Section

from khl.command import rule


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
        # kmd = f'**{self.introduce}**\n---\n> **别名: **{", ".join(self.aliases) if self.aliases is not None else "无"}\n**用法: **`{self.usage}`'
        kmd = f'---\n**{self.name} 命令使用帮助**\n> **别名: **{", ".join(self.aliases) if self.aliases is not None else "无"}\n**描述: **{self.introduce}\n**用法: **{self.usage}\n'
        return Section(Kmarkdown(kmd))


class CommandGroups(enum.Enum):
    GACHA = 'gacha'
    GAME = 'game'
    INFO = 'info'
    SIGN = 'sign'


class MyRules:
    @staticmethod
    def is_admin() -> rule.TypeRule:
        async def rule(msg: Message) -> bool:
            roles = (await msg.ctx.guild.fetch_user(msg.author.id)).roles
            guild_roles = await msg.ctx.guild.fetch_roles()
            for role in guild_roles:
                if role.has_permission(0) and role.id in roles:
                    return True
            return False

        return rule
