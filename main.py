# Library imports
from discord import Embed
from discord.ext.commands import Bot, has_permissions
import re

# Custom file imports
from functions import load_config, load_relay_info, save_relay_info
from classes import Parrot, Keyword

CONFIG = load_config()

bot = Bot(command_prefix=CONFIG["command_prefix"] + " ", case_insensitive=True)

# List of all keywords
KEYWORDS_TO_CHANNELS = load_relay_info()

async def resend(embed, channelID):
    global KEYWORDS_TO_CHANNELS

    # Combine title, description and author name for easy searching
    title = "" if embed.title == Embed.Empty else embed.title 
    desc = "" if embed.description == Embed.Empty else embed.description 
    author = "" if embed.author.name == Embed.Empty else embed.author.name
    
    message = ' '.join([title, desc, author]).lower()

    dictEmbed = embed.to_dict()
    try:
        fields = dictEmbed["fields"]

        for field in range(0, len(fields)):
            if fields[field]["name"] == "":
                fields[field]["name"] = "** **"
            if fields[field]["value"] == "":
                fields[field]["value"] = "** **"     
    except:
        pass
    
    dictEmbed["fields"] = fields

    try:
        channelsToResendSendTo = KEYWORDS_TO_CHANNELS[str(channelID)].get_channels_to_send_to(message)
    except:
        return

    for channelID in channelsToResendSendTo:
        channel = bot.get_channel(channelID)
        await channel.send(embed=Embed.from_dict(dictEmbed))

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

    channelID = message.channel.id
    for embed in message.embeds:
        await resend(embed, channelID)

# list channels
@bot.command()
async def channels(ctx, *args):
    global KEYWORDS_TO_CHANNELS

    embed = Embed(title="ParrotBot Channels", description="A list of all channels that ParrotBot relays messages to.")
    
    relayChannelIDs = []
    monitoredChannelIDs = []
    for channelID in KEYWORDS_TO_CHANNELS:
        relayChannelIDs += KEYWORDS_TO_CHANNELS[channelID].get_all_channels()
        monitoredChannelIDs.append(channelID)

    embedFieldText = []
    for channel in monitoredChannelIDs:
        channelObj = bot.get_channel(int(channel))
        embedFieldText.append("{}".format(channelObj.mention))

    if len(embedFieldText) > 0:
        embed.add_field(name="Channels which are being monitored", value='\n'.join(embedFieldText), inline=False)
    else:
        embed.add_field(name="Channels which are being monitored", value="No channels have been set up!", inline=False)

    embedFieldText = []
    for channel in set(relayChannelIDs):
        channelObj = bot.get_channel(int(channel))
        embedFieldText.append("{}".format(channelObj.mention))

    if len(embedFieldText) > 0:
        embed.add_field(name="Channels which have embeds posted to them (you can delete these)", value='\n'.join(embedFieldText), inline=False)
    else:
        embed.add_field(name="Channels which have embeds posted to them (you can delete these)", value="No channels have been set up!", inline=False)

    await ctx.message.channel.send(embed=embed)

