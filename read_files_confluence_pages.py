#!/usr/bin/python
# Read text from the first example file of each type and update or create wiki pages with the content
# Read properties file with wiki credentials and details
# Force option overwrites manually updated pages
# Compatible with: Python 2.7
# TODO: parameterise input files directory and mediatype version number
import sys
import json
import string
import xmlrpclib
import re
import ast
import glob
import os
import logging
from distutils.util import strtobool

class wikiAuth:
	def __init__(self,auser,apassword,atoken):
		self.user=auser
		self.password=apassword
		self.token=atoken

class wikiLoc:
	def __init__(self,awikiUrl,aspaceKey,aparentTitle):
		self.wikiUrl=awikiUrl
		self.spaceKey=aspaceKey
		self.parentTitle=aparentTitle


def open_if_not_existing(filename):
	try:
		fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
	except:
		logging.error("File: %s already exists" % filename)
		return None
	fobj = os.fdopen(fd, "w")
	return fobj

def write_json_file(filename,jsondict):
	# open if not existing
	jsf = open_if_not_existing(filename)
	# dump json
	if jsf:
		json.dump(jsondict, jsf)
	jsf.close

def process_stringbool(userInput):
    try:
        return strtobool(userInput.lower())
    except ValueError:
    	logging.warning('Invalid boolean property %s' % userInput)
        sys.stdout.write('Invalid boolean property')


def get_properties_file():
	# Load properties for the script, including wiki properties that can't be stored in a public repo
	properties = {}
	with open("confluence_properties.json.txt") as pfile:
		prop_file = pfile.read().replace('\n', '')	
		prop_file = prop_file.replace('\t', " ")
		properties = json.loads(prop_file)
		for ix, ick in enumerate(properties):
#			print "%d: %s - %s" % (ix,ick,properties[ick])
			logging.info("%d: %s - %s" % (ix,ick,properties[ick]))
	wikiUrl = properties['wikiUrl']
	spaceKey = properties['spaceKey']
	parentTitle =  properties['parentTitle'] 
	getforce = properties['confluenceForcePageUpdate']
	force = process_stringbool(getforce)
	user = properties['user']
	password = properties['password']
	wloc = wikiLoc(wikiUrl,spaceKey,parentTitle)
	server = xmlrpclib.ServerProxy(wikiUrl + '/rpc/xmlrpc')
	token = server.confluence2.login(user, password)
	wauth = wikiAuth(user,password,token)
	subdir = properties['subdir']
	return (wloc,wauth,force,server,subdir)


def get_page(wikAuth,wikLoc,pageTitle,server):
# returns the page
	page = {}
	token = server.confluence2.login(wikAuth.user, wikAuth.password)	
	try:	
		page = server.confluence2.getPage(token, wikLoc.spaceKey, pageTitle)
	except xmlrpclib.Fault as err:
		print ("No page created")
		logging.info ("Confluence fault code: %d and string: %s " % (err.faultCode,err.faultString))
#		logging.info ("Confluence string: %s " % err.faultString)	
	return page		
	

def check_page_mod(wikAuth,wikLoc,pagetitle,pagepathfile,server,parentId):
	# check pages for modification and return modification
	token = server.confluence2.login(wikAuth.user, wikAuth.password)
	alt_filename = ""
	gotpage = get_page(wikAuth,wikLoc,pagetitle,server)
	# update forced only 
	# A page may already exist with a different name if there is a upper/lower case version of a test
	return_value = ""
	if gotpage:
		pgcontent = ""
		# copy page content
		pgcontent = gotpage['content']
		# search for a filename on the page
		filename_searchstring = pagetitle + "\.([0-9][0-9][0-9][0-9])\.txt"
		fnm = re.search(filename_searchstring,pgcontent)
		if fnm:
			logging.info("Page %s found containing file name %s " % (fnm.group(0),pagetitle))
	#		print "fnm: %s " % fnm.group(0)
			if fnm.group(1) == "0001":
				modifier = gotpage['modifier']
				if modifier != wikAuth.user:
				#	print "The page %s was manually modified by %s" % (modifier,pagetitle)
					logging.info("The page %s was manually modified by %s" % (modifier,pagetitle))
					# store page in update forced only
					return_vale = "modifer: " + modifier
			else:
				alt_filename = fnm.group(0)
				logging.info("Page: %s uses file: %s " % (pagetitle,alt_filename))
