# 這裡是主程式
# Author : Alone0506
# Date: 2022/04/30
#
# discord.__version__ = 1.7.3
# python.__version__ = 3.10.4 64-bit
#
# abbreviation definition:
# sub = subscribe
# unsub = unsubscribe
# info = information
# dict = dictionary
#
# ############

import discord
# import logging
from discord_components import DiscordComponents, Button, ActionRow
from discord.ext import commands, tasks

from web_spider import Anime
from handle_sub_info import Handle_sub_info
import keep_alive
from random import randint

bot = commands.Bot(command_prefix='$', help_command=None)
DiscordComponents(bot)
# disord emoji樣式用的跟Twitter一樣
sub_emoji = '\U0001F493'
unsub_emoji = '\U0001F494'
bot_emoji = '\U0001F916'
bug_emoji = '\U0001FAB2'
book_emoji = '\U0001F4D6'

invited_bot_url = "https://discord.com/api/oauth2/authorize?client_id=965889341991825409&permissions=2684373072&scope=bot"
add_friend_url = "https://discordapp.com/users/432431174397198339"
github_url = "https://github.com/Alone0506/discord_anime_bot.git"
thumbnail_url = "https://c.tenor.com/l5REW5PZ9ZQAAAAd/nanashi-mumei-hololive.gif"

check_time = randint(5, 8)


@bot.event
# 當機器人完成啟動時
async def on_ready():
    print(f'目前登入身份：{bot.user}')
    game = discord.Game('Mumei')
    # discord.Status.<狀態>，可以是online,offline,idle,dnd,invisible
    await bot.change_presence(status=discord.Status.online, activity=game)
    check_update.start()


@bot.event
async def on_guild_join(guild):
    await guild.create_text_channel("anime-channel")
    discord.utils.get(guild.text_channels, name="anime-channel")


@tasks.loop(minutes=check_time)
async def check_update():
    global check_time

    new_anime_dict = Anime().newanime_info()
    user_sub = Handle_sub_info()
    user_sub.txt_to_dict()
    user_sub_dict = user_sub.info_dict

    for user_id in user_sub_dict:
        for episode, anime_name in user_sub_dict[user_id]:
            if anime_name in new_anime_dict:
                if episode not in new_anime_dict[anime_name]:
                    embed = discord.Embed(
                        title="動畫名稱", description=anime_name, color=0xff6600)
                    embed.add_field(
                        name="最新集數", value=new_anime_dict[anime_name][1], inline=True)
                    embed.add_field(
                        name="最新一集更新時間", value=new_anime_dict[anime_name][2], inline=True)
                    embed.add_field(
                        name="動畫網址", value=new_anime_dict[anime_name][3], inline=False)
                    embed.set_thumbnail(url=new_anime_dict[anime_name][4])
                    embed.set_image(url=new_anime_dict[anime_name][4])

                    idx = user_sub_dict[user_id].index(
                        [episode, anime_name])
                    user_sub_dict[user_id][idx][0] = new_anime_dict[anime_name][1]
                    try:
                        #如果user在訂閱後離開伺服器, 抓使用者時會產生Exception
                        userr = await bot.fetch_user(user_id)
                        await userr.send("追隨中的動畫已更新", embed=embed)
                    except Exception:
                        pass

            else:
                user_sub_dict[user_id].remove([episode, anime_name])
                try:
                    userr = await bot.fetch_user(user_id)
                    await userr.send(f"{anime_name} 因為已完結或移出動畫瘋的的新番列表, 所以已經自動取消追隨.")
                except Exception:
                    pass

    user_sub.dict_to_txt(user_sub_dict)
    check_time = randint(5, 8)


@bot.command()
async def sublist(ctx):
    user_sub = Handle_sub_info()
    user_sub.txt_to_dict()
    user_sub_dict = user_sub.info_dict

    if user_sub_dict == {}:
        response = f"{ctx.author.mention} 目前無訂閱"
        await ctx.send(response, ephemeral=True)

    for user_id in user_sub_dict:
        try:
            user_name = await bot.fetch_user(user_id)
        except Exception:
            pass
        for episode, anime_name in user_sub_dict[user_id]:
            if user_name == ctx.author:
                response = f"{ctx.author.mention} 已訂閱 {anime_name}"
                await ctx.send(response,
                               components=[Button(label="取消訂閱",
                                                  style="2",
                                                  emoji=unsub_emoji,
                                                  custom_id=f"unsubscribe {episode} {anime_name}")])


