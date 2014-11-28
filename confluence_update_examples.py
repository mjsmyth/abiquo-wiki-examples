#!/usr/bin/python

import sys, string, xmlrpclib, re


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

def get_sysargs():
	if len(sys.argv) < 4:
	   exit("Usage: " + sys.argv[0] + "  wikiUrl spaceKey parentPageTitle [--force]")
	input = "".join(sys.stdin.readlines()).rstrip()
	wikiUrl = sys.argv[1]
	spaceKey = sys.argv[2]
	parentTitle = sys.argv[3]
	# if force, overwrite manually edited examples
	if len(sys.arg) > 4:
		getforce = sys.argv[4]
		force = strtobool(getforce)
	# handle error	

def get_inputs():
 	wikiUrl = raw_input("Enter wiki URL + port with no proxy or trailing slash: ")
	spaceKey = raw_input("Enter space key of wiki space: ")
	parentTitle = raw_input("Enter title of parent page: ")
	forceInput = raw_input("Force update of manually edited pages? ")
	force = strtobool(forceInput)
	# handle error
	user = raw_input("Enter user: ")
	password = raw_input("Enter password: ")
	wloc = wikiLoc(wikiUrl,spaceKey,parentTitle)
	token = server.confluence2.login(user, password)
	wauth = wikiAuth(user,password,token)

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
	# Check if this will work	
		parentId = page['parentId']		
		return parentId
	else:
		exit("Could not find page " + spacekey + ":" + pagetitle)	

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
   				
   			   	print "Overwriting page %s, which was manually modified by %s" % (modifier,pagetitle)	
   	else:

   		# create a new page

space = page['space']
print "space: %s " % space
title = page['title']
print "title: %s " % title
content = page['content']
print "content: %s " % content
pageid = page['id']
print "id: %s " % pageid


newpage = {"space": "WST","title": "second test", "content":"<p>Hello multiverse!</p>"}
newpage['parentId'] = pageid
server.confluence2.storePage(token, newpage);
#pattern = re.compile('^\|\|.*\n(?!\|)', re.MULTILINE);
#content = pattern.sub('\g<0>' + input + '\n', content);


#replaceCode = re.compile (r"\[CDATA\[(.*)\]\]");
#replaced = re.sub(replaceCode, "[CDATA[%s]]" % input, content);
#content = replaced;
#print content;
#page['content'] = content;

def main():
	get_inputs()


# Calls the main() function
if __name__ == '__main__':
	main()

