import discord
from discord.ext import commands
from discord.ext.commands import Bot, AutoShardedBot, when_mentioned_or, CheckFailure
from discord.utils import get

import time, timeago
from datetime import datetime
from config import config
import click
import sys, traceback
import asyncio

WORD_FILTER = ["libra", "http", "cheap", "buy", "fаcebook", "imgur", "website", "tweet", "twit", ".net", ".com", ".io", ".org", ".gq"]
NAME_FILTER = ["_bot", "giveaway", "glveaway", "give_away", "b0t"]

bot = AutoShardedBot(command_prefix=['.', '!', '?'], case_insensitive=True)
bot.remove_command("help")

@bot.event
async def on_shard_ready(shard_id):
    print(f'Shard {shard_id} connected')

@bot.event
async def on_ready():
    botLogChan = bot.get_channel(id=config.discord.channelID)
    botReactChan = bot.get_channel(id=config.discord.CaptchaChanID)
    print('------')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    print(str(datetime.now()))
    to_send = 'Bot was started!'



    game = discord.Game(name=config.config.gameName)
    await bot.change_presence(status=discord.Status.online, activity=game)

@bot.event
async def on_message(message):
    global WORD_FILTER
    botLogChan = bot.get_channel(id=config.discord.channelID)
    if any(word.lower() in message.content.lower() for word in WORD_FILTER):
        member = message.author
        account_created = member.created_at
        account_joined = member.joined_at
        if (datetime.utcnow() - account_joined).total_seconds() < config.config.warnPeriod or \
        (datetime.utcnow() - account_created).total_seconds() < config.config.warnPeriod:
            # If just joined and post filtered word
            try:
                await message.delete()
                to_send = '{0.name} (`{1.id}`) has been removed from {2.name}! Spammer / Scammer!'.format(member, member, member.guild)
                await member.send(to_send)
                await botLogChan.send(to_send)
                await member.guild.kick(member)
                print(str(datetime.now()), to_send)
            except Exception as e:
                print(e)

@bot.event
async def on_member_join(member):
    global NAME_FILTER
    EMOJI_OK_BOX = "\U0001F197"
    EMOJI_OK_HAND = "\U0001F44C"
    botLogChan = bot.get_channel(id=config.discord.channelID)
    botReactChan = bot.get_channel(id=config.discord.CaptchaChanID)
    account_created = member.created_at
    time_out_react = config.config.timeout

    # send messages to log and captcha/react channel
    if (datetime.utcnow() - account_created).total_seconds() >= config.config.warnPeriod:
        to_send = '{0.name} (`{1.id}`) has joined {2.name}!'.format(member, member, member.guild)
    else:
        to_send = '{0.name} (`{1.id}`) has joined {2.name}! **Warning!!!**, {3.name} just created his/her account less than'.format(member, member, member.guild, member) + ' %s ago.' % (config.config.warnPeriodText)
    await botLogChan.send(to_send)
    print(str(datetime.now()), to_send)

    # if name contain name filter.
    if any(word.lower() in member.name.lower() for word in NAME_FILTER):
        try:
            msg = await member.send("{} Your name is in filtered list in {}. We remove you from {} server. Sorry for this inconvenience.".format(member.mention, member.guild.name, member.guild.name))
        except (discord.Forbidden, discord.errors.Forbidden) as e:
            pass
        await member.guild.kick(member)
        to_send = '{0.name} (`{1.id}`) has been removed from {2.name}! Filtered name matched.'.format(member, member, member.guild)
	print(str(datetime.now()), to_send)
        await botLogChan.send(to_send)
        return

    try:
        captchaMsg = await member.send("{} Please re-act OK in this message within {}s. Otherwise, we will consider you as bot and remove you from {} server. You can re-act also on my public mention message.".format(member.mention, time_out_react, member.guild.name))
        await captchaMsg.add_reaction(EMOJI_OK_BOX)
        captchaMsg = await botReactChan.send("{} Please re-act OK in this message within {}s. Otherwise, we will consider you as bot and remove you from {} server. You can also re-act on my DM.".format(member.mention, time_out_react, member.guild.name))
        await captchaMsg.add_reaction(EMOJI_OK_BOX)
    except (discord.Forbidden, discord.errors.Forbidden) as e:
        pass

    def check(reaction, user):
        return user == member and ((reaction.emoji == EMOJI_OK_BOX or reaction.emoji == EMOJI_OK_HAND)) and reaction.message.author == bot.user
    try:
        reaction, user =  await bot.wait_for('reaction_add', timeout=time_out_react, check=check)
    except asyncio.TimeoutError:
        # user did not react
        # get user, they might left or got kicked from spamming before timeout
        if (member.guild.id == config.discord.guildID):
            get_member = bot.get_user(id=member.id)
        if get_member:
            to_send = '{0.name} (`{1.id}`) has been removed from {2.name} for not responding on OK emoji.'.format(member, member, member.guild)
            await botLogChan.send(to_send)
            print(str(datetime.now()), to_send)
            try:
                await member.send("You have been removed from {} because of timeout on requested re-action. Sorry for this inconvenience.".format(member.guild.name))
            except:
                pass
            if (await member.guild.kick(member)):
		print(str(datetime.now()), 'User {0.name} was kicked from {2.name}').format(member, member.guild)
    else:
        # check if user re-act (was no exception)
        try:
            await botReactChan.send("Thank you {0.mention} for verification.".format(member))
            await member.send("Thank you {0.mention} for verification.".format(member))
            print(str(datetime.now()), 'User {0.mention} was verified by reaction.'.format(member))
        except (discord.Forbidden, discord.errors.Forbidden) as e:
            pass
    await captchaMsg.delete()

@bot.event
async def on_member_remove(member):
    botLogChan = bot.get_channel(id=config.discord.channelID)
    to_send = '{0.name} (`{1.id}`) has left {2.name}!'.format(member, member, member.guild)
    await botLogChan.send(to_send)
    print(str(datetime.now()), to_send)


@click.command()
def main():
    bot.run(config.discord.token, reconnect=True)


if __name__ == '__main__':
    main()
