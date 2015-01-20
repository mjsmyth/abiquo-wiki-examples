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
    	logging.warning('Invalid boolean property %s' % propbool)

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
	gex = properties['original']
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
# create or update pages as appropriate
#	token = server.confluence2.login(wikAuth.user, wikAuth.password)
	logging.info("PAGE: %s " % pagtitle)
	alt_filename = ""
	gotpage = get_page(wikAuth,wikLoc,pagtitle,server)
	if gotpage:
		logging.info("::Exists" )
		# check if the page in Confluence is the 0001 file - and if not, get the file for the different page
		pgcontent = gotpage['content']
#		filename_searchstring = pagetitle + "\.([0-9][0-9][0-9][0-9])\.txt"
		# if there is a filename on the page
#		fnm = re.search(filename_searchstring,pgcontent)
#		if fnm:
		logging.info("::Overwrite ")
		#  	print "Forced overwrite of page %s, modified by %s" % (modifier,pagetitle)
		gotpage['content'] = ncontent
		token = server.confluence2.login(wikAuth.user, wikAuth.password)
		server.confluence2.storePage(token, gotpage) 			   	
   	else:
		logging.info("::Create" )
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
		with open(c_file_name,'r') as ncf:	
			newcontent = ncf.read()
		logging.info("Read file: %s" % c_file_name)	
		return newcontent
	except:
		logging.info("File error %s " % c_file_name)
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

		if prop['rewriteAll']:
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
							logging.warning("File name is not valid rest option - %s " % pagen)
						else:	
							cf = all_files[pagen]
#							cfp = os.path.join(subdir,cf)
							newcontent = ""
							logging.info("Opening file: %s" % cfp)	
							newcontent = open_content_file(subdir,pagen,cf)
							if newcontent:
								try:
									create_update_page(auth,loc,pagen,newcontent,cserver,parentId)
								except:
									logging.error ("Error page: %s " % pagen)
							else:
								logging.info("Invalid file: %s " % cf)
								continue				
							# create or update pages


		elif prop['updateAll']:
#			read updates file
#			update all pages using the default options
			for option in nup_files:
				logging.info("File: %s" % option)
				for pgnup in nup_files[option]:	
					filenup = nup_files[option][pgnup]
					if pgnup in not_files:
					# skip license and other prohibited files
						logging.info("Skipping: %s " % pgnup)	
					else:
						page_rest = pgnup.split("_") 
						if page_rest:
							if page_rest[0] not in valid_rest:
								logging.warning("File name is not valid rest - %s " % pgnup)
							else:
								logging.info("Opening file: %s" % filenup)	
								filecontent = open_content_file(subdir,pgnup,filenup)
								if filecontent:	
									try:
										logging.info("Update page: %s " % pgnup)
										create_update_page(auth,loc,pgnup,filecontent,cserver,parentId)
									except:
										logging.info("Error page: - %s - %s " % (pgnup,filenup))
								else:
									logging.info("Invalid file: %s " % filenup)		
									continue	

		else:
#			read updates file
#			update according to the options set by user
			logging.info("Processing user options")
			for option in nup_files:
				logging.info("File option: %s" % option)
				if prop[option]:
					logging.info("Group: %s" % option)
					for pnup in nup_files[option]:	
						logging.info("File: %s" % pnup)
						filenup = nup_files[option][pnup]
						if pnup in not_files:
						# skip license and other prohibited files
							logging.info("Skipping: - %s " % pnup)	
						else:
							page_rest = pnup.split("_") 
							if page_rest:
								if page_rest[0] not in valid_rest:
									logging.warning("File name is not valid rest - %s " % pnup)
								else:	
									logging.info("Opening file: %s" % filenup)	
									filecontent = open_content_file(subdir,pnup,filenup)
									if filecontent:	
#									cfp = os.path.join(subdir,filenup)
#									ncf = open(cfp,'r')	
#									newcontent = ncf.read()
									# create or update pages
										try:
											logging.info("Update page: %s " % pnup)
											create_update_page(auth,loc,pnup,filecontent,cserver,parentId)
										except:
											logging.warning ("Page error: %s " % pnup)
									else:
										logging.info("Invalid file: %s " % filenup)			
										continue		
	else:
		logging.info("No parent page %s" % loc.parentTitle)			

# Calls the main() function
if __name__ == '__main__':
	main()

