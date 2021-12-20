import requests
import discord
import json
import asyncio
import sys
from random import randint
from discord.ext import commands

base = "https://example.com/"


def getData():
    req = requests.get(base + "read.php")
    return req.text


def setData(data):
    req = requests.get(base + "write.php?data=" + data)
    return req.text


sys.stdout.reconfigure(encoding="utf-8")
client = commands.Bot(command_prefix="t!")
books = {}

with open("tao_te_ching.json", encoding="utf-8") as stream:
    books["tao_te_ching"] = json.load(stream)

with open("tao_te_ching_cn.json", encoding="utf-8") as stream:
    books["tao_te_ching_cn"] = json.load(stream)

with open("zuang_zi.json", encoding="utf-8") as stream:
    books["zuang_zi"] = json.load(stream)

clientSettings = json.loads(getData())

# git add .
# git commit -am "a"
# git push heroku master

timeInSeconds = 60


def getPassage(book, passageNumber):
    return (books[book][passageNumber])


def getFormattedPassage(book, passageNumber):
    Passage = getPassage(book, passageNumber)
    Title, Text, Source = "", "", ""
    if book == "tao_te_ching":
        Title = "**Dào dé jīng verse " + passageNumber + "**"
        Source = "https://www.wussu.com/laotzu/laotzu" + (
                    int(passageNumber) < 10 and "0" + passageNumber or passageNumber) + ".html"
        for Line in Passage:
            Text += Line + "\n\n"
    elif book == "tao_te_ching_cn":
        Source = "https://www.yellowbridge.com/onlinelit/daodejing" + (
                    int(passageNumber) < 10 and "0" + passageNumber or passageNumber)
        for key, value in Passage.items():
            ChapterName = key
            for key2, value2 in value.items():
                Text += value2 + "\n\n"
        Title = "**Dào dé jīng verse " + passageNumber + " (" + ChapterName + ")**"
    elif book == "zuang_zi":
        Source = "https://ratmachines.com/philosophy/chuang-tzu-legge/chapter-" + passageNumber
        for key, value in Passage.items():
            Title = key
            Text = value
    return Title, Text.replace("\n", " "), Source

async def sendPassage(book, passageNumber, ctx):
    Title, Text, Source = getFormattedPassage(book, passageNumber)
    Splits, Part = [], 1
    if len(Text) > 1999:
        for i in range(0, len(Text), 1750):
            Splits.append(Text[i: i + 1750])
        for i in Splits:
            embed = discord.Embed(title=Title + " Part " + str(Part) + "/" + str(len(Splits)), url=Source,
                                  description=i + (Part < len(Splits) and " - continued" or ""), color=0x72faf3)
            Part += 1
            await ctx.send(embed=embed)
            await asyncio.sleep(3)
    else:
        embed = discord.Embed(title=Title, url=Source, description=Text, color=0x72faf3)
        await ctx.send(embed=embed)


async def task():
    while True:
        await asyncio.sleep(timeInSeconds)
        # for key, value in clientSettings.items():
        #    for key2, value2 in value.items():
        #        if key2 == "guildSettings":
        #            for key3, value3, in value2.items():
        #                print(key3, value3)
        for key, value in clientSettings.items():
            if "guildSettings" in value:
                guildSettings = value.get("guildSettings")
                if "announce" in guildSettings and "channelId" in guildSettings:
                    announce = guildSettings.get("announce")
                    channelId = guildSettings.get("channelId")
                    if announce == "true":
                        ctx = client.get_channel(int(channelId))
                        VerseNumber = str(randint(1, 81))
                        await sendPassage("tao_te_ching", VerseNumber, ctx)
        # if announce:
        #    ctx = client.get_channel(channelId)
        #    VerseNumber = str(randint(1, 81))
        #    await sendPassage("tao_te_ching", VerseNumber, ctx)


@client.event
async def on_ready():
    print(f"Bot online and logged in as {client.user}")
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="the Dào dé jīng (Prefix t!)"))
    client.loop.create_task(task())


@client.command(name="getChapter", aliases=["getVerse", "getPassage", "passage", "verse"],
                help="Get Chapter from various Taoist Books",
                usage="t!getChapter (optional) <chapterNumber> (optional)")
async def getChapter(ctx, chapter="1", book="tao_te_ching_a"):
    book = book.lower()
    bookMax = (book == "zuang_zi" and 33 or 81)
    if str(ctx.message.guild.id) in clientSettings:
        if str(ctx.message.author.id) in clientSettings[str(ctx.message.guild.id)]:
            if book == "tao_te_ching_a":
                book = clientSettings[str(ctx.message.guild.id)][str(ctx.message.author.id)].get("defaultBookFormat")
    book = (book == "tao_te_ching_a" and "tao_te_ching" or book)
    if chapter and chapter.isnumeric():
        VerseNumber = str(max(min(bookMax, int(chapter)), 1))
        await sendPassage(book, VerseNumber, ctx)
    elif "-" in chapter and chapter.split("-")[0] and chapter.split("-")[1]:
        split = chapter.split("-")
        for i in range(int(split[0]), int(split[1]) + 1):
            await sendPassage(book, str(i), ctx)
            await asyncio.sleep(1.5)
    else:
        VerseNumber = str(randint(1, bookMax))
        await sendPassage(book, VerseNumber, ctx)


