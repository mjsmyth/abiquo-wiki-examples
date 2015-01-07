# abiquo-wiki-examples

Automation of Abiquo API examples in the Abiquo wiki with a set of 3 Python scripts using Python 2.7.

Copy the sample properties file to the real properties file name and change values for your system.

There are three scripts: `process_api_examples.py`, `read_files_confluence_pages.py` and `update_confluence_pages.py`

## process_api_examples.py
Read the requests log and create example files in Confluence storage format for all requests with success status code (<400). 
## read_files_confluence_pages.py
Get the 0001 example files and check if a Confluence page already exists and if it has been modified. Create three files:
1 **wiki_all_files.json.txt**: all 0001 files, 
2 **wiki_force_update.json.txt**: updated files (e.g. different user is modifier, different filename: e.g. 0002 file,  *abc_XXX.0001.txt* in *abc_xxx* page)
3 **wiki_prohibited.json.txt**: prohibited files (e.g. licenses)
You can edit any of these files to change which pages will be updated by the next script.
## update_confluence_pages.py
Read *wiki_all_files.json.txt*. If Force update option is set, update pages found in *wiki_force_update.json.txt*. Always ignore prohbited files.  
