import aiohttp

# enable text coloring only if the requirements are met
coloring = False


# ----------------Alt Indexing------------
doAltIndexing = True


def addPretext(lines, icon, baseURL, subURL):
    modified_lines = []
    currMdSubheading = ""
    currSubCat = ""
    currSubSubCat = ""

    for line in lines:
        if line.startswith("#"):  # Title Lines
            if not subURL == "storage":
                if line.startswith("# ►"):
                    currMdSubheading = (
                        "#"
                        + line.replace("# ►", "")
                        .strip()
                        .replace(" / ", "--")
                        .replace(" ", "-")
                        .lower()
                    )
                    currSubCat = "/ " + line.replace("# ►", "").strip() + " "
                    currSubSubCat = ""
                elif line.startswith("## ▷"):
                    if (
                        not subURL == "non-english"
                    ):  # Because non-eng section has multiple subsubcats with same names
                        currMdSubheading = (
                            "#"
                            + line.replace("## ▷", "")
                            .strip()
                            .replace(" / ", "--")
                            .replace(" ", "-")
                            .lower()
                        )
                    currSubSubCat = "/ " + line.replace("## ▷", "").strip() + " "
            elif subURL == "storage":
                if line.startswith("## "):
                    currMdSubheading = (
                        "#"
                        + line.replace("## ", "")
                        .strip()
                        .replace(" / ", "--")
                        .replace(" ", "-")
                        .lower()
                    )
                    currSubCat = "/ " + line.replace("## ", "").strip() + " "
                    currSubSubCat = ""
                elif line.startswith("### "):
                    currMdSubheading = (
                        "#"
                        + line.replace("### ", "")
                        .strip()
                        .replace(" / ", "--")
                        .replace(" ", "-")
                        .lower()
                    )
                    currSubSubCat = "/ " + line.replace("### ", "").strip() + " "

            # Remove links from subcategory titles (because the screw the format)
            if "http" in currSubCat:
                currSubCat = ""
            if "http" in currSubSubCat:
                currSubSubCat = ""

        elif any(char.isalpha() for char in line):  # If line has content
            preText = f"[{icon}{currSubCat}{currSubSubCat}]({baseURL}{subURL}{currMdSubheading}) ► "
            if line.startswith("* "):
                line = line[2:]
            modified_lines.append(preText + line)

    return modified_lines


async def dlWikiChunk(fileName, icon, redditSubURL):
    pagesDevSiteSubURL = fileName.replace(".md", "").lower()
    subURL = pagesDevSiteSubURL
    # print("Local file not found. Downloading " + fileName + "from Github...")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://raw.githubusercontent.com/nbats/FMHYedit/main/" + fileName
        ) as response:
            t = await response.text()
            lines = t.split("\n")
    # print("Downloaded")

    # add a pretext
    redditBaseURL = "https://www.reddit.com/r/FREEMEDIAHECKYEAH/wiki/"
    pagesDevSiteBaseURL = "https://fmhy.pages.dev/"
    baseURL = pagesDevSiteBaseURL
    lines = addPretext(lines, icon, baseURL, subURL)

    return lines


def cleanLineForSearchMatchChecks(line):
    return line.replace("https://www.reddit.com/r/FREEMEDIAHECKYEAH/wiki/", "/").replace(
        "https://fmhy.pages.dev/", "/"
    )


async def alternativeWikiIndexing():
    wikiChunks = [
        await dlWikiChunk("VideoPiracyGuide.md", "📺", "video"),
        await dlWikiChunk("AI.md", "🤖", "ai"),
        await dlWikiChunk("Android-iOSGuide.md", "📱", "android"),
        await dlWikiChunk("AudioPiracyGuide.md", "🎵", "audio"),
        await dlWikiChunk("DownloadPiracyGuide.md", "💾", "download"),
        await dlWikiChunk("EDUPiracyGuide.md", "🧠", "edu"),
        await dlWikiChunk("GamingPiracyGuide.md", "🎮", "games"),
        await dlWikiChunk("AdblockVPNGuide.md", "📛", "adblock-vpn-privacy"),
        await dlWikiChunk("TOOLSGuide.md", "🔧", "tools-misc"),
        await dlWikiChunk("MISCGuide.md", "📂", "misc"),
        await dlWikiChunk("ReadingPiracyGuide.md", "📗", "reading"),
        await dlWikiChunk("TorrentPiracyGuide.md", "🌀", "torrent"),
        await dlWikiChunk("img-tools.md", "📷", "img-tools"),
        await dlWikiChunk("LinuxGuide.md", "🐧🍏", "linux"),
        await dlWikiChunk("DEVTools.md", "🖥️", "dev-tools"),
        await dlWikiChunk("Non-English.md", "🌏", "non-eng"),
        await dlWikiChunk("STORAGE.md", "🗄️", "storage"),
        await dlWikiChunk(
            "NSFWPiracy.md", "🌶", "https://saidit.net/s/freemediafuckyeah/wiki/index"
        ),
    ]
    return [item for sublist in wikiChunks for item in sublist]


# --------------------------------


async def standardWikiIndexing():
    # print("Local single-page file not found.")
    # If that fails, try to get it from Github
    # print("Loading FMHY single-page file from Github...")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://raw.githubusercontent.com/nbats/FMHYedit/main/single-page"
        ) as response:
            t = await response.text()
            lines = t.split("\n")
            return lines


