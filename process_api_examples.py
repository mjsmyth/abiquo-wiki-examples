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
import os.path
import cgi
from lxml import etree
from StringIO import StringIO
from io import BytesIO
import logging



class allheaders:
	def __init__(self,aRequestAccept,aRequestContentType,aResponseContentType):
		self.reqAc=aRequestAccept
		self.reqCT=aRequestContentType
		self.rspCT=aResponseContentType

 
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


def open_if_not_existing(filename):
    try:
        fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except:
		logging.warning("File: %s already exists" % filename)
        return None
    fobj = os.fdopen(fd, "w")
    return fobj


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
		#	print "Exception: xml payload - could not validate the xml"
			valid_xml = ""	
		try:		
			pretty_xml = etree.tostring(valid_xml, pretty_print=True)	
		except Exception:
			logging.warning('Format exception: XML was valid but not well formed and could not be pretty printed!')
		#	print "Exception: XML was not well formed and could not be pretty printed!"
			pretty_xml = valid_xml
		return pretty_xml	
	
	else:
		weird_payload = ""
		weird_payload = payload.encode('ascii')
		return weird_payload

def process_headers_accept_content_type(raw_actp,raw_head):
	ctp = ""
	if raw_actp in raw_head:
		ctp_list = raw_head[ctp]
		if ctp_list:
			ctp = ctp_list[0]
			if ctp:
				ctp = ctp.encode('ascii')
	return ctp


def process_headers(raw_request_head,raw_response_head):
	# Check for header content and put all headers in one convenient object
	request_acc = ""
	request_ct = ""
	response_ct = ""
	request_acc = process_headers_accept_content_type('Accept',raw_request_head)
	request_ct = process_headers_accept_content_type('Content-Type',raw_request_head)
	response_ct = process_headers_accept_content_type('Content-Type',raw_response_head)	
	hedrs = allheaders(request_acc,request_ct,response_ct)
	return hedrs


def pretty_print_line(output_subdir,ex_file_name,line,hdrs,files_dictionary):
#   request = yaml.load(line)
	code_header = '<ac:macro ac:name="code"><ac:plain-text-body><![CDATA['
	code_footer = ']]></ac:plain-text-body></ac:macro>'
	request = json.loads(line)

	if request['status'] < 400:
	# write the request to a file, but if there are already queries from this run, append numbers to the files

		ex_file_name_plus_dir = os.path.join(output_subdir,ex_file_name)

		# Append an X to the list... number of X-es = number of files created! I'm sure there's a better way to count them :-)
		files_dictionary.setdefault(ex_file_name_plus_dir,[]).append("X")
		number_of_files = len(files_dictionary[ex_file_name_plus_dir]) 
		# Pad the integer so that the files are nicely named
		example_file_name = ex_file_name_plus_dir + "." + "{0:04d}".format(number_of_files) + ".txt"
		abiheader_file_name = ex_file_name + "." + "{0:04d}".format(number_of_files) + ".txt"
		# Check that it doesn't already exist and open the file for writing
		ef = open_if_not_existing(example_file_name)
		if not ef:
			logging.warning("File %s already exists" % example_file_name)
			sys.stdout.write('File %s already exists' % example_file_name)

		abiheader = '<ac:macro ac:name="div"><ac:parameter ac:name="class">abiheader</ac:parameter><ac:rich-text-body>' + abiheader_file_name + '</ac:rich-text-body></ac:macro>'
		ef.write(abiheader)
		hcurl = "<p><strong>cURL</strong>:</p>"
		ef.write(hcurl)
		if request['query_params']:
			ccurl1 = '<ac:macro ac:name="code"><ac:plain-text-body><![CDATA[curl -X ' + request['method'] + ' http://localhost:9000' + request['url'] + request['query_params'] + " \\ \n"	
		else:
			ccurl1 = '<ac:macro ac:name="code"><ac:plain-text-body><![CDATA[curl -X ' + request['method'] + ' http://localhost:9000' + request['url'] + " \\ \n"
		ef.write(ccurl1)
		
		ccurl2 = ""	
		if re.search('[a-z]',hdrs.reqAc):
			ccurl2 = "\t -H 'Accept:%s' \\ \n" % hdrs.reqAc 
			if re.search(r'abiquo',hdrs.reqAc):
				if not re.search('version\=[0-9]\.[0-9]',hdrs.reqAc):
					ccurl2 = "\t -H 'Accept:%s;version=3.2' \\ \n" % hdrs.reqAc
			ef.write(ccurl2)
		ccurl3 = ""
		ccurl4 = ""
		if re.search('[a-z]',hdrs.reqCT):
			ccurl3 = "\t -H 'Content-Type:%s' \\ \n" % hdrs.reqCT
			if re.search(r'abiquo',hdrs.reqCT):
				if not re.search('version\=[0-9]\.[0-9]',hdrs.reqCT): 
					ccurl3 = "\t -H 'Content-Type:%s;version=3.2' \\ \n" % hdrs.reqCT 	
			ccurl4 = "\t -d @requestpayload.xml \\ \n"	
			ef.write(ccurl3)
			ef.write(ccurl4)

		ccurl5 = '\t -u user:password --verbose ]]></ac:plain-text-body></ac:macro>'	
		ef.write(ccurl5)