@bot.command()
async def new(ctx):
    info_dict = Anime().newanime_info()

    if isinstance(info_dict, int):
        await ctx.send("錯誤代碼 : ", info_dict)
        return
    else:
        for anime_name, info in info_dict.items():
            embed = discord.Embed(
                title="動畫名稱", description=anime_name, color=0xeee657)
            embed.add_field(name="觀看次數", value=info[0], inline=True)
            embed.add_field(name="最新集數", value=info[1], inline=True)
            embed.add_field(name="最新一集更新時間", value=info[2], inline=False)
            embed.add_field(name="動畫網址", value=info[3], inline=False)
            embed.set_thumbnail(url=info[4])
            embed.set_image(url=info[4])
            if info[1] == "此為OVA或電影":
                await ctx.send(embed=embed)
            else:
                btn = [Button(label="訂閱", style="3", emoji=sub_emoji, custom_id=f"subscribe {info[1]} {anime_name}"), Button(
                    label="取消訂閱", style="2", emoji=unsub_emoji, custom_id=f"unsubscribe {info[1]} {anime_name}")]
                row_btn = ActionRow(*btn)
                await ctx.send(embed=embed, components=[row_btn])

            # custom_id 最多100個字元"追 隨" = 3個字元


@bot.event
async def on_button_click(interaction):
    user_name = interaction.user
    user_id = str(interaction.user.id)
    sub_or_unsub = interaction.custom_id.split(" ", 2)[0]
    episode = interaction.custom_id.split(" ", 2)[1]
    anime_name = interaction.custom_id.split(" ", 2)[2]

    if sub_or_unsub == "subscribe":
        user_sub = Handle_sub_info()
        if user_sub.issub(user_id, episode, anime_name):
            await interaction.respond(content=f"{user_name}\t此動漫已在訂閱列表中", ephemeral=True)

        else:
            user_sub.info_dict[user_id].append([episode, anime_name])
            user_sub.dict_to_txt(user_sub.info_dict)
            await interaction.respond(content=f"{user_name}\t已訂閱\t{anime_name}", ephemeral=True)
    else:  # sub_or_unsub == "unsubscribe"
        user_unsub = Handle_sub_info()
        user_unsub.txt_to_dict()
        user_unsub_dict = user_unsub.info_dict

        if user_id not in user_unsub_dict or [episode, anime_name] not in user_unsub_dict[user_id]:
            await interaction.respond(content=f"{user_name}\t原本就沒訂閱", ephemeral=True)

        else:
            user_unsub_dict[user_id].remove([episode, anime_name])
            user_unsub.dict_to_txt(user_unsub_dict)
            await interaction.respond(content=f"{user_name}\t已取消訂閱 {anime_name}", ephemeral=True)


@bot.command()
async def renew(ctx):
    anime_info = Anime().renew()
    print(anime_info)
    for day, infos in anime_info.items():

        if len(infos[0]) == 2:
            embed = discord.Embed(
                title="預計更新時間", description=infos[0][0], color=0xeee657)
            embed.set_thumbnail(url=infos[0][1])
            await ctx.send(day, embed=embed)

        else:
            for info in infos:
                embed = discord.Embed(
                    title="動畫名稱", description=info[0], color=0xeee657)
                embed.add_field(name="預計更新時間", value=info[1], inline=True)
                embed.add_field(name="集數", value=info[2], inline=True)
                await ctx.send(day, embed=embed)


bot.remove_command('help')


@bot.command()
async def help(ctx):

    embed = discord.Embed(title="指令列表", description="目前的指令如下", color=0xc54343)
    embed.add_field(name="$help", value="列出所有指令", inline=False)
    embed.add_field(name="$new", value="列出已更新的本季新番", inline=False)
    embed.add_field(name="$renew", value="列出這周預訂更新的新番列表", inline=False)
    embed.add_field(name="$sublist", value="列出你目前的訂閱新番", inline=False)
    embed.add_field(name=f"{bot_emoji}邀請bot到你的伺服器",
                    value=invited_bot_url, inline=False)
    embed.add_field(name=f"{bug_emoji}bug 回報",
                    value=add_friend_url, inline=False)
    embed.add_field(name=f"{book_emoji}GitHub Open Source",
                    value=github_url, inline=False)
    embed.set_thumbnail(url=thumbnail_url)
    await ctx.send(embed=embed)

keep_alive.keep_alive()
bot.run("OTY1ODg5MzQxOTkxODI1NDA5.Yl5wjA.xh8N4oiSPCQDAZ0bxQJUd3sDXn4")
