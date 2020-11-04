#! Script made for a specific use case
import sys, os, re, csv
from .tools.data_scraping import YoutubeTitle
from .lib.whatsChat import ChatParser
from argparse import ArgumentParser
from subprocess import getoutput
from platform import system
from shutil import which
from pathlib import Path
from datetime import datetime


parser = ArgumentParser(
    description="parse-lecture-links: scrape lecture links from whatsapp chat file"
)
parser.add_argument(
    "path",
    help="parses [FILE] to get lecture links eg.'WhatsApp Chat with xxx.txt'",
    nargs=1,
    type=str,
    metavar="FILE",
)
parser.add_argument(
    "-o",
    "--output",
    help="write output to [FILE]",
    nargs="?",
    type=str,
    required=False,
    default=Path("output.md"),
    metavar="FILE",
)
parser.add_argument(
    "-l",
    "--link",
    help="open [URL] at exit",
    nargs="?",
    type=str,
    required=False,
    metavar="URL",
)
parser.add_argument(
    "--copy-output",
    help="copy output to clipboard",
    action="store_true",
    required=False,
)
parser.add_argument(
    "--clear",
    help="remove output file and chat file at exit",
    action="store_true",
    required=False,
)
args = parser.parse_args()

output_choices = {"md": ".md", "csv": ".csv", "txt": ".txt"}
# Output path check
output_path = Path(args.output).resolve()
if not output_path.parent.is_dir() or output_path.suffix == "":
    print("error: Enter valid path for output file")
    exit(-1)
if output_path.suffix not in list(output_choices.values()):
    print("error: Supported file formats are {}".format(list(output_choices.values())))
    exit(-1)

data_dir = Path(__file__).resolve().parent.parent.joinpath("data")
if not data_dir.is_dir():
    data_dir.mkdir()

ChatFilePath = Path(args.path[0])
CachePath = data_dir.joinpath("cache.csv")

cmdExists = lambda cmd: which(cmd) is not None
isTermux = False
if system().lower() == "linux":
    isTermux = getoutput("echo $PREFIX | grep 'com.termux'").strip() != ""

if ChatFilePath.is_file():
    parsedData = ChatParser(ChatFilePath).get
    # Date, Time, Author, Message
else:
    if cmdExists("termux-toast"):
        os.system("termux-toast -s -b white -c black error: File not found")
    print("error: File not found")
    exit(-1)

cache_exists = CachePath.is_file()
Cache = None
if cache_exists:
    with open(CachePath, newline="") as f:
        Cache = list(csv.reader(f))

recLectureData = []
# Regex to match zoom links
recSearch = lambda x: re.search("https\:\/\/us\d{2}web\.zoom\.us\/rec", x)
# Regex to match youtube links
ytbSearch = lambda x: re.search("https\:\/\/youtu.be|https\:\/\/www.youtube", x)
descCheck = lambda s, x: re.search(f"({s})", x, re.I)

KeyList = ["dropper", "lecture"]
assert isinstance(KeyList, (list, str)), "Invalid Keywords!"
# Statement to check if atleast one keyword from KeyList is present or not
KeyExists = (
    lambda e: "("
    + " or ".join(["descCheck('%s',parsedData[%s][-1])" % (i, e) for i in KeyList])
    + ")"
)

