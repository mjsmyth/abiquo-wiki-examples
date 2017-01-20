# Python script: getConfluencePageContent
# ---------------------------------------
# Friendly warning: This script is provided "as is" and without any guarantees.
# I developed it to solve a specific problem.
# I'm sharing it because I hope it will be useful to others too.
# If you have any improvements to share, please let me know.
#
# Author: Sarah Maddox
# Source: https://bitbucket.org/sarahmaddox/confluence-full-text-search
# Usage guide: http://ffeathers.wordpress.com/2013/04/20/confluence-full-text-search-using-python-and-grep/
#
# A Python script that gets the content of all pages in a given Confluence space.
# It puts the content of each page into a separate text file, in a given directory.
# The content is in the form of the Confluence "storage format",
# which is a type of XML consisting of HTML with Confluence-specific elements.
#
# This script works with Python 3.2.3
###############
# Script modified by MJ to:
# - Get the content of child pages under APIExamples page
# - Write a file with page details for each page
# - Write page files
#
# - Try to update the wiki with the files


import xmlrpc.client
import os
import re
import time
import json
import collections
import glob

def tree(): return collections.defaultdict(tree)

def open_content_file(subdir,content_file_name):
	c_file_name = os.path.join(subdir,content_file_name)
#	logging.info("c_file_name: %s " % c_file_name)
	newc = ""
	try: 
		ncf = open(c_file_name,'r')	
		newc = ncf.read()
#		logging.info("Read content file okay")
		ncf.close()
	except:
#		logging.info("Could not open content file %s " % c_file_name)
 		print("Could not open content file %s " % c_file_name)
	return newc

def create_file_page_list(globPath):
	pathfiles = glob.glob(globPath)
	FFiles = {}
	for pff in pathfiles:
		pf_path, pf = os.path.split(pff)
		ffpg = pf.split(".")
		fpg = ffpg[0]
		FFiles[fpg]=pf
	return(FFiles)

def get_content_file_names(inputSubdir):
	# read all number 0001 pages in the directory
	# mypath = "big/*.0001.txt"
	# # get the files and only take the first part of the name without the 0001.txt
	oneFiles = {}
	mypath = inputSubdir + "/*.0001.txt"
#	logging.info("mypath %s " % mypath)
	oneFiles = create_file_page_list(mypath)
	# read all the license files in the directory to avoid them
	licenseFiles = {}
	licpath = inputSubdir + "/*license*"
#	logging.info("licpath %s " % licpath)
	licenseFiles = create_file_page_list(licpath)
	return(oneFiles,licenseFiles) 


def write_json_file(fname,jsondict,sbdir):
	jsf = open(os.path.join(sbdir,fname), "w+")
	if jsf:
		json.dump(jsondict, jsf)
		jsf.close

def get_page(server,ctoken,spaceKeyX,pageTitle):
# return the page
	page = {}
#   token = server.confluence2.login(wikAuth.user, wikAuth.password)
	time.sleep(1)   
	try:    
		page = server.confluence2.getPage(ctoken, spaceKeyX, pageTitle)
	except xmlrpclib.Fault as err:
#       logging.info ("Confluence fault code: %d and string: %s " % (err.faultCode,err.faultString))
		print ("Confluence fault code:" + err.faultCode + " and string: " + err.faultString)
	return page     

def search_for_filename(pgcontent):
# search for any filename on the page
	sff = ""
#    filename_searchstring = r'abiheader</ac\:parameter>'+ "[\n\t\s]*?" + r'<ac\:rich-text-body>' + "[\n\t\s]*?([\w.]*?)[\n\s\t]*?" + r'<'
	filename_searchstring = r'abiheader</ac\:parameter>' + ".*?" + r'<ac\:rich-text-body>' + "([\w.]*?)" + r'<'
	fnm = re.search(filename_searchstring,pgcontent,re.DOTALL)
	if fnm:
	   sff = fnm.group(1)    
	return sff
   
def remove_spans(pgcontent):
# search and replace any spans on the page
	span_searchstring = r'<span'+ ".*?" + r'>' 
	endspan_searchstring = r'</span>'    
	nostartspan = re.sub(span_searchstring,"",pgcontent,re.DOTALL)
	noendspan = re.sub(endspan_searchstring,"",nostartspan,re.DOTALL)
	return noendspan

def get_old_style_name(filename):
	print ("Filename: " + filename)
	oldname = filename.split(".")
	if oldname:
		oname = oldname[0]
	else:
		oname = filename[:]
	return oname		

