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
import yaml

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


def tree(): return collections.defaultdict(tree)

def proc_strbool(propbool):
    try:
        return strtobool(propbool.lower())
    except ValueError:
    	logging.warning('Invalid boolean property %s' % userInput)

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
	token = server.confluence2.login(user, password)
	wauth = wikiAuth(user,password,token)

	subdir = properties['subdir']

	propd = {}
	grw = properties['rewriteAll']
	propd['rewriteAll'] = proc_strbool(grw)
	gup = properties['updateAll']
	propd['updateAll'] = proc_strbool(gup)
	gex = properties['existing']
	propd['original'] = proc_strbool(gex)	
	gmo = properties['modifier']
	propd['modifier'] = proc_strbool(gmo)
	gal = properties['alternative']
	propd['alternative'] = proc_strbool(gal)
	gdu = properties['duplicate']
	propd['duplicate'] = proc_strbool(gdu)
	gcu = properties['custom']
	propd['custom'] = proc_strbool(gcu)
	giv = properties['invalid']
	propd['invalid'] = proc_strbool(giv)
	gne = properties['new']
	propd['new'] = proc_strbool(gne)

	

	return (wloc,wauth,server,subdir,propd)

def get_updates_file(work_file):
	# Load a json file 
	file_dict = {}
	with open(work_file) as wfile:
		wk_file = wfile.read().replace('\n', '')	
		wk_file = wk_file.replace('\t', " ")
		file_dict = yaml.load(wk_file)
		logging.info("Work_file: %s " % work_file)
		for ix, ick in enumerate(file_dict):
			logging.info("%d: %s - %s" % (ix,ick,file_dict[ick]))
	return file_dict

def get_page(wikAuth,wikLoc,pageTitle,server):
# returns the page
	page = {}
	token = server.confluence2.login(wikAuth.user, wikAuth.password)	
	try:	
		page = server.confluence2.getPage(token, wikLoc.spaceKey, pageTitle)
	except xmlrpclib.Fault as err:
#		logging.info ("No page exits")
		logging.info ("Confluence fault code: %d and string: %s " % (err.faultCode,err.faultString))
#		logging.info ("Confluence string: %s " % err.faultString)	
	return page		
	

def create_update_page(wikAuth,wikLoc,pagtitle,ncontent,server,parentId):
	print ("In create_update_page for %s :" % pagtitle)
	# create or update pages as appropriate
#	token = server.confluence2.login(wikAuth.user, wikAuth.password)
	logging.info("Trying to update page %s " % pagtitle)
	alt_filename = ""
	gotpage = get_page(wikAuth,wikLoc,pagtitle,server)
	if gotpage:
		print ("Found existing page")
		logging.info("Found existing page %s " % pagtitle)
		# check if the page in Confluence is the 0001 file - and if not, get the file for the different page
		pgcontent = gotpage['content']
#		filename_searchstring = pagetitle + "\.([0-9][0-9][0-9][0-9])\.txt"
		# if there is a filename on the page
#		fnm = re.search(filename_searchstring,pgcontent)
#		if fnm:
		logging.info("Overwrite of page %s " % pagtitle)
		#  	print "Forced overwrite of page %s, modified by %s" % (modifier,pagetitle)
		gotpage['content'] = ncontent
		token = server.confluence2.login(wikAuth.user, wikAuth.password)
		server.confluence2.storePage(token, gotpage) 			   	
   	else:
		print "Creating new page %s" % (pagtitle)
		logging.info ("Trying to create new page %s" % (pagtitle))
		newpage = {}
	#	print "parentId: %s" % (parentId)
		newpage['space'] = wikLoc.spaceKey
		newpage['parentId'] = parentId
		newpage['title'] = pagtitle
		newpage['content'] = ncontent

		token = server.confluence2.login(wikAuth.user,wikAuth.password)
		server.confluence2.storePage(token, newpage)
   		# create a new page


