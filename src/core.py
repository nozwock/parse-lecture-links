#! Script made for a specific use case
import sys, os, re, csv
dir=lambda e: os.path.dirname(e)
sys.path.append(dir(dir(os.path.abspath(__file__))))
from tools.data_scraping import YoutubeTitle
from lib.whatsChat import ChatParser
from argparse import ArgumentParser
from subprocess import getoutput
from platform import system
from shutil import which


parser=ArgumentParser()
parser.add_argument('-d','--dir',nargs='?',required=True)
args=parser.parse_args()

ChatFilePath=args.dir
CachePath="./cache.csv"

cmdExists=lambda cmd: which(cmd) is not None
isTermux=False
if system().lower()=="linux":
    isTermux=getoutput("echo $PREFIX | grep 'com.termux'").strip() != ''

if os.path.isfile(ChatFilePath):
    parsedData=ChatParser(ChatFilePath).get
    #Date, Time, Author, Message
else:
    if cmdExists('termux-toast'):
        os.system('termux-toast -s -b white -c black Error FileNotFound')
    exit(-1)

cache_exists=os.path.isfile(CachePath)
Cache=None
if cache_exists:
    with open(CachePath, newline='') as f:
        Cache=list(csv.reader(f))

recLectureData=[]
#Regex to match zoom links
recSearch=lambda x: re.search('https\:\/\/us\d{2}web\.zoom\.us\/rec',x)
#Regex to match youtube links
ytbSearch=lambda x: re.search('https\:\/\/youtu.be|https\:\/\/www.youtube',x)
descCheck=lambda s,x: re.search(f'({s})',x,re.I)

KeyList=['dropper','lecture']
assert (isinstance(KeyList,(list,str))),('Invalid Keywords!')
#Statement to check if atleast one keyword from KeyList is present or not
KeyExists=lambda e:"("+" or ".join(
    ["descCheck('%s',parsedData[%s][-1])"%(i,e) for i in KeyList])+")"

