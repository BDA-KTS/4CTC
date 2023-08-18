from pathlib import Path
import time
from datetime import datetime, timedelta
import requests
import json
import os
from utils import get_time, get_day

class Board:
    """
    This is a board object that handles the request, saving, tracking to a particular board
    """
    def __init__(self, board_code, logger):

        # Board Code
        self.board_code = board_code
        
        # Logger
        self.logger = logger

        # API address
        self.thread_list_api = f'https://a.4cdn.org/{self.board_code}/threads.json' #TODO import from static definitions
        self.thread_content_api_prefix = f'https://a.4cdn.org/{self.board_code}/thread' #TODO +/op_id +.json import from static definitions
        
        # Saving paths
        self.base_save_path = Path().resolve() / "data"
        self.update_saving_folder_info()

        # For data request interval
        self.thread_list_last_request = None
        self.thread_content_last_request = {} # Its only useful for adding headers for thread content API
        self.thread_list_request_interval = 10 #TODO Static?
        self.thread_content_request_interval = 1 #TODO Static?

        # Not sure
        self.tracking_threads = {} # threads that are observed for their status including last update and death 
        self.online_threads = []

        # Load Saved Files
        self.get_previously_saved_info()

    def update_saving_folder_info(self): #TODO, need to match the new logic where timestamp does not result duplicate file
        """
        Set up all the saving path in the class, this method is called repeatedly because save path is related to current timestamp
        """        
        timestamp = get_day()
        # #TODO, static and argument accept?
        self.thread_list_path = self.base_save_path / "saves" / timestamp / "threads_on_boards"
        self.thread_content_path = self.base_save_path / "saves" / timestamp / "threads" / self.board_code
        self.thread_list_path.mkdir(parents=True, exist_ok=True)
        self.thread_content_path.mkdir(parents=True, exist_ok=True)

    def get_previously_saved_info(self):
        """
        Load previously saved data into the class to prevent downloading the same thread and help monitoring update
        """
        self.logger.debug("Checking for past captures of old threads in previous instances")
        
        for prev_thread_list_path in self.thread_list_path.iterdir(): # get file names inside the folder
            if prev_thread_list_path.name.split("_")[0] == str(self.board_code): 
                prev_thread_counts = 0
                with open(prev_thread_list_path, "r") as prev_thread_list_file:
                    prev_threads = json.load(prev_thread_list_file)
                    for page in prev_threads:
                        for threads in page["threads"]:
                            self.tracking_threads[str(threads["no"])] = [int(threads["last_modified"]), int(threads["replies"])]
                            prev_thread_counts += 1
                self.logger.debug(f"{prev_thread_counts} past captures of old threads in previous instances of {self.board_code} discovered")
                # old_monitor_dict will lookg like old_monitor_dict['po']['thread_no'] = [last modified, reply counts]
                self.logger.debug(
                    f"{prev_thread_counts} past captures of old threads in previous instances discovered"
                )
                return

        self.logger.info(f"No previous thread information for /{self.board_code}/, no old threads to monitor")        

    def get_online_thread_list(self):
        """Request the list of thread IDs on the board
        :return: thread id list
        """
        #TODO this can probably be a class too because it can be written in the same way like get_thread_content
        self.logger.debug(f"Board /{self.board_code}/ thread information requested")
        if self.thread_list_last_request == None:
            request_response = requests.get(self.thread_list_api)
        else:
            thread_list_request_interval = datetime.now() - datetime.fromtimestamp(time.mktime(self.thread_list_last_request)) 
            if thread_list_request_interval < timedelta(seconds=10):
                sleeping = 10 - thread_list_request_interval.total_seconds()
                self.logger.info(f"Sleeping for {sleeping} seconds: time between requests for threads on board {self.board_code} too short")
                time.sleep(sleeping)

            last_modified_time_header = self._format_time_header(self.thread_list_last_request)
            request_response = requests.get(self.thread_list_api, headers=last_modified_time_header)

        if request_response.status_code == 200:
            self.thread_list_last_request = datetime.now().timetuple()
            return request_response.json()

        if request_response.status_code == 304: 
            self.logger.info(f"No new threads on board /{self.board_code}/")
            return None
        
        if request_response.status_code == 404: #TODO should probably implement retry mechanism, if the website is down our program is also down which is not good
            self.logger.info(f"Error when trying to fetch /{self.board_code}/")
            raise Exception(f"404 when trying to fetch /{self.board_code}/")

    def save_thread_list(self, thread_list):
        """Save the thread ID list in local directory
        """
        self.update_saving_folder_info()

        #TODO, need to match the new logic where timestamp does not result duplicate file
        #TODO, static and argument accept?
        filename = self.board_code + get_time() + ".json"

        # delete old thread list
        for prev_thread_list_path in self.thread_list_path.iterdir():
            if prev_thread_list_path.name.split("_")[0] == str(self.board_code): 
                prev_thread_list_path.unlink()
        
        with open(self.thread_list_path / filename, "w") as outfile:
            json.dump(thread_list, outfile, indent=2)

    def get_thread_content(self, thread_id):
        """Based on given thread ID, request the content of the thread

        :return: thread content
        """        
        thread_api_address = self.thread_content_api_prefix + "/" + str(thread_id) + ".json"

        request_attempt = 0
        request_response = None

        while self._check_retry(request_response, thread_id, request_attempt) == True:
            if thread_id not in self.thread_content_last_request:
                # download thread content without header
                request_response = requests.get(thread_api_address)
                # record download time to thread_content_last_request if request is successful
                if request_response.status_code in [200, 304]:
                    self.thread_content_last_request[thread_id] = datetime.now().timetuple()
            else:
                # get last request time for this thread
                last_modified_time_header = self._format_time_header(self.thread_content_last_request[thread_id])
                # download thread content with header
                request_response = requests.get(thread_api_address, headers=last_modified_time_header)
                # record download time to thread_content_last_request if request is successful
                if request_response.status_code in [200, 304]:
                    self.thread_content_last_request[thread_id] = datetime.now().timetuple()

            request_attempt += 1
        time.sleep(self.thread_content_request_interval)
        return request_response.json() if request_response is not None else None

    def save_thread_content(self, thread_id, thread_content):
        """Save the thread content in local directory
        """
        if thread_content is None:
            self.logger.warning(f"Can't save board {self.board_code}, post {thread_id}, likely 404 during requesting, skip saving")
            return

        self.update_saving_folder_info()
        #TODO, need to match the new logic where timestamp does not result duplicate file
        #TODO, static and argument accept?
        filename = str(thread_id) + get_time() + ".json"
        fullname = self.thread_content_path / filename

        for saved_thread_path in self.thread_content_path.iterdir():
            # check if the thread id is found in saved content, then delete it and save a new one
            if int(saved_thread_path.name.split("_")[0]) == int(thread_id): 
                #TODO this insure there is only one copy for one post, so date naming system needs to be changed
                #TODO as well as moving dead threads to an fully saved folder
                #TODO name the still tracking, saving folder as something like tracking saved
                os.remove(saved_thread_path)
            
        with open(fullname, "w") as outfile:
            json.dump(thread_content, outfile, indent=2)

    def get_threads_to_update(self, online_threads):
        """Comapre the currently tracking thread and the thread online, see if there are thread die out or require update
        :return: thread list require update (download)
        """
        threads_to_update = []

        death_count = 0 # previously saved thread it does not match the ones on the current extract threadlist, meaning it's long gone and dead
        birth_count = 0 # added new board's each thread or thread id does not exist in the previously saved id (monitoring_threads), but id exist in the currently extracted threadlist, meaning its a new thread
        update_count = 0 # when thread in threadlist matches id on monitoring_threads, and its last update is newer, then update it
        
        online_threads = self._process_online_threads(online_threads) # basically the current threads on board

        # Check if any tracking thread is dead(disappeared) online
        dead_thread_ids = []
        for thread_id in self.tracking_threads:
            if thread_id not in online_threads:
                self.logger.debug(f"Thread died: /{self.board_code}/{thread_id}")
                death_count += 1
                dead_thread_ids.append(thread_id)
        
        # Remove dead threads from tracking list and request history
        for dead_thread_id in dead_thread_ids:
            del self.tracking_threads[dead_thread_id]
            if dead_thread_id in self.thread_content_last_request:
                del self.thread_content_last_request[dead_thread_id]

        for thread_id in online_threads:
            if thread_id in self.tracking_threads:
                # online thread is already being tracked, update if needed
                tracked_last_modified_time, _ = self.tracking_threads[thread_id]
                online_last_modified_time, _ = self.tracking_threads[thread_id]
                if (tracked_last_modified_time < online_last_modified_time):
                    self.logger.debug(f"Thread updated: /{self.board_code}/{thread_id}")
                    self.tracking_threads[thread_id] = online_threads[thread_id]
                    threads_to_update.append(thread_id)  # posts to update records the board and thread we need to download the content of 
                    update_count += 1
                else:
                    self.logger.debug(f"Do not need to update thread /{self.board_code}/{thread_id}")
            else:
                # online thread is not tracked, it's a new thread
                self.logger.debug(f"New thread: /{self.board_code}/{thread_id}")
                self.tracking_threads[thread_id] = online_threads[thread_id]
                threads_to_update.append(thread_id)
                birth_count += 1

        self.logger.info(f"Thread deaths in previous iteration: {death_count}")
        self.logger.info(f"Thread births in previous iteration: {birth_count}")
        self.logger.info(f"Thread updates in previous iteration: {update_count}")
        self.logger.info(f"{len(self.tracking_threads)} threads are currently being monitored.")

        return threads_to_update

    def _process_online_threads(self, online_threads):
        proccessed_threads = {}
        for page in online_threads:
            for thread in page["threads"]:
                proccessed_threads[str(thread["no"])] = [int(thread["last_modified"]), int(thread["replies"])]
        return proccessed_threads

    def _check_retry(self, request_response, thread_id, attempt):
        # TODO can change this to strategy mapping, having a factory class that generate strategy mapping for threadlist and thread, and a dict to map to return strategy and log info
        if request_response == None:
            return True
            
        if request_response.status_code == 304: # if the content does not change since last request, return none
            self.logger.debug(f"Thread {thread_id} not updated since last request") 
            return False
        
        if request_response.status_code == 200:
            self.logger.debug("Recieved answer")
            return False
        
        error_message = f"Request for thread {thread_id} on board /{self.board_code}/ was unsuccessful with error code {request_response.status_code}."
        if request_response.status_code == 404:
            self.logger.warning(f'{error_message} Skipping')
            return False
        
        if attempt <= 5:
            self.logger.error(f'{error_message} Current Attempt: {attempt}, now entering next attempt')
            time.sleep(self.thread_content_request_interval * 5)
            return True
        else:
            self.logger.warning(f'{error_message} Returning None')
            return False

    def _format_time_header(self, since):
        since = time.gmtime(time.mktime(since))
        return {"If-Modified-Since": time.strftime("%a, %d %b %Y %H:%M:%S GMT", since)}