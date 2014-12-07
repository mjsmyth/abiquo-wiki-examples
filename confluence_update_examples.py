#!/usr/bin/python
# Read text from the first example file of each type and update or create wiki pages with the content
# Read properties file with wiki credentials and details
# Force option overwrites manually updated pages
# Compatible with: Python 2.7
# TODO: parameterise input files directory and mediatype version number
import sys, string, xmlrpclib, re, ast, glob, os
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
        sys.stdout.write('Invalid boolean property')



def get_properties_file():
	# Load properties for the script, including wiki properties that can't be stored in a public repo
	properties = {}
	with open("confluence_properties.json.txt") as pfile:
		prop_file = pfile.read().replace('\n', '')	
		properties = ast.literal_eval(prop_file)
		for ix, ick in enumerate(properties):
			print "%d: %s - %s" % (ix,ick,properties[ick])
	#	print "Abbreviation for enterprise: %s" % abbreviations["enterprise"]	
	wikiUrl = properties['wikiUrl']
	spaceKey = properties['spaceKey']
	parentTitle =  properties['parentTitle'] 
	getforce = properties['getForce']
	force = process_stringbool(getforce)
	user = properties['user']
	password = properties['password']
	wloc = wikiLoc(wikiUrl,spaceKey,parentTitle)
	server = xmlrpclib.ServerProxy(wikiUrl + '/rpc/xmlrpc')
	token = server.confluence2.login(user, password)
	wauth = wikiAuth(user,password,token)
	return (wloc,wauth,force,server)



def get_page(wikAuth,wikLoc,pageTitle,server):
# returns the page
	page = {}
	token = server.confluence2.login(wikAuth.user, wikAuth.password)	
	try:	
		page = server.confluence2.getPage(token, wikLoc.spaceKey, pageTitle)
	except xmlrpclib.Fault as err:
		print "A fault occurred"
		print "Fault code: %d" % err.faultCode
		print "Fault string: %s " % err.faultString	
	return page		
	

def create_update_page(wikAuth,wikLoc,force,pagetitle,newcontent,server,parentId):
	# create or update pages as appropriate
	token = server.confluence2.login(wikAuth.user, wikAuth.password)
	gotpage = get_page(wikAuth,wikLoc,pagetitle,server)
	if gotpage:
   		# check if another user has updated the page and don't overwrite
   		modifier = gotpage['modifier']
   		if modifier != wikAuth.user:
   			print "The page %s was manually modified by %s" % (modifier,pagetitle)
   			if force is True:
   			   	print "Overwriting page %s, modified by %s" % (modifier,pagetitle)
   			   	gotpage['content'] = newcontent
   			   	token = server.confluence2.login(wikAuth.user, wikAuth.password)
   				server.confluence2.storePage(token, gotpage) 			   	
   			else:
   				print "Not overwriting page %s, modifed by %s" % (modifier,pagetitle)  
   		else:
   			print "Overwriting page %s" % (pagetitle)	
   			gotpage['content'] = newcontent	
   			token = server.confluence2.login(wikAuth.user, wikAuth.password) 		
   			server.confluence2.storePage(token, gotpage)
   	else:
		print "Creating new page %s" % (pagetitle)
		newpage = {}
		print "parentId: %s" % (parentId)
		newpage['space'] = wikLoc.spaceKey
		newpage['parentId'] = parentId
		newpage['title'] = pagetitle
		newpage['content'] = newcontent

		token = server.confluence2.login(wikAuth.user, wikAuth.password)
		server.confluence2.storePage(token, newpage)
   		# create a new page

def get_content_file_names():
	# read all number 0001 pages in the directory
	mypath = "test_files/*.0001.txt"
#	mypath = "big/*.0001.txt"
	onlyfiles = glob.glob(mypath)
	pagenames = []

	# get the files and only take the first part of the name
	print "Only files:"
	for onff in onlyfiles:
		print "original: %s " % onff
		onff_path, onf = os.path.split(onff)
		print "trimmed: %s " % onf
		myff = onf.split(".")
		myf = myff[0]
		print "trimmed: %s " % myf
		pagenames.append(myf)
	return(onlyfiles,pagenames)

# space = page['space']
# print "space: %s " % space
# title = page['title']
# print "title: %s " % title
# content = page['content']
# print "content: %s " % content
# pageid = page['id']
# print "id: %s " % pageid

def main():
	# load properties file with wiki properties
	(loc,auth,force,server) = get_properties_file()
	# retrieve the parent page where the pages will be stored and get its ID
	parentPage = get_page(auth,loc,loc.parentTitle,server)
	parentId = parentPage['id']
	# retrieve the content of the files to create as pages
	(filenames,pagenames) = get_content_file_names()
	for idx, pagen in enumerate(pagenames):
		ncf = open(filenames[idx],'r')	
		newcontent = ncf.read()
		# create or update pages
		try:
			create_update_page(auth,loc,force,pagen,newcontent,server,parentId)
		except:
			print "oops - %s " % pagen
		ncf.close()


# Calls the main() function
if __name__ == '__main__':
	main()