#Parsing chat to get [<links>, <description>, <date>, Optional[<access_code>]]
for i, j in enumerate(parsedData):
    dataBuffer=[]
    if recSearch(j[-1]):
        #! Zoom links section
        #Regex to get the zoom rec link from text
        lnk=re.search(
            '(((https\:\/\/us\d{2}web\.zoom\.us\/rec)(.*)(startTime=[\d]+))'
            '|((https\:\/\/us\d{2}web\.zoom\.us\/rec\/share\/)([^\s]+)))',j[-1]).group(1)
        #Appending link
        dataBuffer.append(lnk)
        #For description
        try:
            if (not recSearch(parsedData[i+1][-1]) and eval(KeyExists('i+1'))):
                #i.e. description is in the next line
                #Appending description
                dataBuffer.append(parsedData[i+1][-1])
            else:
                #i.e. description is not in the next line
                if recSearch(j[-1]).start()==0:
                    #For the link starting at 0 index
                    find=0
                    for k in range(1,4+1):
                        #Trying to find description of the link for upto 4 trials
                        if eval(KeyExists('(i+1)+k')):
                            find=1
                            break
                    #Appending description if found
                    if find: dataBuffer.append(parsedData[(i+1)+k][-1])
                    else:
                        #If not found even after that, then using a generic description
                        share_code=re.search(
                            '\/share\/([^\s]+)(([\?])|.)',parsedData[i+1][-1]).group(1)
                        dataBuffer.append(
                            f'Unknown Title (link_code): {share_code[:12]}...')
                        del share_code
                else:
                    #For link not starting at 0 index, i.e. there's some text before it
                    #So, we'll use that text as our description
                    #trim=re.search(
                    #    'Start Time \:.*',j[-1].replace(lnk,'').strip(),re.I)
                    desc_pattern = r"(?P<time>Start Time \:.+?(AM)|(PM)).+(?P<meet>Meeting Recording\:).+"
                    desc_code = r"(?P<code>Access Passcode\:\s+\S+)"
                    trim = re.search(desc_pattern+desc_code,j[-1],re.I)
                    if trim:
                        #Access code is present
                        dataBuffer.append(
                            (j[-1].replace(trim.group(),'')+trim.group('code')).strip())
                    else:
                        # No Access code found
                        trim = re.search(desc_pattern,j[-1],re.I)
                        if trim:
                            dataBuffer.append(
                                j[-1].replace(trim.group(),'').strip())
                        else:
                            # Not much stuff found, removing link from desc
                            dataBuffer.append(
                                j[-1].replace(lnk,'').strip())
        except IndexError: 
            #most likely IndexError for 'i+1' while checking for next line
            #i.e. next line does not exist, so use the text as description
            desc_pattern = r"(?P<time>Start Time \:.+?(AM)|(PM)).+(?P<meet>Meeting Recording\:).+"
            desc_code = r"(?P<code>Access Passcode\:\s+\S+)"
            trim = re.search(desc_pattern+desc_code,j[-1],re.I)
            if trim:
                dataBuffer.append(
                    (j[-1].replace(trim.group(),'')+trim.group('code')).strip())
            else:
                trim = re.search(desc_pattern,j[-1],re.I)
                if trim:
                    dataBuffer.append(
                        j[-1].replace(trim.group(),'').strip())
                else:
                    dataBuffer.append(
                        j[-1].replace(lnk,'').strip())
    elif ytbSearch(j[-1]):
        #! Youtube links section
        #Regex for type1 links
        #https://youtu.be/<id>
        ytbType1=re.search('https\:\/\/youtu.be\/',j[-1])
        #Regex for id of type2 links
        #https://www.youtube.com/...?v=<id>&...
        id2_get=re.search('\/v\/(.+?(?=\?))|\?v=(.+?(?=\&))',j[-1])
        find=0
        if cache_exists:
            for x, data in enumerate(Cache):
                if j[-1]==data[0]:
                    find=1
                    break
        if find:
            dataBuffer+=Cache[x]
        else:
            #Cache not available
            #Appending link
            dataBuffer.append(j[-1])
            #Getting id of Youtube link
            if ytbType1:
                #Type1 link
                id=j[-1].replace(ytbType1.group(),'').strip()
            else:
                #Type2 link
                if id2_get.group(1):
                    id=id2_get.group(1)
                else:
                    id=id2_get.group(2)
            #Appending description
            try:
                dataBuffer.append(YotubeTitle(id))
            except Exception as e:
                print(repr(e))
                if cmdExists('termux-toast'):
                    os.system(
                        'termux-toast -s -b white -c black Connection Error')
                continue
            #Generating cache
            with open(CachePath,'a+') as f:
                csv.writer(f).writerows([dataBuffer])
    else:
        #! is not a link, i.e. just skip
        continue
    #Swapping dates and months position
    dt=j[0].split('/')
    dt[0],dt[1]=dt[1],dt[0]
    #Appending date
    dataBuffer.append('/'.join(dt))
    access_code = re.search(r"(?P<code>Access Passcode\:\s+\S+)",dataBuffer[1],re.I)
    if access_code:
        dataBuffer[1]=dataBuffer[1].replace(access_code.group('code'),"").strip()
        #Appending access_code
        dataBuffer.append(access_code.group('code'))
    else:
        dataBuffer.append(None)
    recLectureData.append(dataBuffer)# [<link>,<desc>,<date>,Optional[<access_code>]]

ExpFileName='export.md'
with open(ExpFileName,'w+') as f:
    f.write('####Recent ↑\n')
    for i, j in enumerate(recLectureData[::-1]):
        #Check if not last index
        pos=((len(recLectureData)-1)!=i)
        f.write(f'**`{j[2]}`**\n')
        f.write(f'> [{j[1]}]({j[0]})')
        if j[3]: f.write(f'\n> `{j[3]}`')
        if pos: f.write('\n\n')

if isTermux:
    #Copy to clipboard
    os.system('termux-clipboard-set < %s'%(ExpFileName))
    #Clean up
    os.remove(ExpFileName)
    #Verbose message
    os.system(
        'termux-toast -s -b white -c black Copied to clipboard!')
    #Open link to edit with new data
    os.system('termux-open-url %s'%getoutput('cat ~/.link'))
os.remove(ChatFilePath)