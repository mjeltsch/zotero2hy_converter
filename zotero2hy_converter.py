#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Converts an Atom feed from Zotero (zotero.org) into an RSS feed that is accepted by the 
# Drupal CMS that is in use by the University of Helsinki (which is very peculiar in its
# requirements.)
#
# This script was exclusively thrown together to support converting of publication data
# and probbaly won't work with anything else.
#
# The URLs of the Zotero feeds are those that I use for my own publication data and obviously
# need to be adjusted if you want to use the script to publish your own publications to an RSS
# feed.
#
# For questions, contact michael@jeltsch.org
#

import requests, json, codecs, datetime
from time import gmtime, strftime

# Make a list of all Zotero group libraries
#
urls = {}
# Featured Publications
urls["Featured_Publications"] = "https://api.zotero.org/groups/1329486/collections/7GCAFNUP/items/top?format=atom&content=json&sort=date&v=3"
# Original Research
urls["Original_Research"] = "https://api.zotero.org/groups/1329486/collections/EBMDJFSM/items/top?format=atom&content=json&sort=date&v=3"
# Books & Book Chapters
urls["Books_and_Book_Chapters"] = "https://api.zotero.org/groups/1329486/collections/SSP45PWI/items/top?format=atom&content=json&sort=date&v=3"
# Conference Proceedings
urls["Conference_Proceedings"] = "https://api.zotero.org/groups/1329486/collections/TR8JESPQ/items/top?format=atom&content=json&sort=date&v=3"
# Theses
urls["Theses"] = "https://api.zotero.org/groups/1329486/collections/NGHDVFGE/items/top?format=atom&content=json&sort=date&v=3"
# Reviews
urls["Reviews"] = "https://api.zotero.org/groups/1329486/collections/KPE97PCJ/items/top?format=atom&content=json&sort=date&v=3"

for library, url in urls.items():

	# Get the feed data
	s = requests.get(url)
	text = s.text

	# Create json string
	json_string = """{
    "publications": [\n"""
	while text:
		# Split the text where the json content starts
		text = text.split("<content zapi:type=\"json\">", 1)
		# Check whether the end of the text has been reached (= whether the string could be split) and quit the loop if yes
		try:
			value = text[1]
		except IndexError:
			break
		# Split the text where the json content ends
		json_content = text[1].split("""</content>
  </entry>""", 1)
		# This prints the first entry
		#print(json_content[0])
		json_string += json_content[0]
		json_string += ",\n"
		# Replace text by all that follows the first occurence
		text = text[1]
	# Remove last "," character
	json_string = json_string[:-2] + "\n"
	# Add json end
	json_string += """]
}"""

	# Write json string to json file
	jsonfilename = library + ".json"
	file = codecs.open(jsonfilename, "w", "utf-8-sig")
	file.write(json_string)
	file.close()

	# Parse json string
	parsed_json = json.loads(json_string)

	#Prints first publication
	#print("publicationTitle: " + parsed_json['publications'][0]['publicationTitle'])

	# Create RSS feed from parsed json string
	feedstring = ''
	for publication in parsed_json['publications']:
		# For all items
		feedstring += "    <item>\n"
		feedstring += "      <title>" + publication['title'] + "</title>\n"
		feedstring += "      <link>" + publication['url'] + "</link>\n"
		feedstring += "      <pubDate>" + publication['date'] + "</pubDate>\n"
		authorlist = ''
		editorlist = ''
		i = 0
		for creator in publication['creators']:
			if creator['creatorType'] == 'editor':
				i += 1
				if 'lastName' in creator and 'firstName' in creator:
					editorlist += creator['firstName'] + " " + creator['lastName'] + ", "
				else:
					editorlist += creator['name'] + ", "
			elif 'lastName' in creator and 'firstName' in creator:
				authorlist += creator['firstName'] + " " + creator['lastName'] + ", "
			else:
				authorlist += creator['name'] + ", "
		editorlist = editorlist[:-2]
		if i > 1:
			editorlist += " (eds.); "
		elif i == 1:
			editorlist += " (ed); "
		else:
			editorlist += "; "
		# Original Research and Reviews
		if publication['itemType'] == "journalArticle":
			# Use Journal Abbreviation if it exists
			if 'journalAbbreviation' in publication:
				description = authorlist[:-2] + "; &lt;i&gt;" + publication['journalAbbreviation'] + "&lt;/i&gt;, " + publication['volume'] + ", " + publication['pages']
			# Otherwise use full Journal name
			else:
				description = authorlist[:-2] + "; &lt;i&gt;" + publication['publicationTitle'] + "&lt;/i&gt;, " + publication['volume'] + ", " + publication['pages']
		# Book Chapter
		elif publication['itemType'] == "bookSection":
			description = authorlist[:-2] + "; In: " + publication['bookTitle'] + "; " + editorlist + publication['publisher'] + ", " + publication['pages']
		# Thesis
		elif publication['itemType'] == "thesis":
			description = authorlist[:-2] + "; " + publication['thesisType'] + "; " + publication['university'] + ", " + publication['place']
		# Conference Proceedings
		elif publication['itemType'] == "conferencePaper":
			description = authorlist[:-2] + "; &lt;i&gt;" + publication['proceedingsTitle'] + "&lt;/i&gt;; " + publication['conferenceName'] + ", " + publication['place']
		# Everything else
		else:
			description = ''
		feedstring += "      <description>" + description + "</description>\n"
		feedstring += "    </item>\n"

	# Generate time strings for the RSS header
	time_now = gmtime()
	time_string1 = strftime("%a, %d %b %Y %H:%M:%S GMT", time_now)
	time_string2 = strftime("%Y-%m-%dT%H:%M:%SZ", time_now)
	# Open file for writing
	rssfilename = library + ".rss"
	feed = codecs.open(rssfilename, "w", "utf-8-sig") 
	# Write RSS feed to file	
	feed.writelines(["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
"<rss xmlns:dc=\"http://purl.org/dc/elements/1.1/\" version=\"2.0\">\n",
"  <channel>\n",
"    <title>Zotero Feed</title>\n",
"    <link>https://jeltsch.org</link>\n",
"    <description>RSS Feed</description>\n",
'    <pubDate>{0}</pubDate>\n'.format(time_string1)])
	feed.write(feedstring)
	feed.writelines(["  </channel>\n", "</rss>\n"])
	feed.close()

