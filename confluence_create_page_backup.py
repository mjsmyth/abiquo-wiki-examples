#!/usr/bin/python
# http://mattryall.net/blog/2008/06/confluence-python 
import sys, string, xmlrpclib, re
import os
import glob
import cgi

if len(sys.argv) < 4:
   exit("Usage: " + sys.argv[0] + " spacekey myuser mypassword");

#input = "".join(sys.stdin.readlines()).rstrip();
spacekey = sys.argv[1];
myuser = sys.argv[2];
mypassword = sys.argv[3];

server = xmlrpclib.ServerProxy('http://wiki.abiquo.com/rpc/xmlrpc');
token = server.confluence2.login(myuser,mypassword);

# read all number 0001 pages in the directory
mypath = "selected_files/*.0001.txt"

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


for idx, pagen in enumerate(pagenames):
	# check if the page exists and if it does, edit it
	page = server.confluence2.getPage(token, spacekey, pagen);
	ncf = open(onlyfiles[idx],'r')	
	newcontent = ncf.read()
	ncf.close()
	print ("newcontent")
	if page is None:
		exit("Could not find page " + spacekey + ":" + pagetitle);
		# create new page
	else:
		print page['content']
		page['content'] = newcontent
#		server.confluence2.storePage(token, page);
#	ncf.close()
# = open('login_get_format.txt','r')
#input = f.read()
#pattern = re.compile('^\|\|.*\n(?!\|)', re.MULTILINE);



#replaceCode = re.compile (r"\[CDATA\[(.*)\]\]");
#replaced = re.sub(replaceCode, "[CDATA[%s]]" % input, content);
#content = replaced;
#print content;
#page['content'] = content;

#f.close()
# otherwise create the page
