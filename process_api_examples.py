#!/usr/bin/python2 -tt
# Process API examples for the wiki
# Read the IT tests log file
# Identify the requests with status 204 or 200
# Create a file name by replacing numbers and long bits of the URL
# Save the requests with a nominal invented curl, status code and request and response payload
# Writes a file with storage format


import json
import yaml
import ast
import re
import xml.dom.minidom
import os
import cgi
from lxml import etree
from StringIO import StringIO
from io import BytesIO
import logging
import sys
import pystache
from distutils.util import strtobool


class allheaders:
	def __init__(self,aRequestAccept,aRequestContentType,aResponseContentType):
		self.reqAc=aRequestAccept
		self.reqCT=aRequestContentType
		self.rspCT=aResponseContentType

	def hprint(self):
#		print "self.reqAc: %s  self.reqCT: %s  self.rspCT %s " % (self.reqAc,self.reqCT,self.rspCT)			
		logging.debug ("self.reqAc: %s  self.reqCT: %s  self.rspCT %s " % (self.reqAc,self.reqCT,self.rspCT))
 
# class example:
# 	def __init__(self,afName,acurl,astatus,arequestData,aresponseData):
# 		self.fName = afName
# 		self.curl = acurl 
# 		self.status = astatus
# 		self.requestData = arequestData
# 		self.responseData = aresponseData

def print_line(line):
	request = yaml.load(line)
#	request = json.loads(line)
	print "Method: %s" % request['method'] # string
	print "URL: %s" % request['url'] # string
	print "Status: %s" % request['status'] # int
	print "Request headers: %s" % request['request_headers'] # It's a JSON dictionary
	print "Response headers: %s" % request['response_headers'] # It's a JSON dictionary
	print "Request payload: %s" % request['request_payload'] # A JSON or an XML, inspect request Content-Type header
	print "Response payload: %s" % request['response_payload']  # A JSON or an XML, inspect response Content-Type header