@client.command(name="editClient")
async def editClient(ctx, key="", val=""):
    authorId = str(ctx.message.author.id)
    guildId = str(ctx.message.guild.id)
    if guildId in clientSettings:
        if authorId in clientSettings[guildId]:
            clientSettings[guildId][authorId][key] = val
            embed = discord.Embed(title="Set", description="Set " + key + " to " + val, color=0x72faf3)
            await ctx.send(embed=embed)
        else:
            clientSettings[guildId][authorId] = {}
            embed = discord.Embed(title="Error",
                                  description="Client Id not in settings, it has been set, retry command",
                                  color=0xff0000)
            await ctx.send(embed=embed)
    else:
        clientSettings[guildId] = {}
        embed = discord.Embed(title="Error", description="Guild Id not in settings, it has been set, retry command",
                              color=0xff0000)
        await ctx.send(embed=embed)
    setData(json.dumps(clientSettings))


@client.command(name="editGuild")
async def editGuild(ctx, key="", val=""):
    authorId = str(ctx.message.author.id)
    guildId = str(ctx.message.guild.id)
    if guildId in clientSettings:
        if "guildSettings" in clientSettings[guildId]:
            clientSettings[guildId]["guildSettings"][key] = val
            embed = discord.Embed(title="Set", description="Set " + key + " to " + val, color=0x72faf3)
            await ctx.send(embed=embed)
        else:
            clientSettings[guildId]["guildSettings"] = {}
            embed = discord.Embed(title="Error",
                                  description="Guild Settings not in settings, it has been set, retry command",
                                  color=0xff0000)
            await ctx.send(embed=embed)
    else:
        clientSettings[guildId] = {}
        embed = discord.Embed(title="Error", description="Guild Id not in settings, it has been set, retry command",
                              color=0xff0000)
        await ctx.send(embed=embed)
    setData(json.dumps(clientSettings))


@client.command(name="clearAllData")
async def clearAllData(ctx):
    setData("{}")
    clientSettings = {}
    await ctx.send("Cleared all data")


@client.command(name="getClientData")
async def getClientData(ctx):
    authorId = str(ctx.message.author.id)
    guildId = str(ctx.message.guild.id)
    if guildId in clientSettings:
        if authorId in clientSettings[guildId]:
            authorSettings = clientSettings[guildId].get(authorId)
            await ctx.send(json.dumps(authorSettings))
        else:
            await ctx.send("No Data")
    else:
        await ctx.send("No Data")


@client.command(name="getGuildData")
async def getGuildData(ctx):
    guildId = str(ctx.message.guild.id)
    if guildId in clientSettings and "guildSettings" in clientSettings[guildId]:
        guildSettings = clientSettings[guildId].get("guildSettings")
        await ctx.send(json.dumps(guildSettings))
    else:
        await ctx.send("No Data")


@client.command(name="getAllGuildData")
async def getAllData(ctx):
    guildId = str(ctx.message.guild.id)
    if guildId in clientSettings:
        guildSettings = clientSettings.get(guildId)
        await ctx.send(json.dumps(guildSettings))
    else:
        await ctx.send("No Data")


client.remove_command('help')


@client.command(name="help", aliases=["cmds", "commands"])
async def help(ctx):
    embed = discord.Embed(title="**Help**",
                          description="getChapter\n\nUsage:\n\nt!getChapter 1 -> Gets Chapter 1 from the Dào dé jīng "
                                      "in English\nt!getChapter 1 tao_te_cheng_cn Gets Chapter 1 from the Dào dé jīng "
                                      "in Chinese\nt!getChapter 1-4 Gets Chapter 1-4 from the Dào dé jīng in "
                                      "English\nt!getChapter 1-4 tao_te_cheng_cn Gets Chapter 1-4 from the Dào dé "
                                      "jīng in Chinese\nt!getChapter random Gets a random chapter from the Dào dé jīng "
                                      "in English\nt!getChapter random tao_te_cheng_cn Gets a random chapter from the "
                                      "Dào dé jīng in English\nt!getChapter 1 zuang_zi Gets Chapter 1 from the Zuang "
                                      "Zi in English\nt!getChapter 1-4 zuang_zi Gets Chapter 1-4 from the Zuang Zi in "
                                      "English\nt!getChapter random zuang_zi Gets a random chapter from the Zuang Zi "
                                      "in English"
                                      "\n\neditClient\n\nUsage:\n\nt!editClient defaultBookFormat zuang_zi -> Sets "
                                      "defaultBookFormat key for zuang_zi value"
                                      "\n\neditGuild\n\nUsage:\n\nt!editServer announce true -> Sets "
                                      "announce key for true value",
                          color=0x72faf3)
    await ctx.send(embed=embed)


client.run("tokenhere!!!")
