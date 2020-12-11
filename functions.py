import json as j
from classes import Parrot

def load_config():
    with open("config.json", "r") as file:
        config = file.read()
    file.close()
    return j.loads(config)

def load_relay_info():
    with open("relay_info.json", "r") as file:
        keywords = file.read()
    file.close()
    channels = j.loads(keywords)["channels"]

    channelsToParrot = {}
    for channel in channels:
        newParrot = Parrot(channels[channel]["keywords"])
        channelsToParrot[channel] = newParrot

    return channelsToParrot

def save_relay_info(info):
    channelIDToParrot = {}

    for key in info:
        parrotObj = info[key]
        keywordsList = []
        for keyword in parrotObj.keywords:
            keywordsList.append({
                "positive": keyword.positiveKeywords,
                "negative": keyword.negativeKeywords,
                "channelsToSendTo": keyword.channelsToSendTo
            })
        keywordsDict = {"keywords": keywordsList}
        channelIDToParrot[key] = keywordsDict
    toSave = {"channels": channelIDToParrot}

    with open("relay_info.json", "w") as file:
        j.dump(toSave, file)
        file.close()