# 		mets = "*Method: %s \n" % request['method'] # string
# 		ef.write(mets)
#		urls = "<strong>URL:</strong> %s \n" % request['url'] # string
#		ef.write(urls)
		stat = "<p><strong>Success status code</strong>: %s </p>" % request['status'] # int
		ef.write(stat)

#		reqh = "Request headers: %s" % request['request_headers'] # It's a JSON dictionary
		nothing = "<p>--none--</p>" 
		emptypayload = "<p>--empty--</p>"
		reqh = "<p><strong>Request payload</strong>:</p>"
		ef.write (reqh)

		if hdrs.reqCT:
			if request['request_payload']:
				pretty_payload = ""
				pretty_payload = process_payload(hdrs.reqCT,request['request_payload'])
				if pretty_payload != "":
					ef.write (code_header)
					ef.write (pretty_payload)
					ef.write (code_footer)
				else:
					ef.write (emptypayload)		
			else:
				ef.write(nothing)
		else:
			ef.write(nothing)		

		resh = "<p><strong>Response payload</strong>:</p>"
		ef.write (resh)
#		accept_type_list = request_head['Accept']
		if 	request['status'] != 204:
			if hdrs.rspCT:
				if request['response_payload']:
					pretty_payload = ""
					pretty_payload = process_payload(hdrs.rspCT,request['response_payload'])
					if pretty_payload != "":
						ef.write (code_header)
						ef.write (pretty_payload)
						ef.write (code_footer)
					else:
						ef.write (emptypayload)
				else:
					ef.write(nothing)
			else:
				ef.write(nothing)
		else:
			ef.write(nothing)
		ef.close()		

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
# This function is used to replace the media type for the file name
	if mediatype:
		subbed_type = mediatype
		subbed_type = re.sub("application/vnd\.abiquo\.","",subbed_type)
		subbed_type = re.sub(';\s*?version\=[0-9]\.[0-9]',"",subbed_type)
		subbed_type = re.sub("\+","_",subbed_type)	
		subbed_type = re.sub("-","_",subbed_type)		
	else:
		subbed_type = ""		
	return subbed_type

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
				logging.info("qpName: %s" % qpName)
				print "qpName: %s" % qpName
				qpValue = qpValuelist[1]
				logging.info("qpValue: %s " % qpValue)
				print "qpValue: %s " % qpValue
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
	return text	

def rep_text(text,abbreviations):
	for abbi, abbr in iter(sorted(abbreviations.iteritems(),reverse=True)):
		text = text.replace(abbi,abbr)
# If it's a storage pool name		
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
	return text

def get_properties_file():
	# Load properties for the scripts, including wiki properties that can't be stored in a public repo
	properties = {}
	with open("confluence_properties.json.txt") as pfile:
		prop_file = pfile.read().replace('\n', '')	
		prop_file = prop_file.replace('\t', " ")
		properties = json.loads(prop_file)
		for ix, ick in enumerate(properties):
#			print "%d: %s - %s" % (ix,ick,properties[ick])
			logging.info("%d: %s - %s" % (ix,ick,properties[ick]))
		output_subdir = properties['outputSubdir']
		return (output_subdir)

def main():
#	output_subdir = "storage_format_files"
	logging.basicConfig(filename='api_examples.log',level=logging.DEBUG)
#	logging.debug('This message should go to the log file')
#	logging.info('So should this')
#	logging.warning('And this, too')	
	(output_subdir) = get_properties_file()
	#output_subdir = "test_files"	
	files_dictionary = {}
# Load a bunch of abbreviations to replace text and shorten links and mediatypes for filenames
# Do not replace the word license
	abbreviations = {}
	with open("abbreviations.json.txt") as afile:
	 	abbrev_file = afile.read().replace('\n', '')
		abbrev_file = abbrev_file.replace('\t', " ")
		abbreviations = json.loads(abbrev_file)		

	with open("requests.log") as file:
		for line in file:
			request = yaml.load(line)
			raw_request_headers = request['request_headers']
			raw_response_headers = request['response_headers']
			hdrs = process_headers(raw_request_headers,raw_response_headers)
			ex_file_name = create_file_name(line,abbreviations,hdrs)
			logging.info('ex_file_name: %s' % ex_file_name)
#			print "ex_file_name: %s" % ex_file_name
			log_summary_line(line)
			pretty_print_line(output_subdir,ex_file_name,line,hdrs,files_dictionary)	
#			ex_file = open(os.path.join(output_subdir,ex_file_name), 'w')	

# Calls the main() function
if __name__ == '__main__':
	main()