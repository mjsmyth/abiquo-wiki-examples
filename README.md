# abiquo-wiki-examples

Automation of Abiquo API examples in the Abiquo wiki with a set of 3 Python scripts using Python 2.7.

Copy the sample properties file to the real properties file name and change the values to appropriate ones for your environment.

There are three scripts: `process_api_examples.py`, `read_files_confluence_pages.py` and `update_confluence_pages.py`

## process_api_examples.py
Read the requests log and create example files in Confluence storage format for all requests with success status code (<400). The file names are based on the query command and URL, abbreviated according to the list in the `abbreviations.json.txt` file. An example of a file name is `DELETE_adm_dcs_X.0001.txt` and an example Confluence page name is `DELETE_adm_dcs_X`. Here X represents an entity number, e.g. Datacenter 6. Note that the abbreviation system is not perfect because the program abbreviates some text literals rather than replacing them with X. 

The example pages are designed to be MANUALLY included in the wiki API reference docs. It is possible to search or retrieve page content (using the Sarah Maddox scripts) and grep for included page names.


## read_files_confluence_pages.py
Get the 0001 files and check if a Confluence page already exists, and if so, check if it has been modified. This script creates three files: `wiki_all_files.json.txt`, `wiki_force_update.json.txt` and `wiki_prohibited.json.txt`. You can edit any of these files to change which Confluence pages will be updated by the next script.  

### wiki_all_files.json.txt
This file contains a JSON dictionary of all *0001* files. You could add your own custom files to this list to create them as new pages. The file is in the format "Page name" : "File path"

### wiki_force_update.json.txt 
This file contains a JSON dictionary of all "updated" files. Files will be included in this list for various reasons, for example
  * if the last user to modify the Confluence page is not the same user as the one running the script
  * the filename included in the page is different, e.g. a user has changed the 0001 file for an 0002 file 
  * the abc_xxx page was created already and there is also an abc_XXX.0001.txt file.

The file is in the format "Page name" : "Info", which info may include a file name. 

### wiki_prohibited.json.txt
Files that must NOT be included in the wiki (e.g. files containing licenses). The file is in the format "Page name" : "File path"

## update_confluence_pages.py
Read *wiki_all_files.json.txt*. If Force update options are set, update all pages found in *wiki_force_update.json.txt*. Always ignore prohbited files.  