async def getAllLines():
    if doAltIndexing:
        try:
            lines = await alternativeWikiIndexing()
        except:
            lines = standardWikiIndexing()
    else:
        lines = standardWikiIndexing()
    return lines


def removeEmptyStringsFromList(stringList):
    return [string for string in stringList if string != ""]


def checkMultiWordQueryContainedExactlyInLine(line, searchQuery):
    if len(searchQuery.split(" ")) <= 1:
        return False
    return searchQuery.lower() in line.lower()


def moveExactMatchesToFront(myList, searchQuery):
    bumped = []
    notBumped = []
    for element in myList:
        if checkMultiWordQueryContainedExactlyInLine(element, searchQuery):
            bumped.append(element)
        else:
            notBumped.append(element)
    return bumped + notBumped


def checkList1isInList2(list1, list2):
    for element in list1:
        if element not in list2:
            return False
    return True


def checkWordForWordMatch(line, searchQuery):
    lineWords = removeEmptyStringsFromList(
        line.lower().replace("[", " ").replace("]", " ").split(" ")
    )
    lineWords = [
        element.strip() for element in lineWords
    ]  # doesnt work on streamlit without this line even though it works locally
    searchQueryWords = removeEmptyStringsFromList(searchQuery.lower().split(" "))
    return checkList1isInList2(searchQueryWords, lineWords)


def checkWordForWordMatchCaseSensitive(line, searchQuery):
    lineWords = removeEmptyStringsFromList(line.replace("[", " ").replace("]", " ").split(" "))
    lineWords = [
        element.strip() for element in lineWords
    ]  # doesnt work on streamlit without this line even though it works locally
    searchQueryWords = removeEmptyStringsFromList(searchQuery.split(" "))
    return checkList1isInList2(searchQueryWords, lineWords)


def moveBetterMatchesToFront(myList, searchQuery):
    bumped = []
    notBumped = []
    for element in myList:
        if checkWordForWordMatch(element, searchQuery):
            bumped.append(element)
        else:
            notBumped.append(element)
    return bumped + notBumped


def getOnlyFullWordMatches(myList, searchQuery):
    bumped = []
    for element in myList:
        if checkWordForWordMatch(element, searchQuery):
            bumped.append(element)
    return bumped


def getOnlyFullWordMatchesCaseSensitive(myList, searchQuery):
    bumped = []
    for element in myList:
        if checkWordForWordMatchCaseSensitive(element, searchQuery):
            bumped.append(element)
    return bumped


def getLinesThatContainAllWords(lineList, searchQuery):
    words = removeEmptyStringsFromList(searchQuery.lower().split(" "))
    bumped = []
    for line in lineList:
        if doAltIndexing:
            lineModdedForChecking = cleanLineForSearchMatchChecks(line).lower()
        else:
            lineModdedForChecking = line.lower()
        for word in words:
            if word not in lineModdedForChecking:
                break
        else:
            bumped.append(line)
    return bumped


def filterLines(lineList, searchQuery):
    if len(searchQuery) <= 2 or (searchQuery == searchQuery.upper() and len(searchQuery) <= 5):
        return getOnlyFullWordMatches(lineList, searchQuery)
    else:
        return getLinesThatContainAllWords(lineList, searchQuery)


def filterOutTitleLines(lineList):
    filteredList = []
    sectionTitleList = []
    for line in lineList:
        if line[0] != "#":
            filteredList.append(line)
        else:
            sectionTitleList.append(line)
    return [filteredList, sectionTitleList]

def filterOutNSFW(lineList):
    filteredList = []
    for line in lineList:
        if 'nsfwpiracy' not in line:
            filteredList.append(line)
    return filteredList


def addNumberingToStringList(string_list):
    for i in range(len(string_list)):
        string_list[i] = f"**{i + 1}** - {string_list[i]}"
    return string_list


def doASearch(searchInput, myLineList):
    # intro to the search results
    myFilterWords = removeEmptyStringsFromList(searchInput.lower().split(" "))

    # main results
    linesFoundPrev = filterLines(myLineList, searchInput)

    sfwLines = filterOutNSFW(linesFoundPrev)

    # limit result list
    if len(linesFoundPrev) > 300:
        # print("Too many results (" + str(len(linesFoundPrev)) + "). Showing only full-word matches.")
        linesFoundPrev = getOnlyFullWordMatches(sfwLines, searchInput)

    # rank results
    # linesFoundPrev = moveExactMatchesToFront(linesFoundPrev, searchInput)
    linesFoundPrev = moveBetterMatchesToFront(linesFoundPrev, searchInput)

    # separate title lines
    linesFoundAll = filterOutTitleLines(linesFoundPrev)
    linesFound = linesFoundAll[0]
    linesFound = addNumberingToStringList(sfwLines)
    sectionTitleList = linesFoundAll[1]

    # reverse list for terminal
    # linesFound.reverse()

    # check for coloring
    textToprint = "\n\n".join(linesFound)

    # # print main results

    return [linesFound[:5], sectionTitleList]

    # # print("# printing " + str(len(linesFound)) + " search results:\n")
    # # print(textTo# print)
    # # print("\nSearch ended with " + str(len(linesFound)) + " results found.\n")

    # #title section results
    # if len(sectionTitleList)>0:
    #     # print("Also there are these section titles: ")
    #     # print("\n".join(sectionTitleList))


async def execute(query):
    lineList = await getAllLines()
    return doASearch(query, lineList)
