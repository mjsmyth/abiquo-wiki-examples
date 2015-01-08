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

def get_updates_file(update_file):
	# Load properties for the script, including wiki properties that can't be stored in a public repo
	updates = {}
	with open(update_file) as ufile:
		upda_file = ufile.read().replace('\n', '')	
		upda_file = upda_file.replace('\t', " ")
		updates = json.loads(upda_file)
		logging.info("Update_file: %s " % update_file)
		for ix, ick in enumerate(updates):
			logging.info("%d: %s - %s" % (ix,ick,updates[ick]))
	return updates

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
	

def create_update_page(wikAuth,wikLoc,pagetitle,newcontent,server,parentId):
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
		if fnm:
			logging.info("Overwrite of page %s " % pagetitle)
			#  	print "Forced overwrite of page %s, modified by %s" % (modifier,pagetitle)
			gotpage['content'] = newcontent
			token = server.confluence2.login(wikAuth.user, wikAuth.password)
			server.confluence2.storePage(token, gotpage) 			   	
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


def main():
	logging.basicConfig(filename='update_pages.log',level=logging.DEBUG)
	# load properties file with wiki properties
	(loc,auth,force,server,inputSubdir) = get_properties_file()
	# retrieve the parent page where the pages will be stored and get its ID

	parentPage = get_page(auth,loc,loc.parentTitle,server)

	if parentPage:
	# I don't know how to handle this exception properly 
	# because if the parent page doesn't exist, it's different to if a normal page doesn't exist
		parentId = parentPage['id']
	# retrieve the content of the files to create as pages
		all_files = get_updates_file("wiki_all_files.json.txt")
		upd_files = get_updates_file("wiki_force_update.json.txt")
		not_files = get_updates_file("wiki_prohibited.json.txt")
		for pagen in all_files:
			print "pagen: %s " % pagen
			if pagen in not_files:
				logging.info("Skipping page - %s " % pagen)
			elif pagen in upd_files:
				logging.info("Updating modified page - %s " % pagen)	
				logging.info("Details of modification are - %s " % all_files[pagen])
				ncf = open(all_files[pagen],'r')	
				newcontent = ncf.read()
				# create or update pages
				try:
					create_update_page(auth,loc,pagen,newcontent,server,parentId)
				except:
					logging.info("Could not update page - %s " % pagen)
				ncf.close()
			else:
				logging.info("Regular page %s " % pagen)				
	else:
		logging.info("Can't find the parent page %s" % loc.parentTitle)			

# Calls the main() function
if __name__ == '__main__':
	main()

