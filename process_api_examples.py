#!/usr/bin/python2 -tt
# Process API examples for the wiki
# Read the IT tests log file
# Identify the requests with status 204 or 200
# Create a file name by replacing numbers and long bits of the URL
# Save the requests to a text file inside a code block


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


def pretty_print_line(output_subdir,ex_file_name,line):
	request = yaml.load(line)
#	request = json.loads(line)
	print "Method: %s" % request['method'] # string
	print "URL: %s" % request['url'] # string
	print "Status: %s" % request['status'] # int
	if request['status'] < 400:
		# write the request to a file, but if there are already files, append numbers to them
	#	out_file = open(os.path.join(output_subdir,output_file_name), 'w')
		ex_file_dir = os.path.join(output_subdir,ex_file_name)
		if os.path.isfile(ex_file_dir)
		print "Request headers: %s" % request['request_headers'] # It's a JSON dictionary
		response_head = request['response_headers']
		print "Response headers: %s" % request['response_headers'] # It's a JSON dictionary
		print "Request payload: %s" % request['request_payload'] # A JSON or an XML, inspect request Content-Type header
	#	print "Response payload: %s" % request['response_payload']  # A JSON or an XML, inspect response Content-Type header
		content_type_list = response_head['Content-Type']
		if content_type_list:
			content_type = content_type_list[0]
			if content_type:
				print "Response payload:"
				print "{newcode}"
				if "json" in content_type:
					json_payload = yaml.load(request['response_payload'])
					print json.dumps(json_payload, sort_keys=False, indent=2)
				if "xml" in content_type:
					print "World!"
					xml_payload = xml.dom.minidom.parseString(request['response_payload'])
					print xml_payload.toprettyxml()
				print "{newcode}"	


def print_summary_line(line):
	request = json.loads(line)
	print "Method: %s" % request['method'] # string
	print "URL: %s" % request['url'] # string
	print "Status: %s" % request['status'] # int


def main():
	output_subdir = "example_files"	
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
			pretty_print_line(ex_file_name,line)	
#			ex_file = open(os.path.join(output_subdir,ex_file_name), 'w')



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
	example_file_name = raw_method + "_".join(rep_url_list) + ".txt"
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

# Calls the main() function
if __name__ == '__main__':
	main()