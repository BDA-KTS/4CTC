# 4TCT 
## A 4chan Text Collection Tool

## Author & Maintainer
- Jack H. Culbert
- jack.culbert@gesis.org
- https://orcid.org/0009-0000-1581-4021
- Maintainer in Gesis: Po-Chun Chang 
- po-chun.chang@gesis.org

## Resource Paper
You can find the associated technical report [here](https://arxiv.org/abs/2307.03556).
Please reference this paper if you use this tool in research or your own projects.

## Attribution and Maintenance Information
Please make sure to credit and cite the author information/technical report for works that are achieved using this repo. And note that Jack will not be maintaining this repo. For any question please refer to the maintainer in Gesis.

## Disclaimer
Both the author and GESIS are not affiliated, associated, authorized, endorsed by, or in any way officially connected with 4chan, or any of its subsidiaries or its affiliates. The official 4chan website can be found at [4chan.org](https://www.4chan.org).

The names 4chan as well as related names, marks, emblems and images are registered trademarks of their respective owners.

Please be aware 4chan may serve offensive and/or illegal images and texts, and it is the sole responsibility of the user to vet and remove material that may be illegal in their jurisdiction. The author and GESIS shall have unlimited liability for damages resulting from injury to life, limb or health and in the event of liability under the German Product Liability Act (Act on Liability for Defective Products). This shall also apply in the event of a breach of so-called cardinal obligations, i.e. obligations the breach of which would jeopardize the purpose of the contract and the performance of which the user as contracting party may therefore reasonably rely on. Otherwise, the author and GESIS shall only be liable for intent and gross negligence.

## Repo Structure
- The entire codes are resides in ```src/```, with ```requester.py``` being the main flow that handles the pipeline of data collection that uses instantiated board class from ```board.py``` to request information from each boards. ```utils.py``` contains helper functions that handle datetime information and logger. 
- By default ```data/``` directory will be created for storing the collected the data once the program start running.
- ```docs/``` is used for documentation purposes with sphinx. It is not relevent to the execution of the program.

## Usage
- Install the requirements found in ```requirements.txt```, e.g. with ```pip install -r requirements.txt```
- Run ```python src/requester.py``` from the root directory.

### Target specific boards for collection
- To select which boards to collect the textual data from, use the `-b` parameter to pass requester.py a list containing the strings of the short form of the board name e.g. ```python src/requester.py -b adv toy sci``` to include only these boards.

- To exclude a selection of boards from the tool, pass a list as above with the `-b` parameter and also include a `-e`.

### Other flags
For more information please run ```python src/requester.py -h```

#### Versions
Tested on Python 3.10.2 and 3.11.4

## Overview of functionality
### First time initialisation
1. Two directories are created for logs, and the data (saves/"the current date")
1. The requester will first query the 4chan API to find the current list of boards, if present the include or exclude boards are selected or removed from the list. 
    * For every board resulting from this process, two subdirectories folder will be created in the data folder, one for storing the threads and one for the thread on each board.
2. The requester then goes through each board to find a list of threads on each board. 
    * These are saved to the threads_on_boards folder
3. The requester then requests the posts on each board. 
    * The data is saved to a subfolder of threads, with a name consisting of the thread id and the time of first observance.
4. The loop repeats by checking each board for new and dead threads, then querying the new and live threads.
### Reruns
The requester attempts to pick up from previous runs by observing the state of the saves directory. If this is deleted it will act as from fresh.
### Logs
Debug logs are set to capture each API call and are as such, very detailed (approx 80 times as large as info). By default the info log is output to terminal.

## Output Example
After running the program, in the `saves/"the current date"`, you should see the `.json` files for the scraped contents. Refer [4chan official API documentation](https://github.com/4chan/4chan-API/blob/master/pages/Threads.md) to understand what each field means for the downloaded data.

## Limits
Please ensure you follow the 4Chan API Rules and Terms of Service found [here](https://github.com/4chan/4chan-API/blob/master/README.md).

At time of writing these are: 
### API Rules ###
Below official API rules have been made as default setting for this repo. They are listed here for those who are interested in modifying the repo.
1. Do not make more than one request per second. To change the waiting time, use `--request-time-limit {your_ideal_value}` flag to set your ideal waiting time (only value above 1 will be accepted).
2. Thread updating should be set to a minimum of 10 seconds, preferably higher.
3. Use [If-Modified-Since](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-Modified-Since) when doing your requests.
4. Make API requests using the same protocol as the app. Only use SSL when a user is accessing your app over HTTPS.

### API Terms of Service ###

1. You may not use "4chan" in the title of your application, product, or service.
2. You may not use the 4chan name, logo, or brand to promote your application, product, or service.
3. You must disclose the source of the information shown by your application, product, or service as 4chan, and provide a link.
4. You may not market your application, product, or service as being "official" in any way.
5. You may not clone 4chan or its existing features/functionality. Example: Don't suck down our JSON, host it elsewhere, and throw ads around it.
6. These terms are subject to change without notice.
## References
Thank you very much to the team behind the [4Chan API](https://github.com/4chan/4chan-API)!
