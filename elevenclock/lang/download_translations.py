import sys
import json
import os
import time

sys.path.append('../');
from lang_tools import *

isAutoCommit = False
isSomeChanges = False

if len(sys.argv)>1:
    if (sys.argv[1] == "--autocommit"):
        isAutoCommit = True
    else:
        print("nocommit")
        print(sys.argv[1])

try:
    apikey = open("APIKEY.txt", "r").read()
    print("  API key found in APIKEY.txt")
except FileNotFoundError:
    if (isAutoCommit):
        print("  Error: APIKEY.txt missing")
        exit(1)
    else:
        apikey = input("Write api key and press enter: ")

apiurl = f"https://app.tolgee.io/v2/projects/688/export?format=JSON&splitByScope=false&splitByScopeDelimiter=~&splitByScopeDepth=0&filterState=UNTRANSLATED&filterState=TRANSLATED&filterState=REVIEWED&zip=true&ak={apikey}"

import os
try:
    import requests
except ImportError:
    os.system("pip install requests")
    import requests
import glob, time, shutil, zipfile


print()
print("-------------------------------------------------------")
print()
print("  Downloading updated translations...")

zipcontent = requests.get(apiurl)
f = open("langs.zip", "wb")
f.write(zipcontent.content)
fname = f.name
f.close()
print("  Download complete!")
print()

downloadedLanguages = []

#olddir = "lang_backup"+str(int(time.time()))
#os.mkdir(olddir)
#for file in glob.glob('lang_*.json'):
#    os.remove(file)
#    shutil.move(file, olddir)

#print(f"  Backup complete. The old files were moved to {olddir}")
#print()
print("-------------------------------------------------------")
print()
print("  Extracting language files...")

import hashlib

def hash_file(filename):
   """"This function returns the SHA-1 hash
   of the file passed into it"""

   # make a hash object
   h = hashlib.sha1()

   # open file for reading in binary mode
   with open(filename,'rb') as file:

       # loop till the end of the file
       chunk = 0
       while chunk != b'':
           # read only 1024 bytes at a time
           chunk = file.read(1024)
           h.update(chunk)

   # return the hex representation of digest
   return h.hexdigest()

print("SHA1 of langs.zip:", hash_file(fname))

zip_file = zipfile.ZipFile(fname)

for file in glob.glob('lang_*.json'):
    os.remove(file)

for name in zip_file.namelist():
    lang = os.path.splitext(name)[0]
    if (lang in languageRemap):
        lang = languageRemap[lang]
    newFilename = f"lang_{lang}.json"
    downloadedLanguages.append(lang)

    try:
        zip_file.extract(name, "./")
        os.replace(name, newFilename)

        print(f"  Extracted {newFilename}")
    except KeyError as e:
        print(type(name))
        f = input(f"  The file {name} was not expected to be in here. Please write the name for the file. It should follow the following structure: lang_[CODE].json: ")
        zip_file.extract(f, "./")
        os.replace(f, newFilename)
        print(f"  Extracted {f}")
zip_file.close()
downloadedLanguages.sort()
os.remove("langs.zip")


print("  Process complete!")
print()
print("-------------------------------------------------------")
print()
print("  Generating translations file...")


langPerc = {}
for lang in downloadedLanguages:
    f = open(f"lang_{lang}.json", "r", encoding='utf-8')
    data = json.load(f)
    f.close()
    c = 0
    a = 0
    for key, value in data.items():
        c += 1
        if (value != None):
            a += 1
    perc = "{:.0%}".format(a / c)
    if (perc == "100%" or lang == "en"):
        continue
    langPerc[lang] = perc

if (isAutoCommit):
    os.system("git add .")
countOfChanges = len(os.popen("git status -s").readlines())
isSomeChanges = True if countOfChanges > 0 else False

outputString = f"""
# Autogenerated file, do not modify it!!!
# The following list includes ONLY non-full translated files.

untranslatedPercentage = {json.dumps(langPerc, indent=2)}
"""

f = open(f"translated_percentage.py", "w")
f.write(outputString.strip())
f.close()



print("  Process complete!")
print()
print("-------------------------------------------------------")
print()
print("  Updating README.md...")


readmeFilename = "../../README.md"

f = open(readmeFilename, "r+", encoding="utf-8")
skip = False
data = ""
for line in f.readlines():
    if (line.startswith("<!-- Autogenerated translations -->")):
        data += line + getMarkdownSupportLangs() + "\nLast updated: "+str(time.ctime(time.time()))+"\n"
        print("  Text modified")
        skip = True
    if (line.startswith("<!-- END Autogenerated translations -->")):
        skip = False
    if (not skip): data += line
if (isSomeChanges):
    f.seek(0)
    f.write(data)
    f.truncate()
f.close()


print("  Process complete!")
print()
print("-------------------------------------------------------")
print()

if (isAutoCommit):
    if (not isSomeChanges):
        os.system("git reset --hard") # prevent clean
else:
    os.system("pause")