def open_if_not_existing(filenam):
	try:
		fd = os.open(filenam, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
		fobj = os.fdopen(fd,"w")
		return fobj
	except:
		logging.warning("File: %s already exists" % filenam)
		return None

def open_to_overwrite(fna):
	try:	
		fob = open(fna, "w")
		return fob
	except:
		logging.warning("Can't open: %s" % fna)
		return None
	

# def proc_strbool(userInput):
#     try:
#         return strtobool(userInput.lower())
#     except ValueError:
#     	logging.warning('Invalid boolean property %s' % userInput)
#         sys.stdout.write('Invalid boolean property')


def get_properties_file():
	# Load properties for the scripts, including wiki properties that can't be stored in a public repo
	properties = {}
	with open("confluence_properties.json.txt") as pfile:
		prop_file = pfile.read().replace('\n','')	
		prop_file = prop_file.replace('\t'," ")
		print ("prop_file %s " % prop_file)
		properties = json.loads(prop_file)
		for ick in (properties):
			logging.info("Property: %s : %s " % (ick,properties[ick]))
		template = properties['template']	
		adminSubdir = properties['adminSubdir']
		subdir = properties['subdir']
		rawLog = properties['rawLog']
		MTversion = properties['MTversion']
		# previously used strtobool for overwritefiles, now just automatically overwrites files
		return (subdir,rawLog,MTversion,adminSubdir,template)


def create_file_name(line,abbreviations,hdrs):
#	request = json.loads(line)
	request = yaml.load(line)
	example_file_name = ""
	raw_url = request['url']
	raw_method = request['method']
	req_acc = sub_media_type(hdrs.reqAc)
	req_ct = sub_media_type(hdrs.reqCT)
	rsp_ct = sub_media_type(hdrs.rspCT)
	rep_url_list = []
	logging.info("Raw_url: %s" % raw_url)
	#print "Raw_url: %s" % raw_url
	raw_url_list = raw_url.split("/")
	for ruli in raw_url_list[2:]:
		ruli = rep_text(ruli,abbreviations)
		rep_url_list.append(ruli)
	method = rep_text(raw_method,abbreviations)	
	example_file_name = raw_method + "_" + "_".join(rep_url_list) 
	if req_ct:
		req_ct = rep_abbrev(req_ct,abbreviations)
		example_file_name = example_file_name + "_CT_" + req_ct 
	if rsp_ct:
		rsp_ct = rep_abbrev(rsp_ct,abbreviations)
		example_file_name = example_file_name + "_AC_" + rsp_ct	
	rep_qp_list = []	
	if request['query_params']:
		query_params = request['query_params']
		qpl = query_params.split("&")
		for qidx, qp in enumerate(qpl):
			if qp:
				qpValuelist = qp.split("=")
				qpName = qpValuelist[0]
				logging.debug("qpName: %s" % qpName)
				qpValue = qpValuelist[1]
				logging.debug("qpValue: %s " % qpValue)
				repQpName = rep_abbrev(qpName,abbreviations)
				rep_qp_list.append(repQpName)
				if qpValue == "true":
					rep_qp_list.append('T')
				if qpValue == "false":
					rep_qp_list.append('F')
				if qpName == "by":
					rep_qp_list.append(qpValue)	
	if rep_qp_list:			
		example_file_name = example_file_name + "_" + "_".join(rep_qp_list)			
	return example_file_name


def rep_abbrev(text,abbreviations):
	for abbi, abbr in iter(sorted(abbreviations.iteritems(),reverse=True)):
		text = text.replace(abbi,abbr)
		text = re.sub("\*/\*","any",text)
		text = re.sub("/","_",text)	
		text = re.sub ("\.","_",text)
	return text	


def rep_text(text,abbreviations):
	for abbi, abbr in iter(sorted(abbreviations.iteritems(),reverse=True)):
		text = text.replace(abbi,abbr)
# If it's a storage pool or a task name		
	if "-" in text:
		text = "X"	
# If it's an ID 	
	if re.match("[0-9]",text):
		text = "X"
# If it's an entity with an underscore as an ID, e.g., request all enterprises but return only user enterprise if not cloud admin	
	if text == "_":
		text = "ALL"
# If it's a hypervisor type or template type or public cloud region type, put TYPE		
	if "_" in text:
		text = "TYPE"
	if "\."	in text:
		text = text.replace("\.","_")		
	return text


def process_payload(mediatype,payload):
	if "text" in mediatype:
		text_payload = payload.encode('ascii')
		return text_payload

	elif "json" in mediatype:
		json_payload = ""
		pretty_json = ""
		try:
			json_payload = yaml.load(payload)
			pretty_json = json.dumps(json_payload, sort_keys=False, indent=2)
		except:
			pretty_json = ""
			logging.warning('Format exception: JSON payload - could not load payload with YAML or dump payload')
		#	print "Exception: json payload - could not load payload with yaml or dump payload"
		return pretty_json
			
	elif "xml" in mediatype:
		xml_payload = ""
		valid_xml = ""
		pretty_xml = ""
		try:
			xml_payload = payload.encode('ascii')
			valid_xml = etree.fromstring(xml_payload)
		except:
			logging.warning('Format exception: XML payload - could not validate the XML')
			valid_xml = ""	
		try:		
			pretty_xml = etree.tostring(valid_xml, pretty_print=True)	
		except Exception:
			logging.warning('Format exception: XML was valid but not well formed and could not be pretty printed!')
			pretty_xml = valid_xml
		return pretty_xml
	
	else:
		weird_payload = ""
		weird_payload = payload.encode('ascii')
		return weird_payload


def process_headers_act(raw_actp,raw_head):
	rctp = ""
	ctp = {}
	if raw_actp in raw_head:		
		rctp = raw_head[raw_actp][0]
	return rctp


def process_headers(raw_request_head,raw_response_head):
	# Check for header content and put all headers in one headers object
	request_acc = ""
	request_ct = ""
	response_ct = ""
	aaa = "Accept"
	ccc = "Content-Type"
	if aaa in raw_request_head:
		request_acc = process_headers_act(aaa,raw_request_head)
	if ccc in raw_request_head:	
		request_ct = process_headers_act(ccc,raw_request_head)
	if ccc in raw_response_head:	
		response_ct = process_headers_act(ccc,raw_response_head)		
	hedrs = allheaders(request_acc,request_ct,response_ct)
	hedrs.hprint()
	return hedrs

def format_payload(headerct,payld):
	code_header = '<ac:macro ac:name="code"><ac:plain-text-body><![CDATA['
	code_footer = ']]></ac:plain-text-body></ac:macro>'
	nothing = "<p>--none--</p>" 
	emptypayload = "<p>--empty--</p>"
	pretty_payload = ""
	pretty_payload = process_payload(headerct,payld)
	if not headerct:
		return (nothing)
	if not payld:
		return (nothing)	 
	if pretty_payload != "":
		payld_return = code_header  + pretty_payload + code_footer
		return payld_return
	else:
		return emptypayload		


def mustache_line(subdir,ex_file_name,line,hdrs,files_dictionary,MTversion,adminSubdir,template):
#   request = yaml.load(line)
	request = json.loads(line)
	exdict = {}
	if request['status'] < 400:
	# write the request to a file, but if there are already queries from this run, append numbers to the files

		ex_file_name_plus_dir = os.path.join(subdir,ex_file_name)

		if ex_file_name_plus_dir not in files_dictionary:
			files_dictionary[ex_file_name_plus_dir] = 1
		else:
			files_dictionary[ex_file_name_plus_dir] += 1
		
		if ex_file_name_plus_dir in files_dictionary:
			number_of_files = files_dictionary[ex_file_name_plus_dir] 

		# Pad the integer so that the files are nicely named
		example_file_name = ex_file_name_plus_dir + "." + "{0:04d}".format(number_of_files) + ".txt"
		abiheader_file_name = ex_file_name + "." + "{0:04d}".format(number_of_files) + ".txt"
		exdict['ofName'] = abiheader_file_name
		# Check that it doesn't already exist and open the file for writing
		nothing = "<p>--none--</p>" 

#		if overwriteFiles:
		ef = open_to_overwrite(example_file_name)
#		else:	
#			ef = open_if_not_existing(example_file_name)

		if ef:
			icurl = []
			if request['query_params']:
				ccurl1 = '<ac:macro ac:name="code"><ac:plain-text-body><![CDATA[curl -X ' + request['method'] + ' http://localhost:9000' + request['url'] + "?" + request['query_params'] + " \\ \n"	
			else:
				ccurl1 = '<ac:macro ac:name="code"><ac:plain-text-body><![CDATA[curl -X ' + request['method'] + ' http://localhost:9000' + request['url'] + " \\ \n"
			icurl.append(ccurl1)
			
			ccurl2 = ""	
			if re.search('[a-z]',hdrs.reqAc):
				ccurl2 = "\t -H 'Accept:%s' \\ \n" % hdrs.reqAc 
				if re.search(r'abiquo',hdrs.reqAc):
					if not re.search('version\=[0-9]\.[0-9]',hdrs.reqAc):
						ccurl2 = "\t -H 'Accept:%s; version=%s' \\ \n" % (hdrs.reqAc,MTversion)
				icurl.append(ccurl2)
			ccurl3 = ""
			ccurl4 = ""
			if re.search('[a-z]',hdrs.reqCT):
				pt = ""
				ccurl3 = "\t -H 'Content-Type:%s' \\ \n" % hdrs.reqCT
				if re.search(r'abiquo',hdrs.reqCT):
					if not re.search('version\=[0-9]\.[0-9]',hdrs.reqCT): 
						ccurl3 = "\t -H 'Content-Type:%s; version=%s' \\ \n" % (hdrs.reqCT,MTversion) 	
				icurl.append(ccurl3)
				pts = re.search('json|xml|text',hdrs.reqCT)
				if pts.group(0): 
					pt = pts.group(0)
					ccurl4 = "\t -d @requestpayload.%s \\ \n" % pt
				else:
					ccurl4 = "\t -d @requestpayload \\ \n" 
				icurl.append(ccurl4)

			ccurl5 = '\t -u user:password --verbose ]]></ac:plain-text-body></ac:macro>'	
			icurl.append(ccurl5)
			exdict['ocurl'] = "".join(icurl)

			exdict['ostatus'] = request['status'] # int

			processed_request_payload = ""
			processed_request_payload = format_payload(hdrs.reqCT,request['request_payload'])
		
			if processed_request_payload:
				exdict['orequestData'] = processed_request_payload

			if 	request['status'] != 204:
				processed_response_payload = ""
				processed_response_payload = format_payload(hdrs.rspCT,request['response_payload'])
				if processed_response_payload:
					exdict['oresponseData'] = processed_response_payload
			else:
				exdict['oresponseData'] = nothing
#			mex = example(ofName,ocurl,ostatus,orequestData,oresponseData)
			tfilepath = os.path.join(adminSubdir,template)
			mustacheTemplate = open(tfilepath, 'r').read()
			efo = pystache.render(mustacheTemplate, exdict).encode('utf-8')
			ef.write(efo)
			ef.close()	
			return True	
		else:					
			logging.warning("File error: %s" % example_file_name)
			return False


def pretty_print_line(subdir,ex_file_name,line,hdrs,files_dictionary,MTversion):
#   request = yaml.load(line)
	code_header = '<ac:macro ac:name="code"><ac:plain-text-body><![CDATA['
	code_footer = ']]></ac:plain-text-body></ac:macro>'
	request = json.loads(line)

	if request['status'] < 400:
	# write the request to a file, but if there are already queries from this run, append numbers to the files

		ex_file_name_plus_dir = os.path.join(subdir,ex_file_name)

		# Append an X to the list... number of X-es = number of files created!
		files_dictionary.setdefault(ex_file_name_plus_dir,[]).append("X")
		number_of_files = len(files_dictionary[ex_file_name_plus_dir]) 

		# Pad the integer so that the files are nicely named
		example_file_name = ex_file_name_plus_dir + "." + "{0:04d}".format(number_of_files) + ".txt"
		abiheader_file_name = ex_file_name + "." + "{0:04d}".format(number_of_files) + ".txt"
		# Check that it doesn't already exist and open the file for writing
		nothing = "<p>--none--</p>" 
#		if overwriteFiles:
		ef = open_to_overwrite(example_file_name)

#		else:	
#			ef = open_if_not_existing(example_file_name)

		if ef:
			abiheader = '<ac:macro ac:name="div"><ac:parameter ac:name="class">abiheader</ac:parameter><ac:rich-text-body>' + abiheader_file_name + '</ac:rich-text-body></ac:macro>'
			ef.write(abiheader)
			hcurl = "<p><strong>cURL</strong>:</p>"
			ef.write(hcurl)
			if request['query_params']:
				ccurl1 = '<ac:macro ac:name="code"><ac:plain-text-body><![CDATA[curl -X ' + request['method'] + ' http://localhost:9000' + request['url'] + "?" + request['query_params'] + " \\ \n"	
			else:
				ccurl1 = '<ac:macro ac:name="code"><ac:plain-text-body><![CDATA[curl -X ' + request['method'] + ' http://localhost:9000' + request['url'] + " \\ \n"
			ef.write(ccurl1)
			
			ccurl2 = ""	
			if re.search('[a-z]',hdrs.reqAc):
				ccurl2 = "\t -H 'Accept:%s' \\ \n" % hdrs.reqAc 
				if re.search(r'abiquo',hdrs.reqAc):
					if not re.search('version\=[0-9]\.[0-9]',hdrs.reqAc):
						ccurl2 = "\t -H 'Accept:%s; version=%s' \\ \n" % (hdrs.reqAc,MTversion)
				ef.write(ccurl2)
			ccurl3 = ""
			ccurl4 = ""
			if re.search('[a-z]',hdrs.reqCT):
				pt = ""
				ccurl3 = "\t -H 'Content-Type:%s' \\ \n" % hdrs.reqCT
				if re.search(r'abiquo',hdrs.reqCT):
					if not re.search('version\=[0-9]\.[0-9]',hdrs.reqCT): 
						ccurl3 = "\t -H 'Content-Type:%s; version=%s' \\ \n" % (hdrs.reqCT,MTversion) 	
				ef.write(ccurl3)
				pts = re.search('json|xml|text',hdrs.reqCT)
				if pts.group(0): 
					pt = pts.group(0)
					ccurl4 = "\t -d @requestpayload.%s \\ \n" % pt
				else:
					ccurl4 = "\t -d @requestpayload \\ \n" 
				ef.write(ccurl4)

			ccurl5 = '\t -u user:password --verbose ]]></ac:plain-text-body></ac:macro>'	
			ef.write(ccurl5)

			stat = "<p><strong>Success status code</strong>: %s </p>" % request['status'] # int
			ef.write(stat)

			reqh = "<p><strong>Request payload</strong>:</p>"
			ef.write (reqh)

			processed_request_payload = ""
			processed_request_payload = format_payload(hdrs.reqCT,request['request_payload'])
		
			if processed_request_payload:
				ef.write(processed_request_payload)

			resh = "<p><strong>Response payload</strong>:</p>"
			ef.write (resh)

			if 	request['status'] != 204:
				processed_response_payload = ""
				processed_response_payload = format_payload(hdrs.rspCT,request['response_payload'])
				if processed_response_payload:
					ef.write(processed_response_payload)
			else:
				ef.write(nothing)
			ef.close()	
			return True	
		else:					
			logging.warning("File problem: %s" % example_file_name)
			return False


def log_summary_line(line):
	request = json.loads(line)
	logging.info("Method: %s" % request['method']) # string
	logging.info("URL: %s" % request['url']) # string
	logging.info("Status: %s" % request['status']) # int


def print_summary_line(line):
	request = json.loads(line)
	print "Method: %s" % request['method'] # string
	print "URL: %s" % request['url'] # string
	print "Status: %s" % request['status'] # int


def sub_media_type(mediatype):	
# This function is used to create a reduced media type for the file name
	if mediatype:
		subbed_type = mediatype
		subbed_type = re.sub("application/vnd\.abiquo\.","",subbed_type)
		subbed_type = re.sub(';\s*?version\=[0-9]\.[0-9]{1,2}',"",subbed_type)
		subbed_type = re.sub("\+","_",subbed_type)	
		subbed_type = re.sub("-","_",subbed_type)		
	else:
		subbed_type = ""		
	return subbed_type


def main():
	logging.basicConfig(filename='api_examples.log',level=logging.DEBUG)
	MTversion = ""
	(subdir,rawLog,MTversion,adminSubdir,template) = get_properties_file()
	#subdir = "test_files"	
	files_dictionary = {}
# Load a bunch of abbreviations to replace text and shorten links and mediatypes for filenames
# Note that the word "license" should not be included in the abbreviation file
	abbreviations = {}
	with open("abbreviations.json.txt") as afile:
	 	abbrev_file = afile.read().replace('\n', '')
		abbrev_file = abbrev_file.replace('\t', " ")
		abbreviations = json.loads(abbrev_file)		

	with open(rawLog) as file:
		for line in file:
			request = yaml.load(line)
			raw_request_headers = request['request_headers']
			raw_response_headers = request['response_headers']
			hdrs = process_headers(raw_request_headers,raw_response_headers)
			ex_file_name = create_file_name(line,abbreviations,hdrs)
			logging.info('ex_file_name: %s' % ex_file_name)
			log_summary_line(line)
			# The output directory must exist. If overwriteFiles is set, existing files will be overwritten
			try:
				mustache_line(subdir,ex_file_name,line,hdrs,files_dictionary,MTversion,adminSubdir,template)	
#				pretty_print_line(subdir,ex_file_name,line,hdrs,files_dictionary,MTversion,overwriteFiles)	
#			ex_file = open(os.path.join(subdir,ex_file_name), 'w')	
			except:
				logging.warning("Could not write example file: %s " % ex_file_name)

# Calls the main() function
if __name__ == '__main__':
	main()