def open_content_file(subdir,content_file_page,content_file_name):
	c_file_name = os.path.join(subdir,content_file_name)
	logging.info("c_file_name: %s " % c_file_name)
	newcontent = ""
	try: 
		ncf = open(c_file_name,'r')	
		newcontent = ncf.read()
		logging.info("Read content file okay")
		ncf.close()
		return newcontent
	except:
		logging.info("Could not open content file %s " % c_file_name)
		return ""


def main():
	logging.basicConfig(filename='update_pages.log',level=logging.DEBUG)
	# load properties file with wiki properties
	prop = {}
	(loc,auth,cserver,subdir,prop) = get_properties_file()

	# retrieve the parent page where the pages will be stored and get its ID
	valid_rest = ['GET','DELETE','OPTIONS','PUT','POST']
	parentPage = get_page(auth,loc,loc.parentTitle,cserver)

	if parentPage:
	# I don't know how to handle this exception properly 
	# because if the parent page doesn't exist, it's different to if a normal page doesn't exist
		parentId = parentPage['id']
	# retrieve the content of the files to create as pages
		all_files = get_updates_file("wiki_all_files.json.txt")
		upd_files = get_updates_file("wiki_update.json.txt")
		not_files = get_updates_file("wiki_prohibited.json.txt")
		nup_files = get_updates_file("wiki_nup.json.txt")

		if prop['rewriteAll'] == True:
#			overwrite all pages
#			don't look at updates file
			for pagen in all_files:
			# pagen is the page name
				if pagen in not_files:
				# skip license and other prohibited files
					logging.info("Skipping page - %s " % pagen)
				else:
					page_rest = pagen.split("_") 
					if page_rest:
						if page_rest[0] not in valid_rest:
							logging.info("File name is not valid rest - %s " % pagen)
						else:	
							cf = all_files[pagen]
							cfp = os.path.join(subdir,cf)
							ncf = open(cfp,'r')	
							newcontent = ncf.read()
							# create or update pages
							try:
								create_update_page(auth,loc,pagen,newcontent,cserver,parentId)
							except:
								logging.warning ("Could not update page - %s " % pagen)
							ncf.close()
		elif prop['updateAll'] == True:
#			read updates file
#			update all pages using the default options
			for option in nup_files:
				for pgnup in nup_files[option]:	
					filenup = nup_files[option][pgnup]
					if pgnup in not_files:
					# skip license and other prohibited files
						logging.info("Skipping page - %s " % pagen)	
					else:
						page_rest = pgnup.split("_") 
						if page_rest:
							if page_rest[0] not in valid_rest:
								logging.info("File name is not valid rest - %s " % pgnup)
							else:
								logging.info("Trying to open file %s" % filenup)	
								filecontent = open_content_file(subdir,pgnup,filenup)
								if filecontent:	
									try:
										logging.info("Trying to create page %s " % pgnup)
										create_update_page(auth,loc,pgnup,filecontent,cserver,parentId)
									except:
										logging.info("Cannot create or update page - %s - %s " % (pgnup,filenup))
								else:
									logging.info("No file content - %s " % pagnup)			

		else:
#			read updates file
#			update according to the options set by user
			for option in nup_files:
				for pgnup in nup_files[option]:	
					if prop[option] == True:
						filenup = nup_files[option][pgnup]
						if pgnup in not_files:
						# skip license and other prohibited files
							logging.info("Skipping page - %s " % pagen)	
						else:
							page_rest = pgnup.split("_") 
							if page_rest:
								if page_rest[0] not in valid_rest:
									logging.info("File name is not valid rest - %s " % pgnup)
								else:
									logging.info("Trying to open file %s" % filenup)	
									filecontent = open_content_file(subdir,pgnup,filenup)
									if filecontent:	
										try:
											logging.info("Trying to create page %s " % pgnup)
											create_update_page(auth,loc,pgnup,filecontent,cserver,parentId)
										except:
											logging.info("Cannot create or update page - %s - %s " % (pgnup,filenup))
									else:
										logging.info("No file content - %s " % pagnup)				

	else:
		logging.info("Can't find the parent page %s" % loc.parentTitle)			

# Calls the main() function
if __name__ == '__main__':
	main()

