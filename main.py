# Library imports
from discord import Embed
from discord.ext.commands import Bot, has_permissions
import threading
import re

# Custom file imports
from functions import load_config, load_relay_info, save_relay_info

CONFIG = load_config()

bot = Bot(command_prefix=CONFIG["command_prefix"] + " ", case_insensitive=True)

# List of all keywords
KEYWORDS, KEYWORDS_TO_CHANNELS, CHANNELS = load_relay_info()

async def resend(embed):
    global KEYWORDS
    subject = ' '.join([embed.title, embed.description, embed.author.name]).lower()

    channelsToResendTo = []
    for keyword in KEYWORDS:
        if keyword in subject:
            channelsToResendTo += KEYWORDS_TO_CHANNELS[keyword]
    
    channelsToResendTo = set(channelsToResendTo)

    for channelID in channelsToResendTo:
        channel = bot.get_channel(channelID)
        await channel.send(embed=embed)

# Listen for messages
@bot.listen('on_message')
async def message_event(message):
    global CONFIG

    # Check if the message is a command
    if message.content.startswith(CONFIG["command_prefix"]):
        return
    
    # Check the message was sent via webhook
    if not message.webhook_id:
        return
    
    for embed in message.embeds:
        await resend(embed)

# list channels
@bot.command()
async def channels(ctx, *args):
    global KEYWORDS_TO_CHANNELS
    global CHANNELS

    embed = Embed(title="ParrotBot Channels", description="A list of all channels that ParrotBot relays messages to.")
    
    embedFieldText = []
    channels_dict = {}

    for channel in CHANNELS:
        keywords_list = []
        for keyword in KEYWORDS_TO_CHANNELS:
            if channel in KEYWORDS_TO_CHANNELS[keyword]:
                keywords_list.append(keyword)
        
        channels_dict[channel] = keywords_list

    for channel in channels_dict:
        channelName = bot.get_channel(channel).name
        embedFieldText.append("Channel Name: **{}** Keywords: **{}**".format(channelName, '**, **'.join(channels_dict[channel])))
    
    embed.add_field(name="Channels", value='\n'.join(embedFieldText), inline=False)
    await ctx.message.channel.send(embed=embed)
        

# add channel
@bot.command()
async def add(ctx, *args):
    global KEYWORDS
    global CHANNELS
    global KEYWORDS_TO_CHANNELS

    if not ctx.message.author.guild_permissions.administrator:
        return
    
    await ctx.message.channel.send("You have started the process of adding a relay channel.")
    await ctx.message.channel.send("Please tag the channel you wish to have messages relayed to below!")
    
    text = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
    text = text.content
    try:
        channelID = int(re.findall("[0-9]{18}", text)[0])
        channel = bot.get_channel(channelID)
    except Exception as e:
        await ctx.message.channel.send("Channel could not be found - please try again!")
        return

    await ctx.message.channel.send("Great! Channel has been set as {}! Now enter the keywords you wish to filter messages by for this channel, seperated by a comma (\",\")!\nhey, these, are, my, keywords".format(channel.mention))
    keywords = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)

    for keyword in keywords.content.split(','):
        try:
            KEYWORDS_TO_CHANNELS[keyword].append(channelID)
        except:
            KEYWORDS_TO_CHANNELS[keyword] = [channelID] 

    save_relay_info(KEYWORDS_TO_CHANNELS)
    KEYWORDS, KEYWORDS_TO_CHANNELS, CHANNELS = load_relay_info()

    await ctx.message.channel.send("Sweet! {} is all set up and ParrotBot has restarted!".format(channel.mention))

# remove channel
@bot.command()  
async def remove(ctx, *args):
    global KEYWORDS
    global CHANNELS
    global KEYWORDS_TO_CHANNELS

    if not ctx.message.author.guild_permissions.administrator:
        return

    await ctx.message.channel.send("You have started the process of removing a relay channel. Please tag the channel you wish to remove in your next message!")
    text = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
    text = text.content
    try:
        channelID = int(re.findall("[0-9]{18}", text)[0])
        channel = bot.get_channel(channelID)
    except Exception as e:
        await ctx.message.channel.send("Channel could not be found - please try again!")
        return
    
    await ctx.message.channel.send("The channel you wish to delete is {}. To confim, reply with \"CONFIRM\". Otherwise reply with anything else!".format(channel.mention))
    confirmation = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
    if confirmation.content != "CONFIRM":
        await ctx.message.channel.send("Deletion aborted!")
        return
    
    keywordsToDelete = []
    for keyword in KEYWORDS_TO_CHANNELS:
        try:
            KEYWORDS_TO_CHANNELS[keyword].remove(channelID)
            if len(KEYWORDS_TO_CHANNELS[keyword]) == 0:
                keywordsToDelete.append(keyword)
        except:
            pass
    
    for keyword in keywordsToDelete:
        del KEYWORDS_TO_CHANNELS[keyword]

    save_relay_info(KEYWORDS_TO_CHANNELS)
    KEYWORDS, KEYWORDS_TO_CHANNELS, CHANNELS = load_relay_info()

    await ctx.message.channel.send("Successfully removed relay channel and ParrotBot has restarted!!")

@bot.command()
async def commands(ctx, *args):
    if not ctx.message.author.guild_permissions.administrator:
        return

    await ctx.message.channel.send(">>parrot channels -> Returns all the channel links and their keywords\n>>parrot add -> Start the process of creating a new channel link\n>>parrot remove -> Start the process of removing a channel link\n>>parrot commands -> Returns a list of available commands")


bot.run(CONFIG["bot_token"])
