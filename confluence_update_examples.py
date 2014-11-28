#!/usr/bin/python

import sys, string, xmlrpclib, re
from distutils.util import strtobool

def user_yes_no_query(question):
    sys.stdout.write('%s [y/n]\n' % question)
    while True:
        try:
            return strtobool(raw_input().lower())
        except ValueError:
            sys.stdout.write('Please respond with \'y\' or \'n\'.\n')

class wikiAuth:
	def __init__(auser,apassword,atoken):
		self.user=auser
		self.password=apassword
		self.token=atoken

class wikiLoc:
	def __init__(awikiUrl,aspaceKey,aparentTitle):
		self.wikiUrl=awikiUrl
		self.spaceKey=aspaceKey
		self.token=aparentTitle

	# def string_admin(self):
	# 	wiki_label = self.label
	# 	wiki_internal_message_id = self.internal_message_id.strip("\"")
	# 	wiki_message = dowikimarkup(self.message)        
	# 	return '| %s | %s | %s | | \n' % (wiki_internal_message_id, wiki_message, wiki_label)

def user_yes_no_query(question):
    sys.stdout.write('%s [y/n]\n' % question)
    while True:
        try:
            return strtobool(raw_input().lower())
        except ValueError:
            sys.stdout.write('Please respond with \'y\' or \'n\'.\n')
def process_stringbool(getForce):
    try:
        return strtobool(getForce.lower())
    except ValueError:
        sys.stdout.write('Invalid boolean property')

def get_sysargs():
	if len(sys.argv) < 4:
	   exit("Usage: " + sys.argv[0] + "  wikiUrl spaceKey parentPageTitle [--force]")
	input = "".join(sys.stdin.readlines()).rstrip()
	wikiUrl = sys.argv[1]
	spaceKey = sys.argv[2]
	parentTitle = sys.argv[3]
	force = user_yes_no_query("Overwrite manually edited examples?")
	user = raw_input("Enter user: ")
	password = raw_input("Enter password: ")
	wloc = wikiLoc(wikiUrl,spaceKey,parentTitle)
	token = server.confluence2.login(user, password)
	wauth = wikiAuth(user,password,token)
	return (wloc,wauth,force)

def get_std_in():
 	wikiUrl = raw_input("Enter wiki URL + port with no proxy or trailing slash: ")
	spaceKey = raw_input("Enter space key of wiki space: ")
	parentTitle = raw_input("Enter title of parent page: ")
	force = user_yes_no_query("Overwrite manually edited examples?")
	user = raw_input("Enter user: ")
	password = raw_input("Enter password: ")
	wloc = wikiLoc(wikiUrl,spaceKey,parentTitle)
	token = server.confluence2.login(user, password)
	wauth = wikiAuth(user,password,token)
	return (wloc,wauth,force)

def get_properties_file():
	# Load a bunch of abbreviations to replace text and shorten links
	properties = {}
	with open("confluence_properties.json.txt") as pfile:
		prop_file = pfile.read().replace('\n', '')	
		properties = ast.literal_eval(prop_file)
	#	print "Abbreviation for enterprise: %s" % abbreviations["enterprise"]	
	wikiUrl = properties['wikiUrl']
	spaceKey = properties['spaceKey']
	parentTitle = properties['parentTitle']
	getforce = properties['getForce']
	user = properties['user']
	password = properties['password']
	wloc = wikiLoc(wikiUrl,spaceKey,parentTitle)
	token = server.confluence2.login(user, password)
	wauth = wikiAuth(user,password,token)
	return (wloc,wauth,force)

def get_parent_id(wikAuth,wikLoc):
# returns the ID of the parent page	
	page = {}	
	server = xmlrpclib.ServerProxy(wikiurl + '/rpc/xmlrpc')
	try:
		page = server.confluence2.getPage(wikAuth.token, wikLoc.spaceKey, wikLoc.parentTitle)
	except xmlrpclib.Fault as err:
		print "A fault occurred"
		print "Fault code: %d" % err.faultCode
		print "Fault string: %s " % err.faultString	
	if page:
		parentId = page['parentId']		
		return parentId
	else:
		exit("Could not find parent page " + spacekey + ":" + pagetitle)	

def create_update_page(wikAuth,wikLoc,force,page):
	server = xmlrpclib.ServerProxy(wikiurl + '/rpc/xmlrpc')
	getpage = {}
	pagetitle = page['title']
	try:
		getpage = server.confluence2.getPage(wikAuth.token, wikLoc.spaceKey, pagetitle)
	except xmlrpclib.Fault as err:
		print "A fault occurred"
		print "Fault code: %d" % err.faultCode
		print "Fault string: %s " % err.faultString	
	if getpage:
   		# check if another user has updated the page and don't overwrite
   		modifier = getpage['modifier']
   		if modifier != wikAuth.user:
   			print "The page %s was manually modified by %s" % (modifier,pagetitle)
   			if force is True:
   			   	print "Overwriting page %s, modified by %s" % (modifier,pagetitle)
   			else:
   				print "Not overwriting page %s, modifed by %s" % (modifier,pagetitle)  
   		else:
   			print "Overwriting page %s" % (modifier,pagetitle)		 		
   			server.confluence2.storePage(token, page);
   	else:
		print "Creating new page %s" % (pagetitle)
		server.confluence2.storePage(token, page);
   		# create a new page

# space = page['space']
# print "space: %s " % space
# title = page['title']
# print "title: %s " % title
# content = page['content']
# print "content: %s " % content
# pageid = page['id']
# print "id: %s " % pageid


# newpage = {"space": "WST","title": "second test", "content":"<p>Hello multiverse!</p>"}
# newpage['parentId'] = pageid
# server.confluence2.storePage(token, newpage);


def main():
	(loc,auth,force) = get_properties_file()
	parentId = get_parent_id(auth,loc)
	page = get_page_data(contentFile, parentId)
	create_update_page(auth,loc,force,page)

# Calls the main() function
if __name__ == '__main__':
	main()

