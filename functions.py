import json as j

def load_config():
    with open("config.json", "r") as file:
        config = file.read()
    file.close()
    return j.loads(config)

def load_relay_info():
    with open("relay_info.json", "r") as file:
        keywords = file.read()
    file.close()
    keywords = j.loads(keywords)["keywords"]

    keywords_list = []
    keywords_to_channels_dict = {}
    channels_list = []

    for keyword in keywords:
        keywords_list.append(keyword["keyword"])
        keywords_to_channels_dict[keyword["keyword"]] = keyword["channel_ids"]
        channels_list += keyword["channel_ids"]

    return keywords_list, keywords_to_channels_dict, set(channels_list)

def save_relay_info(info):
    to_save = {"keywords": []}
    for key in info:
        to_save["keywords"].append({"keyword": key, "channel_ids": info[key]})
    
    with open("relay_info.json", "w") as file:
        j.dump(to_save, file)
        file.close()