def get_page_content(pages_list,server,mtoken,parentId,spacekey,page_details):

	# For each page, get the content of the page, get the filename, and write the content and details out to a file
	for page in pages_list:
		# Get the content of the page
		page_content = {}
	#   token = server.confluence2.login(wikAuth.user, wikAuth.password) 
		try:    
			page_content = server.confluence2.getPage(mtoken, page["id"])		
	#		page = server.confluence2.getPage(ctoken, spaceKeyX, pageTitle)
		except:
	#       logging.info ("Confluence fault code: %d and string: %s " % (err.faultCode,err.faultString))
			print ("Could not get Confluence page: " + page["title"] + "with ID: " + page["id"])  


		# File name is equal to page name without special characters, plus page ID.
		# Use a regular expression (re) to strip non-alphanum characters from page name.
		page_name = page["title"]
		page_id = page["id"]
		page_name_qualified = (re.sub(r'([^\s\w]|_)+', '', page_name)) + "-" + page_id
		# Open the output file for writing. Will overwrite existing file.
		# File is in the required output directory.
#		page_file = open(os.path.join(output_path, page_name_qualified), "w+")
		# Write a line containing the URL of the page, marked with asterisks for easy grepping#
#		page_file.write("**" + page["url"] + "**\n")
		# Write the page content to the file, after removing any weird characters such as a BOM

		page_content_unsafe = page_content["content"]

		# safe_content = str(page_content_unsafe.encode('ascii', 'xmlcharrefreplace'))
		# # Remove unwanted characters at beginning and end
		# safe_content = str.lstrip(safe_content, "b'")
		# safe_content = str.rstrip(safe_content, "'")
		# no_span_content = remove_spans(safe_content) 

		no_span_wiki_content = remove_spans(page_content_unsafe)
		filename = search_for_filename(no_span_wiki_content)
		
		oname = get_old_style_name(filename)
		print ("oldstylename: " + oname)	
		# page_file.write(no_span_wiki_content)
		# page_file.close()

		page_details[oname]["page_info"] = page
		page_details[oname]["filename"] = filename[:]
		page_details[oname]["page_info"]["content"] = no_span_wiki_content[:]
		page_details[oname]["updated"] = "existingPage"
		page_details[oname]["oldpagename"] = oname[:]

	return page_details

def get_file_content(allFiles,licFiles,server,mtoken,parentId,spacekey,page_details,input_path):
	valid_rest_options = ['GET','DELETE','OPTIONS','PUT','POST','PATCH']
	for afile,afilename in allFiles.items():
		if afile not in licFiles:
			# check not a license file
			pRestOption = afile.split("_")
#				print ("Rest option: " + pRestOption[0])
			if pRestOption[0] in valid_rest_options:	
				if afile in page_details:
					if afilename == page_details[afile]["filename"]:
						print ("Update existing page: " + afile )
						# write the content of the file to the page
						file_content = open_content_file(input_path,afilename)
						page_details[afile]["page_info"]["content"] = file_content[:]
						page_details[afile]["updated"] = "updatedPage"						

					else: 
						print ("Existing file not updated: " + page_details[afile]["filename"])										
				else:
					pagenew = {}
						# page_details[afilename] = {}
						# page_details[afilename]["page_info"] = {}
						# page_details[afilename]["page_info"]["title"] = ptitle[0]
						# page_details[afilename]["page_info"]["content"]
						# page_details[afilename] = afilename
					pagenew["parentId"] = parentId
					pagenew["space"] = spacekey[:]
					pagenew["title"] = afile[:]
					file_content = open_content_file(input_path,afilename)
					pagenew["content"] = file_content[:]
					page_details[afile]["page_info"] = pagenew.copy()
					page_details[afile]["filename"] = afilename[:]
					page_details[afile]["updated"] = "newPage"
					page_details[afile]["oldpagename"] = afile[:]
	return page_details

