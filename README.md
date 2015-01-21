# abiquo-wiki-examples
Automation of Abiquo API examples in the Abiquo REST API reference documentation in the Abiquo wiki with a set of three Python scripts.

##Disclaimer
Use these scripts at your own risk because they are provided without any guarantees. I created this project to update the examples in our REST API documentation, and learnt Python and designed the project as I went along. 

##Acknowledgements
Many thanks to the Abiquo Development team for modifying the integration tests to produce the requests.log file.
The `update_confluence_pages.py` script is based on a blog entry by Matt Ryall called "Adding a page to Confluence with Python" from 29 June 2008. Many thanks also to stackoverflow!

## Prerequisites
* These scripts were run using Python 2.7.9 against Confluence 4.3.2
* These scripts require Confluence API access to be enabled
* You should create a Confluence user for running these scripts
* You should create a separate Confluence wiki space with a suitable parent page (no spaces in name) to hold the example pages. Each example is created in a separate file and page. These pages can be included in API reference documentation
* When you have checked your results, you can copy the pages to your documentation wiki or do whatever else you like with them
* If you want to add a new query manually, add a file in the format `query_name.txt`, with the filename in the abiheader div. For example, `GET_api_version.txt`

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
Copy the `confluence_properties_sample.txt` to `confluence_properties.json.txt` and change the values to appropriate ones for your environment. All properties are required. The properties are fully described below.


## Scripts
There are three scripts: `process_api_examples.py`, `read_files_confluence_pages.py` and `update_confluence_pages.py`

### process_api_examples.py

  * Read the requests log and create example files in Confluence storage format for all requests with success status code (<400). 
  * The file names are based on the query command and URL, abbreviated according to the list in the `abbreviations.json.txt` file. 
   * An example file name is `DELETE_adm_dcs_X.0001.txt` and an example Confluence page name is `DELETE_adm_dcs_X`. Here X represents an entity number, e.g. Datacenter 6. Note that the abbreviation system is not perfect because the program abbreviates text literals rather than replacing them.
   * If you create a custom file, it MUST be named the same as your query, with a REST option (GET, etc) at the front and with a .txt extension. i.e. Query name `DELETE_adm_dcs_X` and file name `DELETE_adm_dcs_X.txt` 

Your custom file/page MUST contain the file name in a hidden div with the title abiheader. So if you create a custom file, you can add it, for example, `DELETE_adm_dcs_X.txt`, and the search will look for it in the abiheader section: 
"`abiheader</ac:parameter><ac:rich-text-body>DELETE_adm_dcs_X.txt<`"
It should be a valid filename with no spaces and valid characters.

The example pages are designed to be MANUALLY included in the wiki API reference docs. It is possible to search or retrieve page content (using the scripts written by Sarah Maddox, for example) and grep for included page names.

### read_files_confluence_pages.py
Get the 0001 files from the subdirectory specified in the options and check if a Confluence page already exists, and if so, check if it has been modified. This script creates three files: `wiki_all_files.json.txt`, `wiki_update.json.txt` and `wiki_prohibited.json.txt` as well as `wiki_options_update.json.txt`. You can edit any of these files to change which Confluence pages will be updated by the next script.  

#### wiki_all_files.json.txt
This file contains a JSON dictionary of all *0001* files and all custom ".txt" files. You could add your own custom files to this list to create them as new pages. The file is in the format "Page name" : "File path"
Note that this file contains prohibited files, such as license files.

#### wiki_update.json.txt 
This file contains a JSON dictionary of all files that already have pages, similar to the `wiki_all_files.json.txt` file.

#### wiki_options_update.json.txt
The file is in the format { "option" : { "Page name" : file name", where "option" is one of the status strings in the above list (modifier, alternative, etc.) and an example is `{ "invalid" : "DELETE_adm_dcs_X" : "DELETE_adm_dcs_X.txt"`

Options from status strings include:
  * **modifier**: if the last user to modify the Confluence page is not the same as the user running the script. By default, this page will not be updated
  * **alternative**: the file name pattern is the same but the file name included in the page is different, e.g. a user has changed the 0001 file for an 0002 file. By default, this page will be updated with the alternative page 
  * **duplicate**: the `abc_xxx` page was created already, and there is also an `abc_XXX.0001.txt` file, where part of the text "XXX" is in a different case. By default, this page will be ignored
  * **custom**: this page will be updated with the custom file specified by the user. Note that custom file names should follow the file name standard and end in ".txt" without any numbers. By default this page will not be updated. An example would be `DELETE_adm_dcs_X.txt`
  * **invalid**: there is no valid filename, e.g. because the filename contains spaces. By default this page will not be updated
  * **original**: there is a valid filename and it appears to be the 0001 file.

#### wiki_prohibited.json.txt
Files that must NOT be included in the wiki (e.g. files containing licenses). The file is in the format "Page name" : "File path"

### update_confluence_pages.py
Read `wiki_all_files.json.txt` and create new pages. Depending on the update options set in the properties file, update the pages found in `wiki_update.json.txt` accordingly. Do not add any of the pages in `wiki_prohibited.json.txt` to the wiki.  

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
|overwriteFiles | y | Overwrite existing example files in the subdir |
|MTversion | 3.2 | Default media type version for the API, which is the current product version |

### Properties for `update_confluence_pages.py`
These properties are related to how the update script updates the wiki, based on the `wiki_updates.json.txt` file.
Also see the specific section about this file.
Unless otherwise specified, the pages listed in wiki_options_update.json.txt are updated with the corresponding files listed in the same file. So it is also possible to modify the behaviour of the script by modifying the file directly, although this is not generally recommended.

#### Basic properties
|Property | Default | Description | Default text file |
|:-----|:-----|:------|:-----|
|rewriteAll | no | Overwrite ALL pages listed with the default 0001 file. This option has precedence over all other options. If true, ignore ALL other options. Creates new pages. | 0001 file | 
|updateAll | no | Update ALL pages using the **default text file**. If rewriteAll is false, and this option is true, ignore ALL other options. Creates new pages | Default text file as supplied in this column in the following table | 

#### Status properties
Pages that would be updated are listed in the `wiki_updates.json.txt` file. These properties determine how to treat pages with different status string values as described below. Note that the **basic properties** described above completely override these properties. 

If none of the basic properties are set, these status properties determine if the files are updated or not. The text file used to update the page will be the one shown in the Default text file column below, unless the wiki_update.json.txt file is manually edited to modify the file name values. Note that the file names should have a valid REST option at the start of the name.   

|Property | Default | Description | Default text file | Example file name | 
|:-----|:-----|:------|:-----|:-----|
|original | yes | Update existing pages listed (i.e. pages with no status string) | 0001 | `GET_xxxx.0001.txt`  |
|new| yes | Create new pages | 0001 |`GET_xxx.0001.txt`| 
|modifier | no | Update pages modified by users that are not the script user. If false, the pages are not updated  | 0001 | `GET_xxxx.0001.txt`  |
|alternative | yes | Update pages with an alternative page number version. If false, the pages are not updated | alternative | `GET_xxxx.0002.txt`  |
|duplicate | no | Update pages with a duplicate file with the file text of the other version e.g. `GET_XXXX.0001.txt` changes to `GET_xxxx.0001.txt` and vice versa. If false, the pages are not updated | duplicate | `GET_XXXX.0001.txt`  |
|custom | yes | Update pages with a valid custom file name. If false, the pages are not updated | custom | `GET_xxxx.txt`  |
|invalid | no | Update pages with an invalid file name, e.g. text with spaces. If false, the pages are not updated | 0001 |`GET_xxx.0001.txt`  |

