import modules.unicode as uc
import os
import re
from util.hook import *


def load_db():
    """load lines from find.txt to search_dict"""
    if not os.path.isfile("modules/find.db"):
        f = open("modules/find.db", "w")
        f.write("#test,yolo,swag\n")
        f.close()
    search_file = open("modules/find.db", "r")
    lines = search_file.readlines()
    search_file.close()
    search_dict = dict()
    for line in lines:
        line = uc.decode(line)
        line = uc.encode(line)
        a = line.replace(r'\n', '')
        new = a.split(r',')
        if len(new) < 3:
            continue
        channel = new[0]
        nick = new[1]
        if len(new) < 2:
            continue
        if channel not in search_dict:
            search_dict[channel] = dict()
        if nick not in search_dict[channel]:
            search_dict[channel][nick] = list()
        if len(new) > 3:
            result = ",".join(new[2:])
            result = result.replace('\n', '')
        elif len(new) == 3:
            result = new[-1]
            if len(result) > 0:
                result = result[:-1]
        if result:
            search_dict[channel][nick].append(uc.decode(result))
    return search_dict


def save_db(search_dict):
    """save search_dict to find.db"""
    search_file = open("modules/find.db", "w")
    for channel in search_dict:
        if channel is not "":
            for nick in search_dict[channel]:
                for line in search_dict[channel][nick]:
                    channel_utf = uc.encode(channel)
                    search_file.write(channel_utf)
                    search_file.write(",")
                    nick = uc.encode(nick)
                    search_file.write(nick)
                    search_file.write(",")
                    line_utf = line
                    if not type(str()) == type(line):
                        line_utf = uc.encode(line)
                    search_file.write(line_utf)
                    search_file.write("\n")
    search_file.close()


# Create a temporary log of the most recent thing anyone says.
@hook(rule=r'.*', priority='low')
def collectlines(code, input):
    # don't log things in PM
    channel = (input.sender).encode("utf-8")
    nick = (input.nick).encode("utf-8")
    if not channel.startswith('#'):
        return
    search_dict = load_db()
    if channel not in search_dict:
        search_dict[channel] = dict()
    if nick not in search_dict[channel]:
        search_dict[channel][nick] = list()
    templist = search_dict[channel][nick]
    line = input.group()
    if line.startswith("s/"):
        return
    elif line.startswith("\x01ACTION"):
        line = line[:-1]
        templist.append(line)
    else:
        templist.append(line)
    del templist[:-10]
    search_dict[channel][nick] = templist
    save_db(search_dict)


@hook(rule=r'(?iu)(?:([^\s:,]+)[\s:,])?\s*s\s*([^\s\w])(.*)', priority='high', rate=20)
def findandreplace(code, input):
    # don't bother in PM
    channel = (input.sender).encode("utf-8")
    nick = (input.nick).encode("utf-8")

    if not channel.startswith('#'):
        return

    search_dict = load_db()

    rnick = input.group(1) or nick  # Correcting other person vs self.

    # only do something if there is conversation to work with
    if channel not in search_dict or rnick not in search_dict[channel]:
        return

    sep = input.group(2)
    rest = input.group(3).split(sep)
    me = False  # /me command
    flags = ''
    if len(rest) < 2:
        return  # need at least a find and replacement value
    elif len(rest) > 2:
        # Word characters immediately after the second separator
        # are considered flags (only g and i now have meaning)
        flags = re.match(r'\w*', rest[2], re.U).group(0)
    # else (len == 2) do nothing special

    count = 'g' in flags and -1 or 1  # Replace unlimited times if /g, else once
    if 'i' in flags:
        regex = re.compile(re.escape(rest[0]), re.U | re.I)
        repl = lambda s: re.sub(regex, rest[1], s, count == 1)
    else:
        repl = lambda s: s.replace(rest[0], rest[1], count)

    for line in reversed(search_dict[channel][rnick]):
        if line.startswith("\x01ACTION"):
            me = True  # /me command
            line = line[8:]
        else:
            me = False
        new_phrase = repl(line)
        if new_phrase != line:  # we are done
            break

    if not new_phrase or new_phrase == line:
        return  # Didn't find anything

    # Save the new "edited" message.
    templist = search_dict[channel][rnick]
    templist.append((me and '\x01ACTION ' or '') + new_phrase)
    search_dict[channel][rnick] = templist
    save_db(search_dict)

    # output
    phrase = (
        nick + (input.group(1) and ' thinks ' + rnick or '') +
        (me and ' ' or " \x02meant\x02 to say: ") + new_phrase
    )
    if me and not input.group(1):
        phrase = '\x02' + phrase + '\x02'
    code.say(phrase)
