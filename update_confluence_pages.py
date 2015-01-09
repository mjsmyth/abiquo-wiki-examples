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
	def __init__(self,auser,apassword):
		self.user=auser
		self.password=apassword


class wikiLoc:
	def __init__(self,awikiUrl,aspaceKey,aparentTitle):
		self.wikiUrl=awikiUrl
		self.spaceKey=aspaceKey
		self.parentTitle=aparentTitle

class wikiProp:
	def __init__(self,arw,aup,aex,amo,aal,adu,acu,aiv):
		self.rewriteAll = arw
		self.updateAll = aup
		self.existing = aex
		self.modifier = amo
		self.alternative = aal
		self.duplicate = adu
		self.custom = acu
		self.invalid = aiv


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

	wauth = wikiAuth(user,password)
	subdir = properties['subdir']

	grw = properties['rewriteAll']
	rw = proc_strbool(grw)
	gup = properties['updateAll']
	up = proc_strbool(gup)
	gex = properties['existing']
	ex = proc_strbool(gex)	
	gmo = properties['modifier']
	mo = proc_strbool(gmo)
	gal = properties['alternative']
	al = proc_strbool(gal)
	gdu = properties['duplicate']
	du = proc_strbool(gdu)
	gcu = properties['custom']
	cu = proc_strbool(gcu)
	giv = properties['invalid']
	iv = proc_strbool(giv)
	gne = properties['new']
	ne = proc_strbool(gne)

	wprop = wikiProp(rw,up,ex,mo,al,du,cu,iv)

	return (wloc,wauth,server,subdir,wprop)

def get_updates_file(work_file):
	# Load a json file 
	file_dict = {}
	with open(work_file) as wfile:
		wk_file = wfile.read().replace('\n', '')	
		wk_file = wk_file.replace('\t', " ")
		file_dict = json.loads(wk_file)
		logging.info("Work_file: %s " % work_file)
		for ix, ick in enumerate(file_dict):
			logging.info("%d: %s - %s" % (ix,ick,file_dict[ick]))
	return file_dict

def get_page(wikAuth,wikLoc,pageTitle,server,etoken):
# returns the page
	page = {}
#	token = server.confluence2.login(wikAuth.user, wikAuth.password)	
	try:	
		page = server.confluence2.getPage(etoken, wikLoc.spaceKey, pageTitle)
	except xmlrpclib.Fault as err:
		print ("No page created")
		logging.info ("Confluence fault code: %d and string: %s " % (err.faultCode,err.faultString))
#		logging.info ("Confluence string: %s " % err.faultString)	
	return page		
	

def create_update_page(wikAuth,wikLoc,pagetitle,newcontent,server,parentId,xtoken):
	# create or update pages as appropriate
	token = server.confluence2.login(wikAuth.user, wikAuth.password)
	logging.debug("Trying to update page %s " % pagetitle)
	alt_filename = ""
	gotpage = get_page(wikAuth,wikLoc,pagetitle,server,token)

	if gotpage:
		logging.info("Found existing page %s " % pagetitle)
		# check if the page in Confluence is the 0001 file - and if not, get the file for the different page
		pgcontent = gotpage['content']
#		filename_searchstring = pagetitle + "\.([0-9][0-9][0-9][0-9])\.txt"
		# if there is a filename on the page
#		fnm = re.search(filename_searchstring,pgcontent)
#		if fnm:
		logging.info("Overwrite of page %s " % pagetitle)
		#  	print "Forced overwrite of page %s, modified by %s" % (modifier,pagetitle)
		gotpage['content'] = newcontent
#			token = server.confluence2.login(wikAuth.user, wikAuth.password)
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

#		token = server.confluence2.login(wikAuth.user,wikAuth.password)
		server.confluence2.storePage(token, newpage)
   		# create a new page


def open_content_file(subdir,content_file_page,content_file_name):
	c_file_name = os.path.join(subdir,content_file_name)
	logging.info("c_file_name: %s " % c_file_name)
	newcontent = ""
	try: 
		ncf = open(c_file_name,'r')	
		newcontent = ncf.read()
		logging.info("Read content file")
		ncf.close()
		return newcontent
	except:
		logging.info("Could not open content file %s " % c_file_name)
		return ""


