# DEPRECATED
from wchat import chat
import re

# parsing recorded lectures links
ch_path = ""
parsedData = chat(ch_path).get()
print(f"source: {ch_path}")
recLectureData = []
for i, j in enumerate(parsedData):
    recSearch = re.search("https\:\/\/us\d{2}web\.zoom\.us\/rec", j[-1])
    if recSearch:
        dataBuffer = []
        dataBuffer.append(j[-1])
        # link
        try:
            if recSearch.start() == 0:
                dataBuffer.append(parsedData[i + 1][-1])
            else:
                if re.search("[lL]ecture", parsedData[i + 1][-1]) and not re.search(
                    "https", parsedData[i + 1][-1]
                ):
                    dataBuffer.append(parsedData[i + 1][-1])
                else:
                    dataBuffer.append(None)
        except:
            dataBuffer.append(None)
        # description of link
        dt = j[0].split("/")
        dt[0], dt[1] = dt[1], dt[0]
        # swapping dates and months position
        dataBuffer.append("/".join(dt))
        # date
        recLectureData.append(dataBuffer)

print("export lectures links?(Y/N): ", end="")
choice = input()
if re.match("(^[yY]\w{0,0}$)", choice):
    while 1:
        print("file name: ", end="")
        exp_name = input()
        if re.match("(^[a-zA-Z]\w{0,26}$)", exp_name):
            while 1:
                print("file type?(md/txt): ", end="")
                fl_type = input()
                if re.match(r"(^(\b(txt)\w{0,0}\b)|(\b(md)\w{0,0}\b)$)", fl_type):
                    with open(exp_name + "." + fl_type, "w") as f:
                        mode = 0
                        if fl_type == "md":
                            mode = 1
                            f.write("####Recent ↑\n")
                        for i, j in enumerate(recLectureData[::-1]):
                            pos = (len(recLectureData) - 1) != i
                            if mode:
                                f.write(f"**`{j[2]}`**\n")
                                if re.match("(^http)", j[0]):
                                    f.write(f"> [{j[1]}]({j[0]})")
                                else:
                                    lnk = re.search(
                                        "(((https\:\/\/us\d{2}web\.zoom\.us\/rec)(.*)(startTime=[\d]+))|((https\:\/\/us\d{2}web\.zoom\.us\/rec\/share\/)([^\s]+)))",
                                        j[0],
                                    ).group(1)
                                    if j[1] == None:
                                        msg = j[0].replace(lnk, "").strip()
                                        f.write(f"> [{msg}]({lnk})")
                                    else:
                                        f.write(f"> [{j[1]}]({lnk})")
                                if pos:
                                    f.write("\n\n")
                            else:
                                f.write(f"{j[0]}\n{j[1]}")
                    break
                print("invalid!")
            break
        print("invalid!")
    print(f"saved as {exp_name+'.'+fl_type}")
