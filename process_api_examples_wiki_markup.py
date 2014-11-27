#!/usr/bin/python2 -tt
# Process API examples for the wiki
# Read the IT tests log file
# Identify the requests with status 204 or 200
# Create a file name by replacing numbers and long bits of the URL
# Save the requests with a nominal invented curl, status code and request and response payload
# Writes a file with wiki markup


import json
import yaml
import ast
import re
import xml.dom.minidom
import os.path

 
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
        print "Ooops"
        return None
    fobj = os.fdopen(fd, "w")
    return fobj


def pretty_print_line(output_subdir,ex_file_name,line,files_dictionary):
#   request = yaml.load(line)
	header_html = '<div class="preformatted panel" style="border-width: 1px;"><div class="preformattedContent panelContent"><pre>'
	footer_html = '</pre></div></div>'
	header_wiki_markup = '{newcode}'
	footer_wiki_markup = '{newcode}'
	header = header_wiki_markup
	footer = footer_wiki_markup

	request = json.loads(line)
	if request['status'] < 400:
	# write the request to a file, but if there are already queries from this run, append numbers to the files

		ex_file_name_plus_dir = os.path.join(output_subdir,ex_file_name)

		# Append an X to the list... number of X-es = number of files created!!! this is really dodgy!!!
		files_dictionary.setdefault(ex_file_name_plus_dir,[]).append("X")
		number_of_files = len(files_dictionary[ex_file_name_plus_dir]) 
		# Pad the integer so that the files are nicely named
		example_file_name = ex_file_name_plus_dir + "." + "{0:04d}".format(number_of_files) + ".txt"

		# Check that it doesn't already exist and open the file for writing
		ef = open_if_not_existing(example_file_name)

		abiheader = "{div:class=abiheader}" + example_file_name + "{div}\n"
		ef.write(abiheader)
		hcurl = "*cURL*:\n"
		ef.write(hcurl)
		ccurl1 = "{newcode}curl -X " + request['method'] + "http://localhost:9000" + request['url'] + "\\ \n"
		ef.write(ccurl1)
		ccurl2 = ""
		request_head = request['request_headers']
		if 'Content-Type' in request_head:
			content_type = request_head['Content-Type']
 			ccurl2 = "\t -H 'Content-Type: %s " % content_type[0].encode('ascii') + "\\ \n"
 		ef.write(ccurl2)	
 		ccurl3 = ""	
		if 'Accept' in request_head:
			accept = request_head['Accept'] 
			ccurl3 = "\t -H 'Accept: %s " % accept[0].encode('ascii') + "\\ \n"
		ef.write(ccurl3)
		ccurl4 = "\t -u user:password --verbose {newcode} \n"	
		ef.write(ccurl4)
# 		mets = "*Method: %s \n" % request['method'] # string
# 		ef.write(mets)
#		urls = "<strong>URL:</strong> %s \n" % request['url'] # string
#		ef.write(urls)
		stat = "*Success status code*: %s \n" % request['status'] # int
#		ef.write(stat)
		response_head = request['response_headers']
#		reqh = "Request headers: %s" % request['request_headers'] # It's a JSON dictionary
		nothing = "--none--\n" 
		reqh = "*Request payload*: \n"
		ef.write (reqh)

		if 'Content-Type' in request_head:
			content_type_list = request_head['Content-Type']
			if content_type_list:
				content_type = content_type_list[0]
				if content_type:
					ef.write (header)
					if "json" in content_type:
						json_request_payload = yaml.load(request['request_payload'])
						reqp_json = json.dumps(json_request_payload, sort_keys=False, indent=2)
						ef.write (reqp_json)
					if "xml" in content_type:
						xml_request_payload = xml.dom.minidom.parseString(request['request_payload'])
						pretty_xml = xml_request_payload.toprettyxml()
						reqp_xml = pretty_xml
	#					resp_xml = cgi.escape(pretty_xml).encode('ascii', 'xmlcharrefreplace')
						ef.write(reqp_xml)
					ef.write (footer)	
		else:
			ef.write(nothing)		

		resh = "*Response payload*: \n"
		ef.write (resh)
#		accept_type_list = request_head['Accept']
		if 'Content-Type' in response_head:
			response_ct_list = response_head['Content-Type']
			if response_ct_list:
				response_ct = response_ct_list[0]
				if response_ct:
					ef.write (header)
					if "json" in response_ct:
						json_response_payload = yaml.load(request['response_payload'])
						resp_json = json.dumps(json_response_payload, sort_keys=False, indent=2)
						ef.write (resp_json)
					if "xml" in response_ct:
						xml_response_payload = xml.dom.minidom.parseString(request['response_payload'])
						pretty_xml = xml_response_payload.toprettyxml()
						resp_xml = pretty_xml
	#					resp_xml = cgi.escape(pretty_xml).encode('ascii', 'xmlcharrefreplace')
						ef.write(resp_xml)
					ef.write (footer)	
		else:
			ef.write(nothing)
		ef.close()		

def print_summary_line(line):
	request = json.loads(line)
	print "Method: %s" % request['method'] # string
	print "URL: %s" % request['url'] # string
	print "Status: %s" % request['status'] # int


def create_file_name(line,abbreviation):
#	request = json.loads(line)
	request = yaml.load(line)
	example_file_name = ""
	raw_url = request['url']
	raw_method = request['method']
	rep_url_list = []
	print "Raw_url: %s" % raw_url
	raw_url_list = raw_url.split("/")
	for ruli in raw_url_list:
		ruli = rep_text(ruli,abbreviation)
		rep_url_list.append(ruli)
	example_file_name = raw_method + "_".join(rep_url_list) 
	return example_file_name


def rep_text(text,abbreviation):
	for abbi, abbr in abbreviation.iteritems():
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



def main():
	output_subdir = "test_files"	
	files_dictionary = {}
# Load a bunch of abbreviations to replace text and shorten links
	abbreviations = {}
	with open("abbreviations.json.txt") as afile:
		abbrev_file = afile.read().replace('\n', '')	
		abbreviations = ast.literal_eval(abbrev_file)
#	print "Abbreviation for enterprise: %s" % abbreviations["enterprise"]	

	with open("requests.log") as file:
		for line in file:
			ex_file_name = create_file_name(line,abbreviations)
			print "ex_file_name: %s" % ex_file_name
#			print_summary_line(line)
			pretty_print_line(output_subdir,ex_file_name,line,files_dictionary)	
#			ex_file = open(os.path.join(output_subdir,ex_file_name), 'w')	

# Calls the main() function
if __name__ == '__main__':
	main()