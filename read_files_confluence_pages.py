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
import collections

def tree(): return collections.defaultdict(tree)

class wikiAuth:
	def __init__(self,auser,apassword):
		self.user=auser
		self.password=apassword


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

	user = properties['user']
	password = properties['password']
	wloc = wikiLoc(wikiUrl,spaceKey,parentTitle)
	server = xmlrpclib.ServerProxy(wikiUrl + '/rpc/xmlrpc')
	wauth = wikiAuth(user,password)
	subdir = properties['subdir']
	return (wloc,wauth,server,subdir)


def get_page(wikAuth,wikLoc,pageTitle,server,ctoken):
# returns the page
	page = {}
#	token = server.confluence2.login(wikAuth.user, wikAuth.password)	
	try:	
		page = server.confluence2.getPage(ctoken, wikLoc.spaceKey, pageTitle)
	except xmlrpclib.Fault as err:
#		print ("No page found")
		logging.info ("Confluence fault code: %d and string: %s " % (err.faultCode,err.faultString))
#		logging.info ("Confluence string: %s " % err.faultString)	
	return page		
	

def check_page_mod(wikAuth,wikLoc,pagetitle,pagepathfile,server,parentId,atoken):
	# check pages for modification and return modification
#	atoken = server.confluence2.login(wikAuth.user, wikAuth.password)
	alt_filename = ""
	gotpage = get_page(wikAuth,wikLoc,pagetitle,server,atoken)
	# update optional
	# This section is a bit strung together because I did it over several weeks but basically the idea is to search for 
	# filenames in the Confluence pages. 
	return_value = ""
	return_type = ""
	if gotpage:
		pgcontent = ""
		# copy page content
		pgcontent = gotpage['content']
		# search for a filename on the page
		filename_searchstring = r'abiheader</ac\:parameter><ac\:rich-text-body>' + pagetitle + "\.([0-9][0-9][0-9][0-9])\.txt" + r'<'
		fnm = re.search(filename_searchstring,pgcontent)
		origfile = pagetitle + ".0001.txt"
		if fnm:
			logging.info("Page %s found containing file name %s " % (pagetitle,origfile))
	#		print "fnm: %s " % fnm.group(0)
			if fnm.group(1) == "0001":
				modifier = gotpage['modifier']
				if modifier != wikAuth.user:
				#	print "The page %s was manually modified by %s" % (modifier,pagetitle)
					logging.info("The page %s was manually edited by %s" % (pagetitle,modifier))
					# store page in update forced only
					return_type = "modifier"
					return_value = modifier
				else:
					return_type = "original"
					return_value = origfile
			else:
				altfile = pagetitle + "." + fnm.group(1) + ".txt"
				logging.info("Page: %s uses file: %s " % (pagetitle,altfile))
				return_type = "alternative"
				return_value = altfile
				# if group 1 is not 0001, use the alternative filename
		else:
			# the filename may be the same but with capital or lowercase letters (search by "XXXX" or "xxxxx")
			fnigc = re.search(filename_searchstring,pgcontent,re.IGNORECASE)
			if fnigc:
				dupfile = pagetitle + "." + fnigc.group(1) + ".txt"
				logging.info("The page %s already exists but with the filename %s" % (pagetitle,dupfile))
				return_type = "duplicate" 
				return_value = dupfile
			else:	
				cs = r'abiheader</ac\:parameter><ac\:rich-text-body>' + '([\w,\.]+)' + r'<'
				fncust = re.search(cs,pgcontent)
				if fncust:
					logging.info("The page %s exists and has a custom filename %s " % (pagetitle,fncust.group(1)))
					return_type = "custom" 
					return_value = fncust.group(1)
				else:
					ca = r'abiheader</ac\:parameter><ac\:rich-text-body>' + '([\w,\.,\s]+)' + r'<'
					fnca = re.search(ca,pgcontent)
					if fnca:
						logging.info("Page %s exists and has an invalid filename containing whitespace %s " % (pagetitle,fnca.group(1)))
						return_type = "invalid"
						return_value = pagepathfile			
			# if there is no valid filename in the file, then the file has a fully manual update 		
   			# put invalid filename
   					else:
   						return_type = "invalid" 
						return_value = pagepathfile   						
   						logging.info("Page %s found but filename contained invalid characters (other than whitespace)" % (pagetitle))
   	else:
   		logging.info("The page %s could not be found" % pagetitle)
   		return_type = "new"
		return_value = pagepathfile
   	return(return_type,return_value)			

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


	# get all txt files in the directory, then remove all number files
	textFiles = {}
	textFilesOnly = {}
	txpath = inputSubdir + "/*.txt"
	logging.info("txpath %s " % txpath)
	textFiles = create_file_page_list(txpath)
	for k, v in textFiles.iteritems():
		logging.info("key is %s: " % k)
		found_digits = re.search("([0-9][0-9][0-9][0-9])",k)
		if found_digits:
			logging.info("Found digits in %s " % v)
		else:	
			textFilesOnly[k] = v
			logging.info("No digits in %s" % v)
	return(oneFiles,licenseFiles,textFilesOnly) 



def main():
	logging.basicConfig(filename='read_files_pages.log',level=logging.DEBUG)
	logging.info("***Starting script now ***")
	# load properties file with wiki properties
	(loc,auth,server,inputSubdir) = get_properties_file()

	allFiles = {}
	licFiles = {}
	updFiles = {}
	txtFiles = {}
	nupFiles = tree()

	# retrieve the names of all the 0001 files 
	# and also the license files to add to the prohibited list
	(allFiles,licFiles,txtFiles) = get_content_file_names(inputSubdir)
	mtoken = server.confluence2.login(auth.user, auth.password)
	# retrieve the parent page where the pages will be stored and get its ID
	parentPage = get_page(auth,loc,loc.parentTitle,server,mtoken)
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
				(pagenUpdateType,pagenUpdatedPage) = check_page_mod(auth,loc,pagen,pagenPath,server,parentId,mtoken)
				if pagenUpdatedPage:
					nupFiles.setdefault(pagenUpdateType,{})[pagen] = pagenUpdatedPage
					updFiles[pagen] = pagenUpdatedPage	
		for pagenx in txtFiles:
			logging.info ("pagenx: %s " % pagenx)
			if pagenx in licFiles:
				logging.info ("Skipping page containing license - %s " % pagenx)
			else:
				pagenxPath = txtFiles[pagenx]
				(pagenxUpdateType,pagenxUpdatedPage) = check_page_mod(auth,loc,pagenx,pagenxPath,server,parentId,mtoken)
				if pagenxUpdatedPage:
					if pagenx not in allFiles:
						allFiles[pagenx] = pagenxPath	
					updFiles[pagenx] = pagenxUpdatedPage
					nupFiles.setdefault(pagenxUpdateType,{})[pagenx] = pagenxUpdatedPage
				else:
					allFiles[pagenx] = pagenxPath	

	else:
		logging.error ("Can't find the parent page %s" % loc.parentTitle)			

	# write one JSON file for each list 
	write_json_file("wiki_all_files.json.txt",allFiles)
	write_json_file("wiki_prohibited.json.txt",licFiles)
	write_json_file("wiki_update.json.txt",updFiles)
	write_json_file("wiki_nup.json.txt",nupFiles)



# Calls the main() function
if __name__ == '__main__':
	main()