def main():
	logging.basicConfig(filename='update_pages.log',level=logging.DEBUG)
	# load properties file with wiki properties
	(loc,auth,server,subdir,prop) = get_properties_file()
	itoken = server.confluence2.login(auth.user, auth.password)
	# retrieve the parent page where the pages will be stored and get its ID
	valid_rest = ['GET','DELETE','OPTIONS','PUT','POST']
	parentPage = get_page(auth,loc,loc.parentTitle,server,itoken)

	if parentPage:
	# I don't know how to handle this exception properly 
	# because if the parent page doesn't exist, it's different to if a normal page doesn't exist
		parentId = parentPage['id']
	# retrieve the content of the files to create as pages
		all_files = get_updates_file("wiki_all_files.json.txt")
		upd_files = get_updates_file("wiki_update.json.txt")
		not_files = get_updates_file("wiki_prohibited.json.txt")

		if prop.rewriteAll:
#			overwrite all pages
#			don't look at updates file
			for pagen in all_files:
			# pagen is the page name
				if pagen in not_files:
				# skip license and other prohibited files
					logging.info("Skipping page - %s " % pagen)
				else:
					page_rest = split(pagen,"_") 
					if page_rest:
						if page_rest[0] not in valid_rest:
							logging.info("File name is not valid rest - %s " % pagen)
						else:	
							filecontent = open_content_file(subdir,pagen,all_files[pagen])
							if filecontent:	
								try:
									create_update_page(auth,loc,pagen,newcontent,server,parentId,itoken)
								except:
									logging.info("Could not create or update page - %s " % pagen)
		else:							
			if prop.updateAll:
	#			read updates file
	#			update all pages using the default options
				for pagen in all_files:
				# pagen is the page name
					if pagen in not_files:
					# skip license and other prohibited files
						logging.info("Skipping page - %s " % pagen)	
					else:
						page_rest = split(pagen,"_") 
						if page_rest:
							if page_rest[0] not in valid_rest:
								logging.info("File name is not valid rest - %s " % pagen)
							else:	
								filen = ""
								fileupdate = upd_files[pagen]
								invalid = re.match(fileupdate,r'invalid')
								new = re.match(fileupdate,r'new')
								if invalid:
									logging.info("File name is invalid")
								elif new:
									filen = fileupdate	
								else:	
									irreg = re.sub(fileupdate,'custom\: |alternative\: |duplicate: ','')
#									alternative = re.sub(fileupdate,r'alternative: ')
#									duplicate = re.sub(fileupdate,r'duplicate: ')
#									if custom or alternative or duplicate:
									if irreg:
										filen = irreg
									filecontent = open_content_file(subdir,pagen,filen)
									if filecontent:	
										try:
											create_update_page(auth,loc,pagen,newcontent,server,parentId,itoken)
										except:
											logging.info("Couldn't create or update page - %s " % pagen)
									else:
										logging.info("No file content - %s " % pagen)		

			else:
#			read updates file
#			update according to the options set by user
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
								filen = ""	
								fileupdate = upd_files[pagen]
								if fileupdate:	
									filen = ""
									irreg = re.match(fileupdate,'(custom\: |alternative\: |duplicate\: |new\: |invalid: )([\w,\.]+)')
									if irreg:
										logging.info("Irreg %s " % irreg)
										update_type = irreg.group(1)
										update_file = irreg.group(2)
									# custom = re.sub(fileupdate,r'custom: ','')
									# alternative = re.sub(fileupdate,r'alternative: ','')
									# invalid = re.match(fileupdate,r'invalid')
									# new = re.sub(fileupdate,r'new: ','')	
									# duplicate = re.sub(fileupdate,r'duplicate: ','')
										if "custom" in update_type:
											if prop.custom:
												filen = update_file
										if "alternative" in update_type:
											if prop.alternative:
												filen = update_file
										if "invalid" in update_type:
											if prop.invalid:
												filen = all_files[pagen]	
										if "new" in update_type:
											if prop.new:
												filen = update_file
									else:
										logging.info("None of the irregular options apply %s " % fileupdate)
										filen = fileupdate			
									logging.info("Trying to open file %s" % filen)	
									filecontent = open_content_file(subdir,pagen,filen)
									if filecontent:	
										try:
											logging.info("Trying to create page %s " % pagen)
											create_update_page(auth,loc,pagen,newcontent,server,parentId,itoken)
										except:
											logging.info("Cannot create or update page - %s - %s " % (pagen,filen))
									else:
										logging.info("No file content - %s " % pagen)				

	else:
		logging.info("Can't find the parent page %s" % loc.parentTitle)			

# Calls the main() function
if __name__ == '__main__':
	main()

