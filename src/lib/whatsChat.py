import re, csv


class ChatParser:
    def __init__(self, path: str) -> None:
        """'parses raw WhatsApp export chat into usable format"""
        self.parsedData = []
        with open(path, encoding="utf-8") as file:
            file.readline()
            # skipping first line of the file (end-to-end encryption msg)
            messageBuffer = []
            # for multi-line messages
            date, time, author = None, None, None

            while True:
                line = file.readline()
                if not line:
                    # stop reading further if end of file has been reached
                    # appending data from last iteration before break
                    self.parsedData.append(
                        [date, time, author, " ".join(messageBuffer)]
                    )
                    break
                line = line.strip()
                if self._startsWithDateTime(line):
                    # If a line starts with a date time pattern, then this indicates the beginning of a new message
                    if len(messageBuffer) > 0:
                        # check if the message buffer contains characters from previous iterations
                        self.parsedData.append(
                            [date, time, author, " ".join(messageBuffer)]
                        )
                        # save the data from the previous message in parsedData
                    messageBuffer.clear()
                    # clearing for next message
                    date, time, author, message = self._getData(line)
                    messageBuffer.append(message)
                else:
                    messageBuffer.append(line)
                    # if a line doesn't start with a date time (i.e. the message is in continuation)

    @property
    def get(self) -> list:
        return self.parsedData

    def export_csv(
        self, file: str, header=["Date", "Time", "Author", "Message"]
    ) -> None:
        assert isinstance(header, (list, str)) and len(header) == 4, "Improper header!"
        with open(file, "w+") as export:
            csv.writer(export).writerows([header] + self.get())

    @staticmethod
    def _startsWithDateTime(s: str) -> bool:
        """'regex to identify date time pattern"""
        pattern = "^(([1-9])|((0)[0-9])|((1)[0-2]))(\/)([1-9]|[0-2][0-9]|(3)[0-1])(\/)(\d{2}|\d{4}), "
        "([1-9]|[0-9][0-9]):([0-9][0-9]) ((PM)|(AM)) -"
        result = re.match(pattern, s)
        if result:
            return True
        return False

    @staticmethod
    def _startsWithAuthor(s: str) -> bool:
        """regex to identify author of an message"""
        patterns = [
            "([\w]+):",  # first name
            "([\w]+[\s]+[\w]+):",  # first name + last Name
            "([\w]+[\s]+[\w]+[\s]+[\w]+):",  # first name + middle Name + last name
            "([+]\d{2} \d{5} \d{5}):",  # mobile number
            "([+]\d{2} \d{4} \d{3} \d{3}):",
            "([+]\d{2} \d{3} \d{3} \d{4}):",
            "([+]\d{2} \d{4} \d{7})",
        ]
        pattern = "^" + "|".join(patterns)
        result = re.match(pattern, s)
        if result:
            return True
        return False

    def _getData(self, line: str) -> tuple:
        """parses the raw chat and returns its each component"""
        # line = "18/06/17, 12:47 PM - Mario: Ima..."
        splitLine = line.split(" - ")
        dateTime = splitLine[0]
        date, time = dateTime.split(", ")
        message = " ".join(splitLine[1:])
        if self._startsWithAuthor(message):  # True
            splitMessage = message.split(": ")
            author = splitMessage[0]
            message = " ".join(splitMessage[1:])
        else:
            author = None
        return date, time, author, message
