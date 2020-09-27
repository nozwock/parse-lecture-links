import sys, os, re, csv
dir=lambda e: os.path.dirname(e)
sys.path.append(dir(dir(os.path.abspath(__file__))))
from tools.data_scraping import YoutubeTitle
from lib.whatsChat import chat


ChatFilePath="./WhatsApp Chat with Dropper 2021.txt"
CachePath="./cache.csv"

try:
    parsedData=chat(ChatFilePath).get()
except:
    os.system('termux-toast -s -b white -c black Error -1')
    exit(-1)

cache_exists=os.path.isfile(CachePath)
if cache_exists:
    with open(CachePath, newline='') as f:
        Cache=list(csv.reader(f))
else: 
    Cache=None

recLectureData=[]
#Regex to match zoom links
recSearch=lambda x: re.search('https\:\/\/us\d{2}web\.zoom\.us\/rec',x)
#Regex to match youtube links
ytbSearch=lambda x: re.search('https\:\/\/youtu.be|https\:\/\/www.youtube',x)
descCheck=lambda s,x: re.search(f'({s})',x,re.I)

#Parsing chat to get <links>, their <description>, & <date>
for i, j in enumerate(parsedData):
    dataBuffer=[]
    if recSearch(j[-1]):
        #! Zoom links section
        #Regex to get the zoom rec link from text
        lnk=re.search('(((https\:\/\/us\d{2}web\.zoom\.us\/rec)(.*)(startTime=[\d]+))'
        '|((https\:\/\/us\d{2}web\.zoom\.us\/rec\/share\/)([^\s]+)))',j[-1]).group(1)
        #Appending link
        dataBuffer.append(lnk)
        #For description
        try:
            if (not recSearch(parsedData[i+1][-1]) and 
                (descCheck('lecture',parsedData[i+1][-1]) or 
                descCheck('dropper',parsedData[i+1][-1]))):
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
                        if (descCheck('lecture',parsedData[(i+1)+k][-1]) or 
                           descCheck('dropper',parsedData[(i+1)+k][-1])):
                            find=1
                            break
                    #Appending description if found
                    if find: dataBuffer.append(parsedData[(i+1)+k][-1])
                    else:
                        #If not found even after that, then using a generic description
                        share_code=re.search('\/share\/([^\s]+)(([\?])|.)',parsedData[i+1][-1]).group(1)
                        dataBuffer.append(f'Unknown Title (link_code): {share_code[:12]}...')
                        del share_code
                else:
                    #For link not starting at 0 index, i.e. there's some text before it
                    #So, we'll use that text as our description
                    trim=re.search('Start Time \:.*',j[-1].replace(lnk,'').strip(),re.I)
                    if trim:
                        dataBuffer.append(j[-1].replace(lnk,'').strip().replace(trim.group(0),'').strip())
                    else:
                        dataBuffer.append(j[-1].replace(lnk,'').strip())
        except: 
            #most likely IndexError for 'i+1' while checking for next line
            #i.e. next line does not exist, so use the text as description
            trim=re.search('Start Time \:.*',j[-1].replace(lnk,'').strip(),re.I)
            if trim:
                dataBuffer.append(j[-1].replace(lnk,'').strip().replace(trim.group(0),'').strip())
            else:
                dataBuffer.append(j[-1].replace(lnk,'').strip())
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
                os.system('termux-toast -s -b white -c black Error 404')
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
    recLectureData.append(dataBuffer)

ExpFileName='tmp.md'
with open(ExpFileName,'w+') as f:
    f.write('####Recent ↑\n')
    for i, j in enumerate(recLectureData[::-1]):
        #Check if not last index
        pos=((len(recLectureData)-1)!=i)
        f.write(f'**`{j[2]}`**\n')
        f.write(f'> [{j[1]}]({j[0]})')
        if pos: f.write('\n\n')
          
#Copy to clipboard
os.system('termux-clipboard-set < %s'%(ExpFileName))
#Clean up
os.remove(ChatFilePath)
os.remove(ExpFileName)
#Verbose message
os.system('termux-toast -s -b white -c black Copied to clipboard!')
#Open link to edit with new data
os.system('termux-open-url https://rentry.co/jksdropperlectures/edit')