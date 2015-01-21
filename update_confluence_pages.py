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

class outFileRecord:
	def __init__(self,apageName,afileName,aoutType):
		self.pageName = apageName
		self.fileName = afileName
		self.outType = aoutType


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

def open_if_not_existing(filename):
	try:
		fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
	except:
		logging.error("File: %s already exists" % filename)
		return None
	fobj = os.fdopen(fd, "w")
	return fobj


def write_json_file(filename,jsondict,sbdir):
	# open if not existing
	fnp = os.path.join(sbdir,filename)
	jsf = open(fnp,"w")
#	jsf = open_if_not_existing(fnp)
	# dump json
	if jsf:
		json.dump(jsondict, jsf)
		jsf.close

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
	adminSubdir = properties['adminSubdir']

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
	return (wloc,wauth,server,subdir,adminSubdir,propd)

def get_updates_file(w_file,sd):
	# Load a json file 
	file_dict = {}
	work_file = os.path.join(sd,w_file)
	with open(work_file) as wfile:
		wk_file = wfile.read().replace('\n', '')	
		wk_file = wk_file.replace('\t', " ")
		file_dict = yaml.load(wk_file)
		logging.info("Work_file: %s " % work_file)
		for ix, ick in enumerate(file_dict):
			logging.debug("%d: %s - %s" % (ix,ick,file_dict[ick]))
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
	

def create_update_page(wikAuth,wikLoc,pagtitle,ncontent,server,parentId,filea):
# create or update pages as appropriate
	logging.info("PAGE: %s " % pagtitle)
	gotpage = get_page(wikAuth,wikLoc,pagtitle,server)
	if gotpage:
		logging.info("::Exists" )
		gotpage['content'] = ncontent
		oftype = "updated"	
   	else:
		logging.info("::Create" )
		oftype = "created"
		gotpage = {}
	#	print "parentId: %s" % (parentId)
		gotpage['space'] = wikLoc.spaceKey
		gotpage['parentId'] = parentId
		gotpage['title'] = pagtitle
		gotpage['content'] = ncontent
	try:
		token = server.confluence2.login(wikAuth.user,wikAuth.password)
		server.confluence2.storePage(token, gotpage)
	except xmlrpclib.Fault as err:
		oftype = "failed"
		oFiles[oftype][pagtitle] = filea
		logging.error("::::Create or update ")
		logging.error("Confluence fault code: %d and string: %s " % (err.faultCode,err.faultString))	
	return oftype

def open_content_file(subdir,content_file_page,content_file_name):
	c_file_name = os.path.join(subdir,content_file_name)
	logging.info("c_file_name: %s " % c_file_name)
	newc = ""
	try: 
		ncf = open(c_file_name,'r')	
		newc = ncf.read()
		logging.info("Read content file okay")
		ncf.close()
	except:
		logging.info("Could not open content file %s " % c_file_name)
	return newc

def process_page(pageNa,fileNa,subDi,prohibFiles,validRest,aut,lo,serverConfl,idParent):
	if pageNa in prohibFiles:
		# skip license and other prohibited files
		logging.info("Skipping prohibited page - %s " % pageNa)
	else:
		page_rest = pageNa.split("_") 
		if page_rest:
			if page_rest[0] not in validRest:
				logging.warning("File name is not valid rest option - %s " % pageNa)
			else:	
#				cfp = os.path.join(subDi,fileNa)
#				logging.info("Opening file: %s" % cfp)	
				nc = ""
				nc = open_content_file(subDi,pageNa,fileNa)
				if nc:
					otype = create_update_page(aut,lo,pageNa,nc,serverConfl,idParent,fileNa)
				else:
					otype = "errorfile"
					logging.info("Invalid file: %s " % fileNa)
					# create or update pages
	return otype				

def main():
	logging.basicConfig(filename='update_pages.log',level=logging.DEBUG)
	# load properties file with wiki properties
	prop = {}
	(loc,auth,cserver,subdir,adminSubdir,prop) = get_properties_file()

	# retrieve the parent page where the pages will be stored and get its ID
	valid_rest = ['GET','DELETE','OPTIONS','PUT','POST']
	default_options = ['original','alternative','custom','new']
	parentPage = get_page(auth,loc,loc.parentTitle,cserver)

	if parentPage:
	# I don't know how to handle this exception properly 
	# because if the parent page doesn't exist, it's different to if a normal page doesn't exist
		parentId = parentPage['id']
	# retrieve the content of the files to create as pages
		all_files = get_updates_file("wiki_all_files.json.txt",adminSubdir)
		upd_files = get_updates_file("wiki_update.json.txt",adminSubdir)
		not_files = get_updates_file("wiki_prohibited.json.txt",adminSubdir)
		nup_files = get_updates_file("wiki_options_update.json.txt",adminSubdir)

		outfiletype = ""
		outFiles = tree()

		if prop['rewriteAll']:
#			overwrite all pages without any further considerations but don't create license files
			for pagen in all_files:
				filen = all_files[pagen]
			# pagen is the page name
				outfiletyype = process_page(pagen,filen,subdir,not_files,valid_rest,auth,loc,cserver,parentId)
				outFiles[outfiletype][pagen]=filen

		elif prop['updateAll']:
#			read updates file
#			update all pages using the default options
			for option in nup_files:
				logging.info("File: %s" % option)
				if option in default_options:
					for pagen in nup_files[option]:	
						filen = nup_files[option][pagen]
						outfiletype = process_page(pagen,filen,subdir,not_files,valid_rest,auth,loc,cserver,parentId)
						outFiles[outfiletype][pagen] = filen
				else:								
					logging.info("By default %s is not updated" % option)

		else:
#			read updates file
#			update according to the options set by user
			logging.info("Processing user options")
			for option in nup_files:
				logging.info("File option: %s" % option)
				if prop[option]:
					logging.info("Group: %s" % option)
					for pagen in nup_files[option]:	
						logging.info("File: %s" % pagen)
						filen = nup_files[option][pagen]
						outfiletype = process_page(pagen,filen,subdir,not_files,valid_rest,auth,loc,cserver,parentId)	
						outFiles[outfiletype][pagen] = filen
				else:
					logging.info("Pages of type %s are not selected for update" % option)								
	else:
		logging.info("No parent page %s" % loc.parentTitle)	

	write_json_file("out_files.json.txt",outFiles,adminSubdir)

# Calls the main() function
if __name__ == '__main__':
	main()