def main():
	# Get from input: Confluence URL, username, password, space key, output directory

	print("G'day! I'm the getConfluencePageContent script.\nGive me a Confluence space, and I'll give you the content of all its pages.\n")
	site_URL = input("Confluence site URL (exclude final slash): ")
	username = input("Username: ")
	pwd = input("Password: ")
	spacekey = input("Space key: ")
	output_directory = input("Output directory (relative to current, exclude initial slash, example 'output'): ")

	test = False
	if test == True:
		input_path = "./v4files"
		parentTitle = "APIExamplesTest"
		ofname = "ztest.txt"
		ojfname = "ztest.json.txt"
		ofname2 = "ztestUpdated.txt"
		ofname3 = "zjfiles.txt"
	else:	
		input_path = "./v310newfiles"
		parentTitle = "APIExamples"
		ofname = "zNewUpdateWikiExamples.txt"		
		ojfname = "zNewUpdateWikiExamples.json.txt"
		ofname2 = "zNewUpdatedinWiki.txt"
		ofname3 = "zNewJFiles.txt"

	# Create the output directory
	# os.mkdir("../output")
	output_path = "../" + output_directory
	os.mkdir(output_path)

	# Log in to Confluence
	server = xmlrpc.client.ServerProxy(site_URL + "/rpc/xmlrpc")
	mtoken = server.confluence2.login(username, pwd)



	# retrieve the parent page where the pages will be stored and get its ID
	parentPage = get_page(server,mtoken,spacekey,parentTitle)

	if parentPage:
		parentId = parentPage['id']

	# Get all child pages
	pages_list = server.confluence2.getChildren(mtoken, parentId)

	# Get all the pages in the space
	#pages_list = server.confluence2.getPages(token, spacekey)



	page_details = tree()

	page_details = get_page_content(pages_list,server,mtoken,parentId,spacekey,page_details)


	# retrieve the names of all the 0001 files 
	# and also the license files to add to the prohibited list
	(allFiles,licFiles) = get_content_file_names(input_path)
	

	page_details = get_file_content(allFiles,licFiles,server,mtoken,parentId,spacekey,page_details,input_path)

	print("All done! I've put the results in this directory: ", output_directory)
	write_json_file(ojfname,page_details,"./")

	heading = "|| Page name || Updated || Filename || Page ID || Page URL ||\n"
	output_file = open(os.path.join("./",ofname), "w+")

	output_file.write(heading)
	for apiex,apiexentry in page_details.items():
		if apiexentry["updated"] == "existingPage":
			toWrite = "| " + apiexentry["page_info"]["title"] + " | " + apiexentry["updated"] + " | " + apiexentry["filename"] + " | " + apiexentry["page_info"]["id"] + " | " + apiexentry["page_info"]["url"] + "| \n"
		if apiexentry["updated"] == "newPage":
			toWrite = "| " + apiexentry["page_info"]["title"] + " | " + apiexentry["updated"] + " | " + apiexentry["filename"] + " |  |  | \n"
		if apiexentry["updated"] == "updatedPage":
			toWrite = "| " + apiexentry["page_info"]["title"] + " | " + apiexentry["updated"] + " | " + apiexentry["filename"] + " | " + apiexentry["page_info"]["id"] + " | " + apiexentry["page_info"]["url"] + "| \n"
		output_file.write(toWrite)
	output_file.close()	


	output_file2 = open(os.path.join("./",ofname2), "w+")
	heading2 = "|| Page_name  ||  Filename  ||\n"
	output_file2.write(heading2)
	output_file3 = open(os.path.join("./",ofname3), "w+")

	pUpdateOptions = {}
	updatedPages = []
	for ae,apiexent in page_details.items():
		if apiexent["filename"].lower() not in updatedPages:
			draft_page = {}
			towrite2 = ""
			draft_page = apiexent["page_info"].copy()
			if apiexent["updated"] == "existingPage":
#				toWrite2 = "| " + apiexent["page_info"]["title"] + " | " + apiexent["updated"] + " | " + apiexent["filename"] + " | " + apiexent["page_info"]["id"] + " | " + apiexent["page_info"]["url"] + "| \n"
				if "j0" in apiexent["page_info"]["title"]:
					j0stuff = apiexent["page_info"]["title"] + "\n"	
					output_file3.write(j0stuff)
			if apiexent["updated"] == "newPage":
				toWrite2 = "| " + apiexent["page_info"]["title"] + " | " + apiexent["updated"] + " | " + apiexent["filename"] + " |  |  | \n"
				print("Creating wiki page: " + apiexent["page_info"]["title"])
				# try:
				# 	time.sleep(1)
				# 	server.confluence2.storePage(mtoken, draft_page)
				# 	updatedPages.append(apiexent["filename"].lower())
				# 	output_file2.write(toWrite2)
				# except:
				# 	print("Failed to create page: "+ apiexent["filename"] )	
			if apiexent["updated"] == "updatedPage":
				toWrite2 = "| " + apiexent["page_info"]["title"] + " | " + apiexent["updated"] + " | " + apiexent["filename"] + " | " + apiexent["page_info"]["id"] + " | " + apiexent["page_info"]["url"] + "| \n"
				pUpdateOptions["versionComment"] = "3.10 script " + apiexent["filename"][:]
				pUpdateOptions["minorEdit"] = False
				print("Updating the wiki with page: " + apiexent["page_info"]["title"])				
				# try:
				# 	time.sleep(1)
				# 	server.confluence2.updatePage(mtoken, draft_page, pUpdateOptions)
				# 	updatedPages.append(apiexent["filename"].lower())
				# 	output_file2.write(toWrite2)
				# except:
				# 	print("Failed to update page: "+ apiexent["filename"] )	

	output_file2.close()	
	output_file3.close()

# Calls the main() function
if __name__ == '__main__':
	main()