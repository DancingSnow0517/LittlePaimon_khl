from enum import Enum
from typing import List, Optional

from khl import Message
from khl.command import rule
from khl_card.accessory import Kmarkdown, Button
from khl_card.modules import Section


class CommandGroups(Enum):
    GAME = '游戏'
    INFO = '信息'
    SIGN = '签到'
    CLOUD_GENSHIN = '云原神'
    WIKI = 'WIKI'

    def build_button(self) -> Button:
        return Button(Kmarkdown(f'查看 **{str(self.value)}** 分组的命令'), value=f'command_group_{self.name}',
                      click='return-val', theme='info')


class CommandInfo:
    name: str
    aliases: List[str]
    usage: str
    introduce: str
    groups: List[CommandGroups]

    def __init__(self, name: str, aliases: Optional[List[str]], usage: str, introduce: str,
                 group: List[CommandGroups]) -> None:
        self.name = name
        self.aliases = aliases
        self.usage = usage
        self.introduce = introduce
        self.groups = group

    def build_kmd(self) -> Section:
        # kmd = f'**{self.introduce}**\n---\n> **别名: **{", ".join(self.aliases) if self.aliases is not None else "无"}\n**用法: **`{self.usage}`'
        kmd = f'---\n**{self.name} 命令使用帮助**\n> **别名: **{", ".join(self.aliases) if self.aliases is not None else "无"}\n**描述: **{self.introduce}\n**用法: **{self.usage}\n**分组: **{", ".join([str(group.value) for group in self.groups])}'
        return Section(Kmarkdown(kmd))


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
