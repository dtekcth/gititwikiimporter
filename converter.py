import os
import re
import urllib
import requests
import json
import time

from lxml import html, etree

# Returns the pmwiki markup of a specific version of a page
def findDiffMarkup(session, page, diff):
	print(page, diff)
	pageWithSlash = page.replace(".", "/")
	response = session.get("http://dtek.se/wiki/"+pageWithSlash+"?action=edit&restore=diff:"+diff+":"+diff+"&preview=y")

	tree = html.fromstring(response.content)
	basetime = tree.xpath('//input[@name="basetime"]')

	if len(basetime) == 0:
		print("Invalid", page, diff)
		return ""

	content = tree.xpath('//textarea[@id="text"]/text()')
	if len(content) == 0:
		return ""

	data = {
		'action':'edit',
		'n':page,
		'basetime':basetime[0].value,
        	'text':content[0],
        	'csum':'',
        	'author':'simonwi',
        	'preview':'+Förhandsgranska+'
	}

	encoded = urllib.parse.urlencode(data, encoding='ISO-8859-1')

	out = session.post("http://dtek.se/wiki/Profiles/"+page+"?action=edit", data, session.headers)

	outTree = html.fromstring(out.text)
	outList = outTree.xpath('//div[@id="wikitext"]')[0].getchildren()[5:-2]
	acc = ""
	for el in outList:
		acc += etree.tostring(el,encoding='latin1', method='html', pretty_print=True).decode('utf8', 'replace')
	return(acc)

# Returns current verison of a page
def findCurrentMarkup(session, page):
    page = page.replace(".", "/")
    response = session.get("http://dtek.se/wiki/"+page+"?action=source")
    return response.text

# Returns a touple with the pagename and a dictinoray containing all versions of
# the page as (diff, author, comment)
def pageVersions(file):
    f = open(file, 'r')
    fileText = f.read()
    name = re.search('(?:name=)(.*)', fileText)
    if name is None:
        print("No name", file)
        return {}
    else:
        name = name.group(1)
        regex = re.compile('author:(?P<diff>\d{10})=(?P<author>[\w\/]*)\s(?:csum:\d{10}=(?P<comment>.*))?', re.MULTILINE)
        m = re.findall(regex, fileText)
        f.close
    return name, m

# Returns a dictionary containing all different versions of a page as
# (diff, author, comment, content)
def pageConverter(session, file):
    name, diffs = pageVersions(file)
    diffs2 = {}

    if len(diffs) > 1:
        n = 0
        for diff_number, author, comment in diffs:
            content = findDiffMarkup(session, name, diff_number)
            diffs2[n] = {'diff':int(diff_number), 'author':author, 'comment':comment, 'content':content}
            n+=1
    elif len(diffs) == 1: # If only one version of the page exists get current source instead
        content = findCurrentMarkup(session, name)
        diff_number, author, comment = diffs[0]
        diffs2[0] = {'diff':int(diff_number), 'author':author, 'comment':comment, 'content':content}
    else:
        print("Empty", file)
    return diffs2

# Finds all pages in a directory and turns them into a dictionary
def findAndConvertPages(session, directory, types, ignore_names):
	if not os.path.exists("converted"):
	    os.mkdir("converted")
	pages = os.listdir(directory)

	# Offset for starting converter at specific point, 0 = default
	# 563 = dHack (header crash)
	offset = 0
	count = 1
	for page in pages:
		pagetype, pagename = page.split('.',2)
		# Convert page if it is not on the ignore list or a deleted page
		if (pagetype in types) and (pagename not in ignore_names) and (len(page.split(',')) < 2):
			if count >= offset and not os.path.isfile('converted/'+page):
				f = open('converted/'+page, 'w')
				pagecontent = pageConverter(session, directory+page)
				f.write(json.dumps(pagecontent, sort_keys=True, indent=4, separators=(',', ': ')))
				f.close
			elif os.path.isfile('converted/'+page):
				print(page+" is already parsed, if it is not finished, remove this file.")
		count += 1

def main(filename, username, password):
	s = requests.Session()
	s.post("https://dtek.se/wiki/Main/LoginPage?action=login", data={"username" : username,"password" : password})
#	pageConverter(s, "/home/swij/Kod/wiki/wiki.d/Profiles.Rövgoat")
	findAndConvertPages(s, "/home/swij/Kod/wiki/wiki.d/", ["Main", "Profiles"], ["RecentChanges", "GroupAttributes", "Profiles", "Rövgoat"])
	#print(findAndConvertPages(s, "/home/swij/Kod/wiki/converted/", ["Main","Profiles"]))
	#print (json.dumps(pageConverter(s, filename)))

main("", "username", "password")
