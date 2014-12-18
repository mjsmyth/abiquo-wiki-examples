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
	

def create_update_page(wikAuth,wikLoc,force,pagetitle,newcontent,server,parentId):
	# create or update pages as appropriate
	token = server.confluence2.login(wikAuth.user, wikAuth.password)
	alt_filename = ""
	gotpage = get_page(wikAuth,wikLoc,pagetitle,server)

	if gotpage:
		# check if the page in Confluence is the 0001 file - and if not, get the file for the different page
		pgcontent = gotpage['content']
		filename_searchstring = pagetitle + "\.([0-9][0-9][0-9][0-9])\.txt"
		# if there is a filename on the page
		fnm = re.search(filename_searchstring,pgcontent)
		print "fnm: %s " % fnm.group(0)
		if fnm:
			if fnm.group(1) == "0001":
				modifier = gotpage['modifier']
				if modifier != wikAuth.user:
				#	print "The page %s was manually modified by %s" % (modifier,pagetitle)
					logging.info("The page %s was manually modified by %s" % (modifier,pagetitle))
					if force is True:
						logging.info("Forced overwrite of page %s, modified by %s" % (modifier,pagetitle))
						#  	print "Forced overwrite of page %s, modified by %s" % (modifier,pagetitle)
						gotpage['content'] = newcontent
						token = server.confluence2.login(wikAuth.user, wikAuth.password)
						server.confluence2.storePage(token, gotpage) 			   	
					else:
					#	print "Not overwriting page %s, modifed by %s" % (modifier,pagetitle)
						logging.info("Not overwriting page %s, modifed by %s" % (modifier,pagetitle))  
				else:
					logging.info("Page has not been manually modified, overwriting page %s" % (pagetitle))
					# print "Overwriting page %s" % (pagetitle)	
					gotpage['content'] = newcontent	
					token = server.confluence2.login(wikAuth.user, wikAuth.password) 		
					server.confluence2.storePage(token, gotpage)
			else:	
				alt_filename = fnm.group(0)
				logging.info("The page: %s uses file: %s " % (pagetitle,alt_filename))
			  	# if group 1 is not 0001, use the alternative filename
		else:
		# if there is no valid filename in the file, then the file has a manual update 		
   		# don't overwrite it
   			logging.info("The page: %s has been manually modified and will not be updated" % pagetitle)

   	else:
		print "Creating new page %s" % (pagetitle)
		logging.info ("Creating new page %s" % (pagetitle))
		newpage = {}
	#	print "parentId: %s" % (parentId)
		newpage['space'] = wikLoc.spaceKey
		newpage['parentId'] = parentId
		newpage['title'] = pagetitle
		newpage['content'] = newcontent

		token = server.confluence2.login(wikAuth.user, wikAuth.password)
		server.confluence2.storePage(token, newpage)
   		# create a new page

def trim_file_glob(globPath):
	pathfiles = glob.glob(globPath)
	pgnames = []
	for pff in pathfiles:
		pf_path, pf = os.path.split(pff)
		ffpg = pf.split(".")
		fpg = ffpg[0]
		pgnames.append(fpg)
		logging.info("Full file path: %s and page name: %s " % (pff,fpg))
	return(pathfiles,pgnames)

def get_content_file_names(inputSubdir):
	# read all number 0001 pages in the directory
	# mypath = "big/*.0001.txt"
	# # get the files and only take the first part of the name without the 0001.txt
	pagenames = []
	mypath = inputSubdir + "/*.0001.txt"
	print "mypath %s " % mypath
	(onlyfiles,pagenames) = trim_file_glob(mypath)

	# read all the license files in the directory to avoid them
	licpagenames = []
	licpath = inputSubdir + "/*license*"
	print "licpath %s " % licpath
	(licfiles,licpagenames) = trim_file_glob(licpath)
	return(onlyfiles,pagenames,licfiles,licpagenames)



def main():
	logging.basicConfig(filename='confluence_update_examples.log',level=logging.DEBUG)
	# load properties file with wiki properties
	(loc,auth,force,server,inputSubdir) = get_properties_file()
	# retrieve the parent page where the pages will be stored and get its ID
	parentPage = get_page(auth,loc,loc.parentTitle,server)

	if parentPage:
	# I don't know how to handle this exception properly 
	# because if the parent page doesn't exist, it's different to if a normal page doesn't exist
		parentId = parentPage['id']
	# retrieve the content of the files to create as pages
		(filenames,pgenames,licfilenames,licpgnames) = get_content_file_names(inputSubdir)
		for idx, pagen in enumerate(pgenames):
			print "pagen: %s " % pagen
			if 'license' in pagen:
				logging.info ("Skipping page containing license - %s " % pagen)
			else:	
				ncf = open(filenames[idx],'r')	
				newcontent = ncf.read()
				# create or update pages
				try:
					create_update_page(auth,loc,force,pagen,newcontent,server,parentId)
				except:
					logging.warning ("Could not update page - %s " % pagen)
				ncf.close()
	else:
		logging.warning ("Can't find the parent page %s" % loc.parentTitle)			
# Calls the main() function
if __name__ == '__main__':
	main()

