# abiquo-wiki-examples

Automation of Abiquo API examples in the Abiquo wiki with a set of three Python scripts using Python 2.7.

## Input files
Developers provide a requests.log JSON file with query output from integration tests.

  * method: string
  * url: string
  * query_params: string
  * status: int
  * request_headers: JSON dictionary
  * response_headers: JSON dictionary
  * request_payload: JSON or XML, inspect request Content-Type header
  * response_payload: JSON or XML, inspect response Content-Type header

## Properties
Copy the sample properties file to the real properties file name and change the values to appropriate ones for your environment.

## Scripts
There are three scripts: `process_api_examples.py`, `read_files_confluence_pages.py` and `update_confluence_pages.py`

### process_api_examples.py

  * Read the requests log and create example files in Confluence storage format for all requests with success status code (<400). 
  * The file names are based on the query command and URL, abbreviated according to the list in the `abbreviations.json.txt` file. 
   * An example of a file name is `DELETE_adm_dcs_X.0001.txt` and an example Confluence page name is `DELETE_adm_dcs_X`. Here X represents an entity number, e.g. Datacenter 6. Note that the abbreviation system is not perfect because the program abbreviates text literals rather than replacing them.

The example pages should contain the file name in a hidden div with the title abiheader. So if you create a custom file, you can add it, for example, my_own_file.txt, and the search will look for it in the abiheader section: 
"`abiheader</ac:parameter><ac:rich-text-body>my_own_file.txt<`"
It should be a valid filename with no spaces.

The example pages are designed to be MANUALLY included in the wiki API reference docs. It is possible to search or retrieve page content (using the Sarah Maddox scripts) and grep for included page names.

### read_files_confluence_pages.py
Get the 0001 files from the subdirectory specified in the options and check if a Confluence page already exists, and if so, check if it has been modified. This script creates three files: `wiki_all_files.json.txt`, `wiki_force_update.json.txt` and `wiki_prohibited.json.txt`. You can edit any of these files to change which Confluence pages will be updated by the next script.  

#### wiki_all_files.json.txt
This file contains a JSON dictionary of all *0001* files. You could add your own custom files to this list to create them as new pages. The file is in the format "Page name" : "File path"

#### wiki_force_update.json.txt 
This file contains a JSON dictionary of all files that already have pages. 

The file is in the format "Page name" : "[<status string>: ]file name", where <status string> is one of the status strings in the above list (modifier, alternative, etc.) and an example is "DELETE_adm_dcs_X" : "custom: My_file.txt"

Where the 0001 file appears to have been used, only the file name given and no status string is included. 

Status strings include:
  * **modifier**: if the last user to modify the Confluence page is not the same as the user running the script
  * **alternative**: the file name pattern is the same but the file name included in the page is different, e.g. a user has changed the 0001 file for an 0002 file 
  * **duplicate**: the `abc_xxx page` was created already and there is also an `abc_XXX.0001.txt` file. By default, this page will be ignored
  * **custom**: this page will be updated with the custom file specified by the user. Note that custom file names cannot contain spaces
  * **invalid**: there is no valid filename, e.g. because the filename contains spaces



#### wiki_prohibited.json.txt
Files that must NOT be included in the wiki (e.g. files containing licenses). The file is in the format "Page name" : "File path"

### update_confluence_pages.py
Read `wiki_all_files.json.txt`. If update options are set in the properties file, update all pages found in `wiki_force_update.json.txt` accordingly. Do not add any of the pages in `wiki_prohibited.json.txt` to the wiki.  