# add channel
@bot.command()
async def add(ctx, *args):
    global KEYWORDS_TO_CHANNELS

    if not ctx.message.author.guild_permissions.manage_channels:
        return
    
    await ctx.message.channel.send("You have started the process of adding a relay channel.")

    await ctx.message.channel.send("Please tag the channel you wish to have messages relayed **to** below!")
    text = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
    text = text.content
    try:
        targetChannelID = int(re.findall("[0-9]{18}", text)[0])
        targetChannel = bot.get_channel(targetChannelID)
    except Exception as e:
        await ctx.message.channel.send("Channel could not be found - please try again!")
        return
    
    await ctx.message.channel.send("Awesome! The target channel has been set to {}".format(targetChannel.mention))
    
    await ctx.message.channel.send("Please tag the channel/s you wish to have messages relayed **from**!")
    text = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
    text = text.content
    try:
        monitoredChannelIDs = re.findall("[0-9]{18}", text)
        if len(monitoredChannelIDs) < 1:
            await ctx.message.channel.send("No channel was tagged. Try again!")
            return

        channelMentions = ""
        for channelID in monitoredChannelIDs:
            channel = bot.get_channel(int(channelID))
            channelMentions += "{}".format(channel.mention)

    except Exception as e:
        await ctx.message.channel.send("One or more channels could not be found - please try again!")
        return

    await ctx.message.channel.send("Great! Channel/s has/have been set as {}! Now enter the keywords you wish to filter messages by for this channel, seperated by a comma (\",\") with + or - prefixes!\ne.g `+hey,+these,-are,-my,-keywords`".format(channelMentions))
    keywords = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)

    positiveKeywords = []
    negativeKeywords = []
    for keyword in keywords.content.split(','):
        if keyword.startswith("+"):
            positiveKeywords.append(keyword[1::])
        elif keyword.startswith("-"):
            negativeKeywords.append(keyword[1::])
        else:
            await ctx.message.channel.send("{} wasn't prefixed with a `+` or `-`. Ignoring it and using the rest of the keywords!".format(keyword))

    for channel in monitoredChannelIDs:
        try:
            parrotObj = KEYWORDS_TO_CHANNELS[channel]
            keywordObj = Keyword(positiveKeywords, negativeKeywords, [targetChannelID])
            parrotObj.keywords.append(keywordObj)
            
        except Exception as e:
            parrotObj = Parrot([{"positive": positiveKeywords, "negative": negativeKeywords, "channelsToSendTo": [targetChannelID]}])
            KEYWORDS_TO_CHANNELS[channel] = parrotObj
    
    save_relay_info(KEYWORDS_TO_CHANNELS)
    KEYWORDS_TO_CHANNELS = load_relay_info()
    await ctx.message.channel.send("Sweet! {} is all set up and ParrotBot has restarted!".format(targetChannel.mention))

# remove channel
@bot.command()  
async def remove(ctx, *args):
    global KEYWORDS_TO_CHANNELS

    if not ctx.message.author.guild_permissions.manage_channels:
        return

    await ctx.message.channel.send("You have started the process of removing a relay channel. Please tag the channel you wish to remove in your next message!")
    text = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
    text = text.content
    try:
        channelIDToDelete = re.findall("[0-9]{18}", text)[0]
        channel = bot.get_channel(int(channelIDToDelete))

        relayChannelIDs = []
        for channelID in KEYWORDS_TO_CHANNELS:
            relayChannelIDs += KEYWORDS_TO_CHANNELS[channelID].get_all_channels()
        
        if int(channelIDToDelete) not in set(relayChannelIDs):
            await ctx.message.channel.send("Channel could not be found - please try again!")
            return

    except Exception as e:
        await ctx.message.channel.send("Channel could not be found - please try again!")
        return
    
    await ctx.message.channel.send("The channel you wish to delete is {}. To confim, reply with \"CONFIRM\". Otherwise reply with anything else!".format(channel.mention))
    confirmation = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
    if confirmation.content != "CONFIRM":
        await ctx.message.channel.send("Deletion aborted!")
        return
    

    parrotsToDelete = []
    for parrotObj in KEYWORDS_TO_CHANNELS:
        KEYWORDS_TO_CHANNELS[parrotObj].remove_channel_from_keyword(channelIDToDelete)
        if len(KEYWORDS_TO_CHANNELS[parrotObj].keywords) < 1:
            parrotsToDelete.append(parrotObj)

    for parrotObj in parrotsToDelete:
        del KEYWORDS_TO_CHANNELS[parrotObj]

    
    save_relay_info(KEYWORDS_TO_CHANNELS)
    KEYWORDS_TO_CHANNELS = load_relay_info()
    await ctx.message.channel.send("Successfully removed relay channel and ParrotBot has restarted!!")

@bot.command()
async def commands(ctx, *args):
    if not ctx.message.author.guild_permissions.manage_channels:
        return

    await ctx.message.channel.send(">>parrot channels -> Returns all the channel links and their keywords\n>>parrot add -> Start the process of creating a new channel link\n>>parrot remove -> Start the process of removing a channel link\n>>parrot commands -> Returns a list of available commands")


bot.run(CONFIG["bot_token"])
