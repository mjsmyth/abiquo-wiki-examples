# abiquo-wiki-examples
Automation of Abiquo API examples in the Abiquo REST API reference documentation in the Abiquo Confluence wiki with a set of three Python scripts.

##Disclaimer
Use these scripts at your own risk because they are provided without any guarantees. I created this project to update the examples in our REST API documentation, and learnt Python and designed the project as I went along. 

##Acknowledgements
Many thanks to the Abiquo Development team for modifying the integration tests to produce the requests.log file.
The `update_confluence_pages.py` script is based on a blog entry by Matt Ryall called "Adding a page to Confluence with Python" from 29 June 2008. Many thanks also to Stack Overflow!

## Prerequisites
* These scripts were run using Python 2.7.9 and 3.4.x against Confluence 4.3.2
* These scripts require Confluence API access to be enabled
* You should create a separate Confluence user for running these scripts
* You should create a separate Confluence wiki space with a suitable parent page (with no spaces in the name) to hold the example pages. 
* Each example is created in a separate file and page using a mustache template, so you can customise this template file
* When you have checked your results, you can copy the pages to your documentation wiki or do whatever else you like with them. For example, we have "manually" included the pages in our API reference documentation


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
There are two scripts: `process_api_examples.py`and `ReadAndUpdateConfluencePages.p`
### process_api_examples.py
* Read the requests log and create example files in Confluence storage format for all requests with success status code `< 400`
* The file names are based on the query command and URL, abbreviated according to the list in the `abbreviations.json.txt` file. 
* An example file name is `DELETE_adm_dcs_X.0001.txt` and an example Confluence page name is `DELETE_adm_dcs_X`. Here X represents an entity number, e.g. Datacenter 6. Note that the abbreviation system is not perfect because the program abbreviates text literals rather than replacing them.
* Later in Confluence you replace examples with a different number. And you can rename the pages to match the API methods. However, you must keep a filename in the abiheader div, with a REST option (GET, etc) at the front, the example file number, and with a .txt extension. e.g. file name `DELETE_adm_dcs_X.0002.txt` 
* The example pages are designed to be manually included in wiki API reference docs. It is possible to search or retrieve page content (using the scripts written by Sarah Maddox, for example) and grep for included page names.

### ReadPagesAndUpdateWiki.py
 * Run with Python 3
 * Read the wiki pages and check for filenames, store in the dictionary
 * Read the 0001 files and store in the dictionary (overwrite existing wiki files)
 * Create and update pages  
 * Note there is a "test" parameter that you can set to run a test on a test wiki that will create different output files 

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
|adminSubdir | admin | Directory under the project directory where admin files are stored |
|template | template.mustache | Mustache template for creating Confluence wiki page or what 
|MTversion | 3.2 | Default media type version for the API, which is the current product version |
|overwriteFiles | y | Overwrite existing example files in the subdir |
|writeWikiPages| y | Update wiki pages |


### Results files
The script creates two output files:
 * A JSON file from the dictionary
 * A wiki markup file with information on the changes to pages


