class Parrot():
    def __init__(self, parrotInfo):
        self.keywords = []
        for set_ in parrotInfo:
            self.keywords.append(Keyword(set_["positive"], set_["negative"], set_["channelsToSendTo"]))

    def get_channels_to_send_to(self, message):
        channels = []
        for keyword in self.keywords:
            channels += keyword.find_channels(message)

        return set(channels)
    
    def get_all_channels(self):
        channelIDs = []

        for keyword in self.keywords:
            channelIDs += keyword.channelsToSendTo

        return channelIDs

    def remove_channel_from_keyword(self, channelID):
        toRemove = []
        for keyword in self.keywords:
            try:
                keyword.channelsToSendTo.remove(int(channelID))
            except:
                pass

            if len(keyword.channelsToSendTo) < 1:
                toRemove.append(keyword)

        for keyword in toRemove:
            self.keywords.remove(keyword)


class Keyword():
    def __init__(self, positiveKeywords, negativeKeywords, channelsToSendTo):
        self.positiveKeywords = positiveKeywords
        self.negativeKeywords = negativeKeywords
        self.channelsToSendTo = channelsToSendTo

    def find_channels(self, message):
        for negativeKeyword in self.negativeKeywords:
            if negativeKeyword in message:
                return []
        
        for positiveKeyword in self.positiveKeywords:
            if positiveKeyword in message:
                return self.channelsToSendTo
        
        return []