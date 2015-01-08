# abiquo-wiki-examples
Automation of Abiquo API examples in the Abiquo REST API reference documentation in the Abiquo wiki with a set of three Python scripts.

##Disclaimer
Use these scripts at your own risk because they are provided without any guarantees. I created this project to update the examples in our REST API documentation, and learnt Python and designed the project as I went along. 

##Acknowledgements
Many thanks to the Abiquo Development team for modifying the integration tests to produce the requests.log file.
The `update_confluence_pages.py` script is based on a blog entry by Matt Ryall called "Adding a page to Confluence with Python" from 29 June 2008. 

## Prerequisites
* I have run these scripts using Python 2.7.9 against Confluence 4.3.2
* These scripts require Confluence API access to be enabled
* You should create a Confluence user for running these scripts
* You should create a separate Confluence wiki space with a suitable parent page (no spaces in name) to hold the example pages. Each example is created in a separate file and page. These pages can be included in API reference documentation
* When you have checked your results, you can copy the pages to your documentation wiki or do whatever else you like with them

## Input files
Developers provide a requests.log JSON file with query output from integration tests. The file used in this case has the following content.

| JSON element | Data type |
| :---------------- |:--------- |
| method | string |
| url | string |
| query_params | string |
| status | int |
| request_headers | JSON dictionary |
| response_headers | JSON dictionary |
| request_payload | JSON or XML, inspect request Content-Type header |
| response_payload | JSON or XML, inspect response Content-Type header |

## Properties
Copy the sample properties file to `confluence_properties.json.txt` and change the values to appropriate ones for your environment. All properties are required. The properties are fully described below.


## Scripts
There are three scripts: `process_api_examples.py`, `read_files_confluence_pages.py` and `update_confluence_pages.py`

### process_api_examples.py

  * Read the requests log and create example files in Confluence storage format for all requests with success status code (<400). 
  * The file names are based on the query command and URL, abbreviated according to the list in the `abbreviations.json.txt` file. 
   * An example of a file name is `DELETE_adm_dcs_X.0001.txt` and an example Confluence page name is `DELETE_adm_dcs_X`. Here X represents an entity number, e.g. Datacenter 6. Note that the abbreviation system is not perfect because the program abbreviates text literals rather than replacing them.

The example pages should contain the file name in a hidden div with the title abiheader. So if you create a custom file, you can add it, for example, my_own_file.txt, and the search will look for it in the abiheader section: 
"`abiheader</ac:parameter><ac:rich-text-body>my_own_file.txt<`"
It should be a valid filename with no spaces.

The example pages are designed to be MANUALLY included in the wiki API reference docs. It is possible to search or retrieve page content (using the scripts written by Sarah Maddox, for example) and grep for included page names.

### read_files_confluence_pages.py
Get the 0001 files from the subdirectory specified in the options and check if a Confluence page already exists, and if so, check if it has been modified. This script creates three files: `wiki_all_files.json.txt`, `wiki_update.json.txt` and `wiki_prohibited.json.txt`. You can edit any of these files to change which Confluence pages will be updated by the next script.  

#### wiki_all_files.json.txt
This file contains a JSON dictionary of all *0001* files. You could add your own custom files to this list to create them as new pages. The file is in the format "Page name" : "File path"

#### wiki_update.json.txt 
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

### General Properties

|Property | Example | Description |
|:-----|:-----|:------|
|wikiUrl |  http://URL:port | Wiki URL and port |
|spaceKey | MSK | Wiki space key |
|parentTitle | APIExamples | Title of parent page without spaces  |
|user |  myuser | Wiki user name for running script |
|password | mypassword | Wiki password for running script |
|rawLog | requests.log | Log file provided by friendly developers with output of integration tests |
|subdir | apiexamples | Directory under the project directory where example files are stored |
|MTversion | 3.2 | Default media type version for the API |

### Properties for `update_confluence_pages.py`
These properties are related to how the update script updates the wiki, based on the `wiki_updates.json.txt` file.
Also see the specific section about this file below
Unless otherwise specified, the pages listed in wiki_updates.json.txt are updated with the corresponding files listed in the same file. So it is also possible to modify the behaviour of the script by modifying the file directly, although this is not generally recommended.

#### Basic properties
|Property | Default | Description | Default text file |
|:-----|:-----|:------|:-----|
|rewriteAll | no | Overwrite ALL pages listed with the default 0001 file | 0001 file | 
|updateAll | no | Update ALL pages using the default text file | Default text file as supplied in this column in the following table | 

#### Status properties
Pages that would be updated are listed in the `wiki_updates.json.txt` file. These properties determine how to treat pages with different status string values as described below. Note that the **basic properties** described above completely override these properties. 

If none of the basic properties are set, these status properties determine if the files are updated or not. The text file used to update the page will be the one shown in the Default text file column below, unless the wiki_update.json.txt file is manually edited to modify the file name values.   

|Property | Default | Description | Default text file | Example file name | 
|:-----|:-----|:------|:-----|:-----|
|existing | yes | Update existing pages listed (i.e. pages with no status string) | 0001 | xxxx.0001.txt  |
|modifier | no | Update pages modified by users that are not the script user  | 0001 | xxxx.0001.txt  |
|alternative | yes | Update pages with an alternative page number version | alternative | xxxx.0002.txt  |
|duplicate | no | Update pages with a duplicate file with the file text of the other version e.g. XXXX.0001.txt changes to xxxx.0001.txt and vice versa | duplicate | XXXX.0001.txt  |
|custom | no | Update pages with a valid custom file name | custom | myfile.txt  |
|invalid | no | Update pages with an invalid file name, e.g. text with spaces | 0001 | xxx.0001.txt  |