#				alt_filepath = os.path.join(subdir,alt_filename)
				return_value = "alternative: " + alt_filename
				# if group 1 is not 0001, use the alternative filename
		else:
			# the filename may be the same but with a by "XXXX" or "xxxxx" (i.e. in capital letters or lower case)
			fnigc = re.search(filename_searchstring,pgcontent,re.IGNORECASE)
			if fnigc:
				logging.info("The page %s already exists but with the filename %s" % (pagetitle,fnigc.group(0)))
				return_value = "duplicate: " + fnigc.group(0)
			else:	
				logging.error("In the wrong place")
				cs = r'abiheader</ac\:parameter><ac\:rich-text-body>' + '([\w,\.]+)' + r'<'
				fncust = re.search(cs,pgcontent)
				ca = r'abiheader</ac:parameter><ac:rich-text-body>'
				fnca = re.search(ca,pgcontent)
				if fnca:
					logging.error ("Hello!")	
				if fncust:
					logging.info ("group0: %s |group1: %s " % (fncust.group(0),fncust.group(1)))
					if fncust.group(1):
						logging.error ("found something else")
						logging.info("The page %s exists and has a custom filename %s " % (pagetitle,fncust.group(1)))
						return_value = "custom: " + fncust.group(1)
					else:
						return_value = "invalid"			
			# if there is no valid auto filename in the file, then the file has a manual update 		
   			# put custom
   				else:
   					return_value = "invalid"
   					logging.info("The page %s was found but did not contain a valid filename" % (pagetitle))
   	else:
   		logging.info("The page %s could not be found" % pagetitle)
   		return_value = "new"
   	return(return_value)			

def create_file_page_list(globPath):
	pathfiles = glob.glob(globPath)
	FFiles = {}
	for pff in pathfiles:
		pf_path, pf = os.path.split(pff)
		ffpg = pf.split(".")
		fpg = ffpg[0]
		FFiles[fpg]=pf
		logging.info("Create file: %s and page name: %s " % (pff,fpg))
	return(FFiles)


def get_content_file_names(inputSubdir):
	# read all number 0001 pages in the directory
	# mypath = "big/*.0001.txt"
	# # get the files and only take the first part of the name without the 0001.txt
	oneFiles = {}
	mypath = inputSubdir + "/*.0001.txt"
	logging.info("mypath %s " % mypath)
	oneFiles = create_file_page_list(mypath)

	# read all the license files in the directory to avoid them
	licenseFiles = {}
	licpath = inputSubdir + "/*license*"
	logging.info("licpath %s " % licpath)
	licenseFiles = create_file_page_list(licpath)
	return(oneFiles,licenseFiles)


def main():
	logging.basicConfig(filename='read_files_pages.log',level=logging.DEBUG)
	logging.info("***Starting script now ***")
	# load properties file with wiki properties
	(loc,auth,force,server,inputSubdir) = get_properties_file()

	allFiles = {}
	licFiles = {}
	updFiles = {}

	# retrieve the names of all the 0001 files 
	# and also the license files to add to the prohibited list
	(allFiles,licFiles) = get_content_file_names(inputSubdir)
	for lix in licFiles:
		print "lix: %s" % lix

	# retrieve the parent page where the pages will be stored and get its ID
	parentPage = get_page(auth,loc,loc.parentTitle,server)
	if parentPage:
	# I don't know how to handle this exception properly 
	# because if the parent page doesn't exist, it's different to if a normal page doesn't exist
		parentId = parentPage['id']

		# try to determine any pages that have been modified and put them in updFiles dictionary
		for pagen in allFiles:
			logging.info ("pagen: %s " % pagen)
			if pagen in licFiles:
				logging.info ("Skipping page containing license - %s " % pagen)
			else:
				pagenPath = allFiles[pagen]
				pagenUpdatedPage = check_page_mod(auth,loc,pagen,pagenPath,server,parentId)
				if pagenUpdatedPage:
					updFiles[pagen] = pagenUpdatedPage				
	else:
		logging.error ("Can't find the parent page %s" % loc.parentTitle)			
	for lix in licFiles:
		print "lix: %s" % lix
	for uix in updFiles:
		print "uix: %s" % uix		
	# write one JSON file for each list 
	write_json_file("wiki_all_files.json.txt",allFiles)
	write_json_file("wiki_prohibited.json.txt",licFiles)
	write_json_file("wiki_force_update.json.txt",updFiles)



# Calls the main() function
if __name__ == '__main__':
	main()

