from whatsChat import chat
import re
import os
import csv
import urllib.request
import json
import urllib

#change to yours VideoID or change url inparams
def ytbTitle(id):
    VideoID = id 
    params = {"format": "json", "url": "https://www.youtube.com/watch?v=%s" % VideoID}
    url = "https://www.youtube.com/oembed"
    query_string = urllib.parse.urlencode(params)
    url = url + "?" + query_string

    with urllib.request.urlopen(url) as response:
        response_text = response.read()
        data = json.loads(response_text.decode())
        return data['title']

#parsing recorded lectures links
ch_path="./WhatsApp Chat with Dropper 2021.txt"
cache_path="./cache.csv"
cache_exists=os.path.isfile(cache_path)

if cache_exists:
    with open(cache_path, newline='') as f:
        Cache=list(csv.reader(f))
else: 
    Cache=None

try:
    parsedData=chat(ch_path).get()
except:
    os.system('termux-toast -s -b white -c black Error -1')
    exit(-1)

recLectureData=[]
recSearch=lambda x: re.search('https\:\/\/us\d{2}web\.zoom\.us\/rec',x)
ytbSearch=lambda x: re.search('https\:\/\/youtu.be|https\:\/\/www.youtube',x)
desc_chk=lambda s,x: re.search(f'({s})',x,re.I)

#data refining to get links, their description, & date
for i, j in enumerate(parsedData):
    dataBuffer=[]
    if recSearch(j[-1]):
        lnk=re.search('(((https\:\/\/us\d{2}web\.zoom\.us\/rec)(.*)(startTime=[\d]+))'
        '|((https\:\/\/us\d{2}web\.zoom\.us\/rec\/share\/)([^\s]+)))',j[-1]).group(1)
        dataBuffer.append(lnk)
        #link
        try:
            if (not recSearch(parsedData[i+1][-1]) and 
                (desc_chk('lecture',parsedData[i+1][-1]) or 
                desc_chk('dropper',parsedData[i+1][-1]))):
                #desc is in the next line
                dataBuffer.append(parsedData[i+1][-1])
            else:
                #desc is not in the next line
                if recSearch(j[-1]).start()==0:
                    #link starts at 0 index
                    find=0
                    for k in range(1,4+1):
                        #checking for description for the link for upto 4 next messages
                        if (desc_chk('lecture',parsedData[(i+1)+k][-1]) or 
                           desc_chk('dropper',parsedData[(i+1)+k][-1])):
                            find=1
                            break
                    if find: dataBuffer.append(parsedData[(i+1)+k][-1])
                    else:
                        share_code=re.search('\/share\/([^\s]+)(([\?])|.)',parsedData[i+1][-1]).group(1)
                        dataBuffer.append(f'Unknown Title (link_code): {share_code[:12]}...')
                        del share_code
                else:
                    #link does not start at 0 index i.e. there's some text before it
                    #we'll use that text as desc
                    trim=re.search('Start Time \:.*',j[-1].replace(lnk,'').strip(),re.I)
                    if trim:
                        dataBuffer.append(j[-1].replace(lnk,'').strip().replace(trim.group(0),'').strip())
                    else:
                        dataBuffer.append(j[-1].replace(lnk,'').strip())
        except: 
            trim=re.search('Start Time \:.*',j[-1].replace(lnk,'').strip(),re.I)
            if trim:
                dataBuffer.append(j[-1].replace(lnk,'').strip().replace(trim.group(0),'').strip())
            else:
                dataBuffer.append(j[-1].replace(lnk,'').strip())
        #description of the link
    elif ytbSearch(j[-1]):
        #for youtube link
        #type1 link
        ytbType=re.search('https\:\/\/youtu.be\/',j[-1])
        #id for type2 link
        id2_get=re.search('\/v\/(.+?(?=\?))|\?v=(.+?(?=\&))',j[-1])
        found=0
        if cache_exists:
            for x, data in enumerate(Cache):
                if j[-1]==data[0]:
                    found=1
                    break
        if found:
            dataBuffer+=Cache[x]
        else:
            #cache not available
            #link
            dataBuffer.append(j[-1])
            #id
            if ytbType:
                id=j[-1].replace(ytbType.group(),'').strip()
            else:
                if id2_get.group(1):
                    id=id2_get.group(1)
                else:
                    id=id2_get.group(2)
            #description
            try:
                dataBuffer.append(ytbTitle(id))
            except Exception as e:
                print(repr(e))
                os.system('termux-toast -s -b white -c black Error 404')
                continue
            #creating cache
            with open(cache_path,'a+') as f:
                csv.writer(f).writerows([dataBuffer])
    else:
        continue
    dt=j[0].split('/')
    dt[0],dt[1]=dt[1],dt[0]
    # swapping dates and months position
    dataBuffer.append('/'.join(dt))
    #date
    recLectureData.append(dataBuffer)

cpName='tmp.md'
with open(cpName,'w+') as f:
    f.write('####Recent ↑\n')
    for i, j in enumerate(recLectureData[::-1]):
        pos=((len(recLectureData)-1)!=i)
        #check if not last index
        f.write(f'**`{j[2]}`**\n')
        f.write(f'> [{j[1]}]({j[0]})')
        if pos: f.write('\n\n')
          
os.system('termux-clipboard-set < %s'%(cpName))
#clean up
os.remove(ch_path)
os.remove(cpName)
#verbose
os.system('termux-toast -s -b white -c black Copied to clipboard!')
#open link to edit with new lecture list
os.system('termux-open-url https://rentry.co/jksdropperlectures/edit')