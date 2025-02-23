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
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://raw.githubusercontent.com/fmhy/edit/main/docs/" + fileName
        ) as response:
            t = await response.text()
            lines = t.split("\n")

    # add a pretext
    redditBaseURL = "https://www.reddit.com/r/FREEMEDIAHECKYEAH/wiki/"
    pagesDevSiteBaseURL = "https://fmhy.pages.dev/"
    baseURL = pagesDevSiteBaseURL
    lines = addPretext(lines, icon, baseURL, subURL)

    return lines


def cleanLineForSearchMatchChecks(line):
    return line.replace("https://www.reddit.com/r/FREEMEDIAHECKYEAH/wiki/", "/").replace("https://fmhy.pages.dev/", "/")


async def alternativeWikiIndexing():
    wikiChunks = [
        await dlWikiChunk("adblockvpnguide.md", "📛", "adblock-vpn-privacy"),
        await dlWikiChunk("ai.md", "🤖", "ai"),
        await dlWikiChunk("android-iosguide.md", "📱", "android"),
        await dlWikiChunk("audiopiracyguide.md", "🎵", "audio"),
        await dlWikiChunk("devtools.md", "🖥️", "dev-tools"),
        await dlWikiChunk("downloadpiracyguide.md", "💾", "download"),
        await dlWikiChunk("edupiracyguide.md", "🧠", "edu"),
        await dlWikiChunk("file-tools.md", "🗃️", "file-tools"),
        await dlWikiChunk("gaming-tools.md", "🎮", "game-tools"),
        await dlWikiChunk("gamingpiracyguide.md", "🎮", "games"),
        await dlWikiChunk("img-tools.md", "📷", "img-tools"),
        await dlWikiChunk("internet-tools.md", "🔗", "internet-tools"),
        await dlWikiChunk("linuxguide.md", "🐧🍏", "linux"),
        await dlWikiChunk("miscguide.md", "📂", "misc"),
        await dlWikiChunk("non-english.md", "🌏", "non-eng"),
        await dlWikiChunk("readingpiracyguide.md", "📗", "reading"),
        await dlWikiChunk("social-media-tools.md", "💬", "social-media"),
        await dlWikiChunk("storage.md", "🗄️", "storage"),
        await dlWikiChunk("system-tools.md", "💻", "system-tools"),
        await dlWikiChunk("text-tools.md", "📝", "text-tools"),
        await dlWikiChunk("torrentpiracyguide.md", "🌀", "torrent"),
        await dlWikiChunk("video-tools.md", "📼", "video-tools"),
        await dlWikiChunk("videopiracyguide.md", "📺", "video"),
    ]
    return [item for sublist in wikiChunks for item in sublist]


# --------------------------------


async def standardWikiIndexing():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.fmhy.net/single-page") as response:
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
    lineWords = removeEmptyStringsFromList(line.lower().replace("[", " ").replace("]", " ").split(" "))
    lineWords = [element.strip() for element in lineWords]
    searchQueryWords = removeEmptyStringsFromList(searchQuery.lower().split(" "))
    return checkList1isInList2(searchQueryWords, lineWords)


def checkWordForWordMatchCaseSensitive(line, searchQuery):
    lineWords = removeEmptyStringsFromList(line.replace("[", " ").replace("]", " ").split(" "))
    lineWords = [element.strip() for element in lineWords]
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
        if "nsfwpiracy" not in line:
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

    if len(linesFoundPrev) > 300:
        linesFoundPrev = getOnlyFullWordMatches(sfwLines, searchInput)

    # rank results
    linesFoundPrev = moveBetterMatchesToFront(linesFoundPrev, searchInput)

    # separate title lines
    linesFoundAll = filterOutTitleLines(linesFoundPrev)
    linesFound = linesFoundAll[0]
    linesFound = addNumberingToStringList(sfwLines)
    sectionTitleList = linesFoundAll[1]

    # check for coloring
    textToprint = "\n\n".join(linesFound)

    return [linesFound[:5], sectionTitleList]


async def execute(query):
    lineList = await getAllLines()
    return doASearch(query, lineList)
