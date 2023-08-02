import argparse
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import math
import requests


class requester:
    def __init__(
        self,
        monitor: bool, # always True from the starting function
        run_in_docker: bool, # -d flag
        boards: list = None, # boards to be scraped
        exclude_boards: bool = False, # if this is true the boards will not be collected
        request_time_limit: float = 1, # no arugment passed for this one
        stream_log_level=logging.INFO,
        logfolderpath: str = "logs",
    ):
        if run_in_docker:
            self._base_save_path: Path = Path("/data") # : defined object type, like the above lines 
        else:
            self._base_save_path: Path = Path().resolve() / "data" # .resolve() creates absolute path
        self._save_debuglog = True
        self._stream_log_level = stream_log_level
        self._setup_logging(logfolderpath) #set up self._logger ...etc

        self.monitor: bool = monitor
        self._include_boards: list = boards
        self._exclude_boards: bool = exclude_boards
        self._request_time_limit: float = request_time_limit
        self._check_new_boards: bool = True # always check new boards
        self._last_requested = {}

        self.last_request = None

        if self.monitor is True:
            self.begin_monitoring() # go into the main program

    def begin_monitoring(self):
        self._logger.info("Beginning monitoring")
        self._logger.info(f"Storing data in path: {self._base_save_path}")
        
        self.monitoring_boards = []
        self.monitoring_threads = {}
        self._threads_last_checked = {}
        self._logger.debug("Initialising Monitoring Thread")
        self._monitor_thread = threading.Thread(target=self._begin_monitoring) # turn the function into thread
        self._logger.debug("Starting Thread")
        self._monitor_thread.start() # start the thread #TODO but isn't it just one thread here? how to achieve multithread
        self._logger.debug("Monitoring Started") 

    def end_monitoring(self):
        # not being used as well, could be used to terminiate it from outer command
        self._logger.info("Ending loop and closing monitoring thread")
        self.monitor = False
        self._monitor_thread.join()
        self._logger.info("Closed monitoring thread")

    def _load_old_monitors(self): # begin_monitoring -> _begin_monitoring -> here
        """
        Mainly to setup self.monitoring_threads, which is essentialy threads that have been previously monitored
        self.monitoring_threads[board_code]['thread_no'] = [last modified, reply counts]
        there could be old monitored board but if this round it is not specified then the old monitored board data will not be looked
        """
        self._update_monitoring_boards() # self.monitoring_boards is set #TODO, this should probably be moved out, its not relvant to old board
        self._logger.debug(
            "Checking for past captures of old threads in previous instances"
        )
        old_monitor_dict = {}
        old_threads = 0
        for board in self.monitoring_boards:
            timestamp = self._get_day()
            boardfolderpath = (
                self._base_save_path / "saves" / timestamp / "threads_on_boards"
            )
            boardfolderpath.mkdir(parents=True, exist_ok=True)
            threadpath = self._base_save_path / "saves" / timestamp / "threads" / board
            threadpath.mkdir(parents=True, exist_ok=True)
            # boardfolderpath is for threads infomation on a board  saves/2023_07_12/threads/ for example
            # one json for each board
            # threadpath is for threads saves/2023_07_12/threads/po for example
            # one json for each thread(post and their responses)

            good_boardpath_found = False # good_boardpath_found basically means if the board was monitored before, not neccessary mean its a good board
            for boardpath in boardfolderpath.iterdir(): # get file names inside the folder
                if boardpath.name.split("_")[0] == str(board): 
                    # check the prefix of each file name (because the prefix is the board code)
                    # if there are a match that means that board was previously monitored
                    good_boardpath = boardpath 
                    good_boardpath_found = True

            if not good_boardpath_found:
                self._logger.info(
                    f"No previous thread information for /{board}/, no old threads to monitor"
                )
                continue # if not monitor previously, we have no previous thread info to load from this board
            old_monitor_dict[board] = {}

            # here basically records each thread(post) no prevously records and their last_modified and reply info 
            with open(good_boardpath, "r") as prev_threads_file:
                prev_threads = json.load(prev_threads_file)
                for page in prev_threads:
                    for threads in page["threads"]:
                        old_monitor_dict[str(board)][str(threads["no"])] = [
                            int(threads["last_modified"]),
                            int(threads["replies"]),
                        ]
                        old_threads += 1
            self._logger.debug(
                f"{len} past captures of old threads in previous instances of {board} discovered"
            )
            # old_monitor_dict will lookg like old_monitor_dict['po']['thread_no'] = [last modified, reply counts]
        self.monitoring_threads = old_monitor_dict
        self._logger.debug(
            f"{old_threads} past captures of old threads in previous instances discovered"
        )

    def set_include_exclude_boards(
        self, include_boards: list = None, exclude_boards: bool = False
    ):
        # the function is not used!! seems to be a function that can accept command to add new board for monitoring without stopping the current program
        self._logger.info("Updating boards to monitor")
        self._include_boards = include_boards
        self._exclude_boards = exclude_boards
        if include_boards is None and not exclude_boards:
            self._check_new_boards = False
        else:
            self._check_new_boards = True

    def _update_monitoring_boards(self): # begin_monitoring -> _begin_monitoring -> _load_old_monitors -> here
        """_summary_
        Check self._include_boards and self._exclude_boards
        if exclude_boards then self._include_boards become the ones not to monitor
        eventually self.monitoring_boards will be the ones for monitoring
        """
        self._logger.debug("Updating monitor board list (checking)")
        if self._include_boards is not None and not self._exclude_boards:
            self.monitoring_boards = self._include_boards # monitor the _include_boards
        elif self._include_boards is not None and self._exclude_boards: # monitor boards other than the _include_boards
            self.monitoring_boards = list( 
                set(self._set_board_list()).difference(self._include_boards)
            )
        else: # if no boards provided then all boards are monitored
            self.monitoring_boards = self._set_board_list()
        self._check_new_boards = False

    def _begin_monitoring(self): # coming from begin_monitoring function
        self._logger.debug("_begin_monitoring entered")
        self._load_old_monitors() # determine what boards to monitor in this run
        #  +  get monitoring board and old threads that has monitored
        self._logger.debug("Old monitors retrieved")
        while self.monitor is True:
            self._logger.debug("Started loop")
            if self._check_new_boards: #it was set to False when _update_monitoring_boards was executed in _load_old_monitors
                # this will never be true after the _update_monitoring_boards was executed in _load_old_monitors
                # so technically it will only be run once
                # unless set_include_exclude_boards is actulally used, but it is not at the moment
                self._logger.debug("Started updating monitoring boards")
                self._update_monitoring_boards()
            self._update_monitoring_threads() # prepare self._posts_to_update and also update what's currently being monitored in self.monitoring_threads
            #TODO the naming is confusing because it doesnt reflect the _posts_to_update part within the fuction
            self._logger.debug("updating posts on monitoring list")
            self._update_posts_on_monitoring_threadlist() # based on self._posts_to_update this part will be about saving the threads content
            #TODO the naming is confusing because it has a big part about actually saving the thread content
            self._logger.debug("Ended loop")

    
    def _delete_threads(self, board, threads):
        for thread in threads:
            del self.monitoring_threads[board][thread]
            #TODO, not sure about this part # answered: the "thread" is created in get_thread(), its the time stamp when the thread content is donwloaded
            if thread in self._last_requested[board]["threads"]: # if old monitored thread not found in current board
                # meaning it died( last modified and replies do not match, then deleted it from last_requested)
                # deleted it 
                del self._last_requested[board]["threads"][thread]
                
    def _update_monitoring_threads(self):
        """Main usage is to figure out what threads need to be downloaded, the info is stored into self._posts_to_update [[board, thread]]
        monitoring_threads is also updated based on the information from threads_on_boards (in the beginning this came from loading the saved threads)
        """
        self._logger.info("Beginning search for threads to monitor")
        self._posts_to_update = []
        death_count = 0 # previously saved thread it does not match the ones on the current extract threadlist, meaning it's long gone and dead
        birth_count = 0 # added new board's each thread or thread id does not exist in the previously saved id (monitoring_threads), but id exist in the currently extracted threadlist, meaning its a new thread
        update_count = 0 # when thread in threadlist matches id on monitoring_threads, and its last update is newer, then update it
        for board in self.monitoring_boards:
            self._logger.info(f"Searching for threads in {board}")
            #TODO should saparate to threadlist and thread part instead of putting into one single function
            threads_json = self.get_and_save_single_board_threadlist(
                board, with_return=True
            )
            if threads_json is None:
                continue # if there is no update of the threadlist information (including thread id, last modified and reply counts)
            # then it means threads on this board has not changed, then we can move on
            threads_on_board = {} # basically the current threads on board
            for page in threads_json:
                for thread in page["threads"]:
                    threads_on_board[str(thread["no"])] = [
                        int(thread["last_modified"]),
                        int(thread["replies"]),
                    ]
                    #threads_on_board[thread_no] = [last_modified, replies]
            if board in self.monitoring_threads: # monitoring_threads comes from reading the saved data before program start
                # self.monitoring_threads['po']['thread_no'] = [last modified, reply counts]
                to_be_delete = []
                for thread in self.monitoring_threads[board]:
                    if thread in threads_on_board: #TODO, will monitoring_threads be updated after this? becuase it only starts from saved data
                        pass
                    else:
                        self._logger.debug(f"Thread died: /{board}/{thread}")
                        death_count += 1
                        to_be_delete.append(thread)
                self._delete_threads(board, to_be_delete)
                # self._last_requested[board_code]["board"] = datetime.now().timetuple()
                # get_thread add the part about ['threads']
                for thread in threads_on_board: # this is key, so its the thread id
                    # update existing threads
                    if thread in self.monitoring_threads[board]:
                        if (
                            self.monitoring_threads[board][thread][0] # [last modified, replies]
                            < threads_on_board[thread][0]
                        ):
                            self._logger.debug(f"Thread updated: /{board}/{thread}")
                            self.monitoring_threads[board][thread] = threads_on_board[
                                thread # update its last modified and replies
                            ]
                            self._posts_to_update.append([board, thread])  # posts to update records the board and thread we need to download the content of 
                            update_count += 1
                        else:
                            self._logger.debug(
                                f"Do not need to update thread /{board}/{thread}"
                            )
                    else:
                        # add new threads
                        self._logger.debug(f"New thread: /{board}/{thread}")
                        self.monitoring_threads[board][thread] = threads_on_board[
                            thread
                        ]
                        self._posts_to_update.append([board, thread]) # posts to update records the board and thread we need to download the content of 
                        birth_count += 1
            else:
                # this handles where the entire boared was not saved in the past in # monitoring_threads which comes from reading the saved data before program start
                self._logger.debug(f"New Board: updated to monitor list {board}")
                self.monitoring_threads[board] = threads_on_board
                for thread in threads_on_board:
                    self._logger.debug(f"New thread: /{board}/{thread}")
                    self._posts_to_update.append([board, thread])
                    birth_count += 1

        self._logger.info(f"Thread deaths in previous iteration: {death_count}")
        self._logger.info(f"Thread births in previous iteration: {birth_count}")
        self._logger.info(f"Thread updates in previous iteration: {update_count}")
        self._logger.info(
            f"{len(self.monitoring_threads[board])} threads found to monitor."
        )

    def _update_posts_on_monitoring_threadlist(self):
        # main point is to use get_and_save_thread()
        number_posts_in_iteration = len(self._posts_to_update)
        i = 1
        prev_board = ""
        for board, post in self._posts_to_update:
            if prev_board != board: # in _posts_to_update, post from same board are put together, so if this changes that means we are going to process a new board
                self._logger.info(f"Updating posts in {board}")
                prev_board = board
            start_time = time.time()
            self.get_and_save_thread(board, post) # key function #TODO, why is it hidden here?

            #below are simple report on how long long it will take based on the number of remaining post to be saved
            current_time_diff = (time.time() - start_time) * (
                number_posts_in_iteration - i
            )
            self._logger.debug(
                f"{i}/{number_posts_in_iteration}: Capturing post {post} in /{board}/ approximate seconds remaining in iteration {current_time_diff:n}"
            )
            i += 1

    def _set_board_list(self):
        boards_info = self.get_chan_info_json()
        codes = [board["board"] for board in boards_info["boards"]]
        return codes

    @staticmethod
    def _get_time():
        now = datetime.utcnow()
        return now.strftime("_%H_%M_%S")

    @staticmethod
    def _get_day():
        now = datetime.utcnow()
        return now.strftime("%Y_%m_%d")

    @staticmethod
    def _get_full_time():
        now = datetime.utcnow()
        return now.strftime("%Y_%m_%d_%H_%M_%S")

    def _check_time_and_wait(self):
        if self.last_request is None:
            self.last_request = time.time()
        else:
            cur_time = time.time()
            if cur_time - self.last_request >= self._request_time_limit:
                self.last_request = cur_time
            else:
                time.sleep(self._request_time_limit - (cur_time - self.last_request))
                self.last_request = time.time()

    def get_chan_info_json(self):
        self._check_time_and_wait()
        self._logger.debug("chan information requested")
        r_boards = requests.get("http://a.4cdn.org/boards.json")
        return r_boards.json()

    @staticmethod
    def _format_if_mod_since_header(since):
        since = time.gmtime(time.mktime(since))
        return {"If-Modified-Since": time.strftime("%a, %d %b %Y %H:%M:%S GMT", since)}

    def get_single_board_threadlist(self, board_code:str):
        """get a list of all the threads within the proccessed single board
        if the board's thread list did not change since last request, return None

        :param board_code: the code of the board that's being processed (ie. po)
        :type board_code: str
        :return: none or a json object of all the threads within the proccessed single board 
        :rtype: None or a json object
        """
        self._check_time_and_wait()
        self._logger.debug(f"Board /{board_code}/ thread information requested")
        if board_code not in self._last_requested:
            # when the program first started, the self._last_requested is empty 
            # if there is no previous request time stamp
            self._last_requested[board_code] = {}
            self._last_requested[board_code]["threads"] = {}
            r_thread_list = requests.get(
                "https://a.4cdn.org/" + board_code + "/threads.json"
            )
            # https://a.4cdn.org/po/threads.json example api
        else:
            board_request_time = datetime.now() - datetime.fromtimestamp(
                time.mktime(self._last_requested[board_code]["board"])
            ) 
            if board_request_time < timedelta(seconds=10):
                # seems like request between a board's thread list will wait at least 10 seconds 
                sleeping = 10 - board_request_time.total_seconds()
                self._logger.info(
                    f"Sleeping for {sleeping} seconds: time between requests for threads on board {board_code} too short"
                )
                time.sleep(sleeping)
            r_thread_list = requests.get(
                "https://a.4cdn.org/" + board_code + "/threads.json",
                headers=self._format_if_mod_since_header(
                    self._last_requested[board_code]["board"]
                ), #the usage of header provide a timestamp, the api will only provide data if the content has been modifited after that timestamp
                # else it gives 304
            )

        self._last_requested[board_code]["board"] = datetime.now().timetuple()
        if r_thread_list.status_code == 304: 
            self._logger.info(f"No new threads on board /{board_code}/")
            return None
        return r_thread_list.json()

    def get_thread(self, board_code:str, op_ID:int):
        # get the thread content info and return r_thread.json()
        self._check_time_and_wait() #TODO read this to know about the waiting time detail
        if board_code not in self._last_requested[board_code]["threads"]:
            r_thread = requests.get(
                "https://a.4cdn.org/" + board_code + "/thread/" + str(op_ID) + ".json"
            )
        else: # else get the use header to check whether it is updated and then download the new version
            # but the confusing part is everything that can come here is already decided to be updated in previous functions
            # it seems a thread can still have no update even though the thread information says the last modified has being more recent
            r_thread = requests.get(
                "https://a.4cdn.org/" + board_code + "/thread/" + str(op_ID) + ".json",
                headers=self._format_if_mod_since_header(
                    self._last_requested[board_code]["threads"][op_ID]
                ),
            )
        self._last_requested[board_code]["threads"][op_ID] = datetime.now().timetuple()

        countdown = 1
        while r_thread.status_code not in [200, 304]: # 200 means success 304 means no update to be download
            # this while loop is simply a retry attempt that wait for request_time_limit * 5
            if r_thread.status_code == 404:
                self._logger.warning(
                    f"Request for thread {op_ID} on board /{board_code}/ was unsuccessful with error code {r_thread.status_code}, skipping"
                )
                return None
            elif countdown < 6:
                self._logger.error(
                    f"Request for thread {op_ID} on board /{board_code}/ was unsuccessful with error code {r_thread.status_code}, trying {countdown} more times"
                )
            else:
                self._logger.warning(
                    f"Request for thread {op_ID} on board /{board_code}/ was unsuccessful with error code {r_thread.status_code}, returning None"
                )
                return None
            time.sleep(self._request_time_limit * 5)
            r_thread = requests.get(
                "https://a.4cdn.org/" + board_code + "/thread/" + str(op_ID) + ".json",
                headers=self._format_if_mod_since_header(
                    self._last_requested[board_code]["threads"][op_ID]
                ), #the usage of header provide a timestamp, the api will only provide data if the content has been modifited after that timestamp
                # else it gives 304
            )
            self._last_requested[board_code]["threads"][
                op_ID
            ] = datetime.now().timetuple() # update the last attempt for retry
            countdown += 1
        if r_thread.status_code == 304: # if the content does not change since last request, return none
            self._logger.debug(f"Thread {op_ID} not updated since last request") # so it seems that a thread might not be updated even if it was decided to be updated from using lastest_modified time 
            return None
        elif r_thread.status_code == 200:
            self._logger.debug("Recieved answer")
        time.sleep(self._request_time_limit)
        return r_thread.json()

    def get_and_save_chan_info(self, outpath:Path=None, filename:str=None):
        timestamp = self._get_day()
        if outpath is None:
            outpath = self._base_save_path / "saves" / timestamp
        if filename is None:
            filename = "boards.json"
        outpath.mkdir(parents=True, exist_ok=True)
        with open(outpath / filename, "w") as outfile:
            json.dump(self.get_chan_info_json(), outfile, indent=2)

    def get_and_save_single_board_threadlist(
        self, board_code:str, outpath:Path=None, filename:str=None, with_return:bool=False
    ):
        timestamp = self._get_day()
        if outpath is None:
            outpath = self._base_save_path / "saves" / timestamp / "threads_on_boards"
            #./data/saves/2023_07_12/threads_on_boards/
        if filename is None:
            filename = board_code + self._get_time() + ".json"
            # po_12_15_10.json   _hour_minute_seconds
        outpath.mkdir(parents=True, exist_ok=True)
        threadlist = self.get_single_board_threadlist(board_code)
        #TODO confusing naming of get_and_save_single_board_threadlist and get_single_board_threadlist
        #TODO need to simplfy this
        if threadlist is None:
            return None
        #if there is no change to the threadlist then return None
        #note that the first request will always result in the below, because there is no previous request to compare to
        for threads in outpath.iterdir():
        #if there are changes, first delete all the saved threadlist json and save the new one in
            if threads.name.split("_")[0] == str(board_code):
                threads.unlink()
        with open(outpath / filename, "w") as outfile:
            json.dump(threadlist, outfile, indent=2)
        if with_return:
            return threadlist

    def get_and_save_thread(self, board_code:str, op_ID:int, outpath:Path=None, filename:str=None):
        # it only save the threads that are new or updated
        # to determine if a thread is updated, it was determined based on the last modified component from the 4chan
        # so ideally if a post is dead, it will not be put for saved again
        # if a post is updated within the same day, since the file name is based on _get_time which is hour minute second
        # there could be double copy of same post 這邊不確定要搞清楚
        timestamp = self._get_day()
        if outpath is None:
            outpath = (
                self._base_save_path / "saves" / timestamp / "threads" / board_code
            )
        outpath.mkdir(parents=True, exist_ok=True)

        if filename is None:
            filename = str(op_ID) + self._get_time() + ".json"
        fullname = outpath / filename
        new_thread = True
        for threads in outpath.iterdir():
            if int(threads.name.split("_")[0]) == int(op_ID): # if the existing file has same id to the posts_to_update thread id, then update that file directly
                # meaning this thread is not new
                with open(threads, "r+") as outfile:
                    try:
                        data = json.load(outfile)
                    except json.decoder.JSONDecodeError as jerror:
                        self._logger.warning(
                            f"Loading JSON file {threads} caused error {jerror}, continuing to writing new file rather than append. Board {board_code}, post {op_ID}"
                        )
                        continue
                    else:
                        to_update = self.get_thread(board_code, op_ID) #TODO another big function hidden here
                        if to_update is None:
                            self._logger.warning(
                                f"Likely 404 caused no return for, skipping | board {board_code}, post {op_ID}"
                            )
                            new_thread = False
                            continue
                        data.update(to_update) 
                        # to see if new_thread might be result in extra copies
                        #TODO, the folder is based on the date, what if the date changes? the same threads will be used to compare to the new folder
                        # 不會 因為它會在 threads on board 上面所以不會被更新
                        # 但如果發生更新了 這邊又對比不到前一天的資料 就會存到新的資料夾裡
                        outfile.seek(0)
                        json.dump(data, outfile, indent=2) #json dump overwrite content inside
                        new_thread = False # 
        if new_thread is True:
            with open(fullname, "w") as outfile:
                json.dump(self.get_thread(board_code, op_ID), outfile, indent=2)

    def _setup_logging(self, logfolderpath:Path):
        logfolder = self._base_save_path / logfolderpath
        logfolder.mkdir(parents=True, exist_ok=True)

        self._logger = logging.getLogger("4chan_requester")
        self._logger.setLevel(logging.DEBUG)
        self._log_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s: %(threadName)s - %(message)s"
        )

        self._streamlogs = logging.StreamHandler()
        self._streamlogs.setLevel(self._stream_log_level)
        self._streamlogs.setFormatter(self._log_formatter)
        self._logger.addHandler(self._streamlogs)

        self._infologpath = logfolder / ("info_log" + self._get_full_time() + ".log")
        self._infologfile = logging.FileHandler(self._infologpath)
        self._infologfile.setLevel(logging.INFO)
        self._infologfile.setFormatter(self._log_formatter)
        self._logger.addHandler(self._infologfile)

        if self._save_debuglog:
            self._debuglogpath = logfolder / (
                "debug_log" + self._get_full_time() + ".log"
            )
            self._debuglogfile = logging.FileHandler(self._debuglogpath)
            self._debuglogfile.setLevel(logging.DEBUG)
            self._debuglogfile.setFormatter(self._log_formatter)
            self._logger.addHandler(self._debuglogfile)

        self._logger.debug("Logger Initalised")


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="4TCT tool")
    argparser.add_argument(
        "-d", action="store_true", help="Configure for running in docker"
    )
    argparser.add_argument(
        "-b",
        "--boards",
        metavar="boards:",
        nargs="*",
        action="store",
        type=str,
        default=None,
        help="List boards to include after this flag, use the short form board name from 4chan, e.g. '-b a c g sci' would collect data from the boards /a/, /c/, /g/ and /sci/",
    )
    argparser.add_argument(
        "-e",
        "--exclude",
        action="store_true",
        help="Boolean flag - whether to exclude the flags after -b, e.g. '-b a c g sci -e' would exclude the boards /a/ /c/ /g/ and /sci/ from collection",
    )
    args = argparser.parse_args()
    requester_instance = requester(
        True, args.d, boards=args.boards, exclude_boards=args.exclude
    )
