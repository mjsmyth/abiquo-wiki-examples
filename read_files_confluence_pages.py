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
	

def check_page_mod(wikAuth,wikLoc,force,pagetitle,pagepathfile,server,parentId,updFiles):
	# check pages for modification and build a list
	token = server.confluence2.login(wikAuth.user, wikAuth.password)
	alt_filename = ""
	gotpage = get_page(wikAuth,wikLoc,pagetitle,server)
	# update forced only 
	# If a page with this name exists
	if gotpage:
		# copy page content
		pgcontent = gotpage['content']
		# search for a filename on the page
		filename_searchstring = pagetitle + "\.([0-9][0-9][0-9][0-9])\.txt"
		fnm = re.search(filename_searchstring,pgcontent)
		#print "fnm: %s " % fnm.group(0)
		if fnm:
			if fnm.group(1) == "0001":
				modifier = gotpage['modifier']
				if modifier != wikAuth.user:
				#	print "The page %s was manually modified by %s" % (modifier,pagetitle)
					logging.info("The page %s was manually modified by %s" % (modifier,pagetitle))
					# store page in update forced only
					updFiles[pagetitle] = pagepathfile
			else:	
				alt_filename = fnm.group(0)
				logging.info("The page: %s uses file: %s " % (pagetitle,alt_filename))
#				alt_filepath = os.path.join(subdir,alt_filename)
				updFiles[pagetitle] = alt_filename 
				# if group 1 is not 0001, use the alternative filename
		else:
		# if there is no valid filename in the file, then the file has a manual update 		
   		# put custom
   			updFiles[pagetitle] = "custom"
   			logging.info("The page: %s has been manually modified and will not be updated" % pagetitle)


def create_file_page_list(globPath):
	pathfiles = glob.glob(globPath)
	pageFiles = {}
	for pff in pathfiles:
		pf_path, pf = os.path.split(pff)
		ffpg = pf.split(".")
		fpg = ffpg[0]
		pageFiles[fpg]=pff
		logging.info("Full file path: %s and page name: %s " % (pff,fpg))
	return(pageFiles)


def get_content_file_names(inputSubdir):
	# read all number 0001 pages in the directory
	# mypath = "big/*.0001.txt"
	# # get the files and only take the first part of the name without the 0001.txt
	pagenames = []
	mypath = inputSubdir + "/*.0001.txt"
	print "mypath %s " % mypath
	oneFiles = create_file_page_list(mypath)

	# read all the license files in the directory to avoid them
	licpagenames = []
	licpath = inputSubdir + "/*license*"
	print "licpath %s " % licpath
	licenseFiles = create_file_page_list(licpath)
	return(oneFiles,licenseFiles)


def main():
	logging.basicConfig(filename='confluence_update_examples.log',level=logging.DEBUG)
	# load properties file with wiki properties
	(loc,auth,force,server,inputSubdir) = get_properties_file()

	allFiles = {}
	licFiles = {}
	updFiles = {}

	# retrieve the names of all the 0001 files 
	# and also the license files to add to the prohibited list
	(allFiles,licFiles) = get_content_file_names(inputSubdir)

	# retrieve the parent page where the pages will be stored and get its ID
	parentPage = get_page(auth,loc,loc.parentTitle,server)
	if parentPage:
	# I don't know how to handle this exception properly 
	# because if the parent page doesn't exist, it's different to if a normal page doesn't exist
		parentId = parentPage['id']

		# try to determine any pages that have been modified and put them in updFiles dictionary
		for pagen in allFiles:
			print "pagen: %s " % pagen
			if pagen in licFiles:
				logging.info ("Skipping page containing license - %s " % pagen)
			else:
				pagenPath = allFiles[pagen]
				try:
					check_page_mod(auth,loc,pagen,pagenPath,server,parentId,updFiles)
				except:
					logging.info ("Could not find page - %s " % pagen)
				ncf.close()
	else:
		logging.error ("Can't find the parent page %s" % loc.parentTitle)			

	# write one JSON file for each list 
	write_json_file("All_files.json.txt",allFiles)
	write_json_file("Prohibited_files.json.txt",licFiles)
	write_json_file("Force_update.json.txt",updFiles)



# Calls the main() function
if __name__ == '__main__':
	main()