# Parsing chat to get [<links>, <description>, <date>, Optional[<access_code>]]
for i, j in enumerate(parsedData):
    dataBuffer = []
    if recSearch(j[-1]):
        #! Zoom links section
        # Regex to get the zoom rec link from text

        # lnk = re.search(
        #    "(((https\:\/\/us\d{2}web\.zoom\.us\/rec)(.*)(startTime=[\d]+))"
        #    "|((https\:\/\/us\d{2}web\.zoom\.us\/rec\/share\/)([^\s]+)))",
        #    j[-1],
        # ).group(1)
        lnk = re.search(
            "https\:\/\/us\d{2}web\.zoom\.us\/rec\/share\/\S+startTime=[\d]+"
            "|https\:\/\/us\d{2}web\.zoom\.us\/rec\/share\/\S+",
            j[-1],
        ).group()
        # Appending link
        dataBuffer.append(lnk)
        # For description
        try:
            if not recSearch(parsedData[i + 1][-1]) and eval(KeyExists("i+1")):
                # i.e. description is in the next line
                # Appending description
                dataBuffer.append(parsedData[i + 1][-1])
            else:
                # i.e. description is not in the next line
                if recSearch(j[-1]).start() == 0:
                    # For the link starting at 0 index
                    find = 0
                    for k in range(1, 4 + 1):
                        # Trying to find description of the link for upto 4 trials
                        if eval(KeyExists("(i+1)+k")):
                            find = 1
                            break
                    # Appending description if found
                    if find:
                        dataBuffer.append(parsedData[(i + 1) + k][-1])
                    else:
                        # If not found even after that, then using a generic description
                        # share_code = re.search(
                        #    "\/share\/([^\s]+)(([\?])|.)", parsedData[i + 1][-1]
                        # ).group(1)
                        share_code = re.search(
                            "(?<=\/share\/)\S+(?=\?)|(?<=\/share\/)\S+",
                            parsedData[i + 1][-1],
                        ).group()
                        dataBuffer.append(
                            f"Unknown Title (link_code): {share_code[:12]}..."
                        )
                        del share_code
                else:
                    # For link not starting at 0 index, i.e. there's some text before it
                    # So, we'll use that text as our description
                    # trim=re.search(
                    #    'Start Time \:.*',j[-1].replace(lnk,'').strip(),re.I)
                    desc_pattern = (
                        r"(?P<time>Start Time \:.+?(AM|PM)).+"
                        "(?P<meet>Meeting Recording\:).+"
                    )
                    desc_code = r"(?P<code>Access Passcode\:\s+\S+)"
                    trim = re.search(desc_pattern + desc_code, j[-1], re.I)
                    if trim:
                        # Access code is present
                        dataBuffer.append(
                            (
                                j[-1].replace(trim.group(), "") + trim.group("code")
                            ).strip()
                        )
                    else:
                        # No Access code found
                        trim = re.search(desc_pattern, j[-1], re.I)
                        if trim:
                            dataBuffer.append(j[-1].replace(trim.group(), "").strip())
                        else:
                            # Not much stuff found, removing link from desc
                            dataBuffer.append(j[-1].replace(lnk, "").strip())
        except IndexError:
            # most likely IndexError for 'i+1' while checking for next line
            # i.e. next line does not exist, so use the text as description
            desc_pattern = (
                r"(?P<time>Start Time \:.+?(AM|PM)).+(?P<meet>Meeting Recording\:).+"
            )
            desc_code = r"(?P<code>Access Passcode\:\s+\S+)"
            trim = re.search(desc_pattern + desc_code, j[-1], re.I)
            if trim:
                dataBuffer.append(
                    (j[-1].replace(trim.group(), "") + trim.group("code")).strip()
                )
            else:
                trim = re.search(desc_pattern, j[-1], re.I)
                if trim:
                    dataBuffer.append(j[-1].replace(trim.group(), "").strip())
                else:
                    dataBuffer.append(j[-1].replace(lnk, "").strip())
    elif ytbSearch(j[-1]):
        #! Youtube links section
        # Regex for id type1 links
        # https://youtu.be/<id>
        id1_get = re.search("(?<=https\:\/\/youtu.be\/)\S+", j[-1])
        # Regex for id of type2 links
        # https://www.youtube.com/...?v=<id>&...
        id2_get = re.search("\/v\/(.+?(?=\?))|\?v=(.+?(?=\&))", j[-1])
        find = 0
        if cache_exists:
            for x, data in enumerate(Cache):
                if j[-1] == data[0]:
                    find = 1
                    break
        if find:
            dataBuffer += Cache[x]
        else:
            # Cache not available
            # Appending link
            dataBuffer.append(j[-1])
            # Getting id of Youtube link
            if id1_get:
                # Type1 link
                id = id1_get.group().strip()
            else:
                # Type2 link
                id2_get = [i for i in id2_get.groups() if i is not None][0]
                id = id2_get
            # Appending description
            try:
                dataBuffer.append(YoutubeTitle(id))
            except Exception as e:
                print(repr(e))
                if cmdExists("termux-toast"):
                    os.system("termux-toast -s -b white -c black Connection Error")
                continue
            # Generating cache
            with open(CachePath, "a+") as f:
                csv.writer(f).writerows([dataBuffer])
    else:
        #! is not a link, i.e. just skip
        continue
    # Swapping dates and months position
    dt = j[0].split("/")
    dt[2] = "20{}".format(dt[2])
    dt = datetime.strptime("-".join(dt), "%m-%d-%Y")
    dt = dt.strftime("%d %b %Y")
    # Appending date
    dataBuffer.append(dt)
    access_code = re.search(r"(?P<code>Access Passcode\:\s+\S+)", dataBuffer[1], re.I)
    if access_code:
        dataBuffer[1] = dataBuffer[1].replace(access_code.group("code"), "").strip()
        # Appending access_code
        dataBuffer.append(access_code.group("code"))
    else:
        dataBuffer.append(None)
    recLectureData.append(dataBuffer)  # [<link>,<desc>,<date>,Optional[<access_code>]]

with args.output.open("w+") as f:
    if args.output.suffix == output_choices["md"]:
        f.write("### Recent ↑\n")
        for i, j in enumerate(recLectureData[::-1]):
            # Check if not last index
            pos = (len(recLectureData) - 1) != i
            f.write(f"**`{j[2]}`**\n")
            f.write(f"> [{j[1]}]({j[0]})")
            if j[3]:
                f.write(f"\n> `{j[3]}`")
            if pos:
                f.write("\n\n")
    else:
        raise NotImplementedError

if isTermux:
    # Copy to clipboard
    if args.copy_output:
        os.system("termux-clipboard-set < %s" % (str(args.output.resolve())))
        # Verbose message
        os.system("termux-toast -s -b white -c black Copied to clipboard!")
    # Clean up
    if args.clear:
        args.output.unlink()
        ChatFilePath.unlink()
    if args.link:
        # Open link to edit with new datab
        os.system("termux-open-url %s" % args.link)
