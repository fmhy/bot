import json
import random

data = json.load(open("data/drama.json"))


def fillPhrase(phrase: str, data: dict):
    phr = phrase.split(" ")
    for i in range(len(phr)):
        for j in data["replacers"].keys():
            if phr[i].startswith(j):
                replacives = data[data["replacers"][j]]
                current_phrase = " ".join(phr)
                to_replace_with = random.choice(replacives)
                if to_replace_with not in current_phrase:
                    phr[i] = phr[i].replace(j, to_replace_with)
                    break
                else:
                    replacives.remove(to_replace_with)
                    phr[i] = phr[i].replace(j, random.choice(replacives))
                    break
    return " ".join(phr)


def getPhrase(data: dict):
    return random.choice(data["phrases"])


def generateRandomPhrase():
    return fillPhrase(getPhrase(data), data)
