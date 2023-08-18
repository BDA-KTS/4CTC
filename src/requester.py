import time
import logging
from pathlib import Path
import requests
from board import Board
from utils import LoggerManager, get_argparser

class Requester:
    """
    The main class for 4chan scraper, it handles creation of Board and Logger class, triggering each methods in Board class for entire scrapping process
    """
    def __init__(
        self,
<<<<<<< HEAD
        monitor: bool,
        run_in_docker: bool,
        boards: list = None,
        exclude_boards: bool = False,
        request_time_limit: float = 1,
        stream_log_level=logging.INFO,
        logfolderpath: str = "logs",
    ):
        if run_in_docker:
            self._base_save_path: Path = Path("/data")
        else:
            self._base_save_path: Path = Path().resolve() / "data" 
        self._save_debuglog = True
        self._stream_log_level = stream_log_level
        self._setup_logging(logfolderpath)

        self.monitor: bool = monitor
        self._include_boards: list = boards
        self._exclude_boards: bool = exclude_boards
        self._request_time_limit: float = request_time_limit
        self._check_new_boards: bool = True
        self._last_requested = {}
=======
        boards: list,
        exclude_boards: bool = False,
        request_time_limit: float = 1,
        log_folder_path: str = "logs",
        save_log: bool = True,
        clean_log: bool = True
    ):
        self._base_save_path: Path = Path().resolve() / "data" # .resolve() creates absolute path

        # Setup Logger
        self._log_manager = LoggerManager(self._base_save_path, log_folder_path, save_log)
        self._log_manager.setup_logging(stream_log_level=logging.INFO)
        self.logger = self._log_manager.get_logger()
        self._clean_log = clean_log
>>>>>>> develop

        # Setup request time interval variables
        self._last_request = None
        self._request_time_limit: float = request_time_limit

<<<<<<< HEAD
        if self.monitor is True:
            self.begin_monitoring()

    def begin_monitoring(self):
        self._logger.info("Beginning monitoring")
        self._logger.info(f"Storing data in path: {self._base_save_path}")
        
        self.monitoring_boards = []
        self.monitoring_threads = {}
        self._threads_last_checked = {}
        self._logger.debug("Initialising Monitoring Thread")
        self._monitor_thread = threading.Thread(target=self._begin_monitoring)
        self._logger.debug("Starting Thread")
        self._monitor_thread.start()
        self._logger.debug("Monitoring Started") 

    def end_monitoring(self):
        self._logger.info("Ending loop and closing monitoring thread")
        self.monitor = False
        self._monitor_thread.join()
        self._logger.info("Closed monitoring thread")

    def _load_old_monitors(self):
        self._update_monitoring_boards()
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

            good_boardpath_found = False
            for boardpath in boardfolderpath.iterdir():
                if boardpath.name.split("_")[0] == str(board): 

                    good_boardpath = boardpath 
                    good_boardpath_found = True

            if not good_boardpath_found:
                self._logger.info(
                    f"No previous thread information for /{board}/, no old threads to monitor"
                )
                continue
            old_monitor_dict[board] = {}

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
        self.monitoring_threads = old_monitor_dict
        self._logger.debug(
            f"{old_threads} past captures of old threads in previous instances discovered"
        )

    def set_include_exclude_boards(
        self, include_boards: list = None, exclude_boards: bool = False
    ):
        self._logger.info("Updating boards to monitor")
        self._include_boards = include_boards
        self._exclude_boards = exclude_boards
        if include_boards is None and not exclude_boards:
            self._check_new_boards = False
        else:
            self._check_new_boards = True

    def _update_monitoring_boards(self):
        self._logger.debug("Updating monitor board list (checking)")
        if self._include_boards is not None and not self._exclude_boards:
            self.monitoring_boards = self._include_boards
        elif self._include_boards is not None and self._exclude_boards:
            self.monitoring_boards = list( 
                set(self._set_board_list()).difference(self._include_boards)
            )
        else:
            self.monitoring_boards = self._set_board_list()
        self._check_new_boards = False

    def _begin_monitoring(self):
        self._logger.debug("_begin_monitoring entered")
        self._load_old_monitors()
        self._logger.debug("Old monitors retrieved")
        while self.monitor is True:
            self._logger.debug("Started loop")
            if self._check_new_boards:
                self._logger.debug("Started updating monitoring boards")
                self._update_monitoring_boards()
            self._update_monitoring_threads()
            self._logger.debug("updating posts on monitoring list")
            self._update_posts_on_monitoring_threadlist()
            self._logger.debug("Ended loop")

    
    def _delete_threads(self, board, threads):
        for thread in threads:
            del self.monitoring_threads[board][thread]
            if thread in self._last_requested[board]["threads"]:
                del self._last_requested[board]["threads"][thread]
                
    def _update_monitoring_threads(self):
        self._logger.info("Beginning search for threads to monitor")
        self._posts_to_update = []
        death_count = 0
        birth_count = 0
        update_count = 0 
        for board in self.monitoring_boards:
            self._logger.info(f"Searching for threads in {board}")
            threads_json = self.get_and_save_single_board_threadlist(
                board, with_return=True
            )
            if threads_json is None:
                continue
            threads_on_board = {}
            for page in threads_json:
                for thread in page["threads"]:
                    threads_on_board[str(thread["no"])] = [
                        int(thread["last_modified"]),
                        int(thread["replies"]),
                    ]
            if board in self.monitoring_threads:
                to_be_delete = []
                for thread in self.monitoring_threads[board]:
                    if thread in threads_on_board: 
                        pass
                    else:
                        self._logger.debug(f"Thread died: /{board}/{thread}")
                        death_count += 1
                        to_be_delete.append(thread)
                self._delete_threads(board, to_be_delete)
                for thread in threads_on_board:
                    if thread in self.monitoring_threads[board]:
                        if (
                            self.monitoring_threads[board][thread][0]
                            < threads_on_board[thread][0]
                        ):
                            self._logger.debug(f"Thread updated: /{board}/{thread}")
                            self.monitoring_threads[board][thread] = threads_on_board[
                                thread
                            ]
                            self._posts_to_update.append([board, thread])
                            update_count += 1
                        else:
                            self._logger.debug(
                                f"Do not need to update thread /{board}/{thread}"
                            )
                    else:
                        self._logger.debug(f"New thread: /{board}/{thread}")
                        self.monitoring_threads[board][thread] = threads_on_board[
                            thread
                        ]
                        self._posts_to_update.append([board, thread])
                        birth_count += 1
            else:
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
        number_posts_in_iteration = len(self._posts_to_update)
        i = 1
        prev_board = ""
        for board, post in self._posts_to_update:
            if prev_board != board:
                self._logger.info(f"Updating posts in {board}")
                prev_board = board
            start_time = time.time()
            self.get_and_save_thread(board, post) 

            current_time_diff = (time.time() - start_time) * (
                number_posts_in_iteration - i
            )
            self._logger.debug(
                f"{i}/{number_posts_in_iteration}: Capturing post {post} in /{board}/ approximate seconds remaining in iteration {current_time_diff:n}"
            )
            i += 1

    def _set_board_list(self):
        boards_info = self.get_chan_info_json()
=======
        # Setup monitoring boards
        self._include_boards: list = boards
        self._exclude_boards: bool = exclude_boards
        self._monitoring_boards = self._set_monitoring_boards()

        # Start scraping pipeline
        self._begin_monitoring()

    def _begin_monitoring(self):
        """
        Start the monitoring program.
        """
        self.logger.info("Beginning monitoring")
        self.logger.info(f"Storing data in path: {self._base_save_path}")
        self.logger.debug("Monitoring Started")
        self._run_scraping_pipeline()
    
    def _run_scraping_pipeline(self):
        self.logger.debug("scraping_pipeline_monitoring entered")

        # Data Collection Loop
        while True:
            self.logger.debug("Started loop")
            #TODO add check new board mechanism?
            for board in self._monitoring_boards:

                self._check_time_and_wait()
                online_thread_list = board.get_online_thread_list()
                
                if online_thread_list is not None: #TODO this is weird. where should the update checking logic be used?
                    board.save_thread_list(online_thread_list)
                    threads_to_update = board.get_threads_to_update(online_thread_list)
                    
                    self.logger.info(f"Updating posts in {board.board_code}")
                    n_threads_to_update = len(threads_to_update)
                    i = 1
                    for thread_id in threads_to_update: #TODO incorporate getting thread content"s" without looping here?
                        start_time = time.time()

                        self._check_time_and_wait()
                        thread_content = board.get_thread_content(thread_id)
                        board.save_thread_content(thread_id, thread_content)

                        current_time_diff = (time.time() - start_time) * (n_threads_to_update - i)
                        self.logger.debug(f"{i}/{n_threads_to_update}: Capturing post {thread_id} in /{board.board_code}/ approximate seconds remaining for this board {current_time_diff:n}")
                        i += 1
                self.logger.debug(f"Ended /{board.board_code}/ collection")
            self.logger.debug("Ended loop")

            if self._clean_log:
                self.logger.debug("Cleaning Log")
                self._log_manager.cleanup_old_logs(days_to_keep=3)

    def _set_monitoring_boards(self):
        """
        Preparing self.monitoring_boards which is essentially a list of board code that the program should monitor
        Process includes checking self._include_boards and self._exclude_boards
        if exclude_boards then self._include_boards become the ones not to monitor
        """
        available_boards = self._get_4chan_board_list()

        self.logger.debug("Updating monitor board list (checking)")
        if self._include_boards is not None and not self._exclude_boards:
            board_list = self._include_boards
        elif self._include_boards is not None and self._exclude_boards:
            board_list = list( 
                set(available_boards).difference(self._include_boards)
            )
        else: # if no boards provided then all boards are monitored
            board_list = available_boards
        # check if all the boards that will be monitored are valid
        for board in board_list:
            if board not in available_boards:
                self.logger.info(f"Board code '{board}' is not available in 4chan")
                raise KeyError(f"Board code '{board}' is not available in 4chan")

        # initialize Board class list
        monitoring_boards = []
        for board in board_list:
            monitoring_boards.append(Board(board, self.logger))
        self.logger.debug("Old monitors retrieved")
        #TODO Caculate overall pre_threads after all boards are initialized
        #self.logger.debug(f"{old_threads} past captures of old threads in previous instances discovered")

        return monitoring_boards
    
    def _get_4chan_board_list(self):
        self._check_time_and_wait()
        self.logger.debug("chan information requested")
        boards = requests.get("http://a.4cdn.org/boards.json")
        boards_info = boards.json()
>>>>>>> develop
        codes = [board["board"] for board in boards_info["boards"]]
        return codes

    def _check_time_and_wait(self):
        if self._last_request is None:
            self._last_request = time.time()
        else:
            cur_time = time.time()
            if cur_time - self._last_request >= self._request_time_limit:
                self._last_request = cur_time
            else:
                time.sleep(self._request_time_limit - (cur_time - self._last_request))
                self._last_request = time.time()

if __name__ == "__main__":
    argparser = get_argparser()
    args = argparser.parse_args()
    requester_instance = Requester(
        boards=args.boards,
        exclude_boards=args.exclude,
        request_time_limit=args.request_time_limit,
        log_folder_path=args.log_folder_path,
        save_log=args.save_log,
        clean_log=args.clean_log
    )

'''unused
    def set_include_exclude_boards(
        self, include_boards: list = None, exclude_boards: bool = False
    ):
        """
        Update the list of boards to include or exclude from monitoring.

<<<<<<< HEAD
    def get_single_board_threadlist(self, board_code:str):
        self._check_time_and_wait()
        self._logger.debug(f"Board /{board_code}/ thread information requested")
        if board_code not in self._last_requested:
            self._last_requested[board_code] = {}
            self._last_requested[board_code]["threads"] = {}
            r_thread_list = requests.get(
                "https://a.4cdn.org/" + board_code + "/threads.json"
            )
        else:
            board_request_time = datetime.now() - datetime.fromtimestamp(
                time.mktime(self._last_requested[board_code]["board"])
            ) 
            if board_request_time < timedelta(seconds=10):
                sleeping = 10 - board_request_time.total_seconds()
                self._logger.info(
                    f"Sleeping for {sleeping} seconds: time between requests for threads on board {board_code} too short"
                )
                time.sleep(sleeping)
            r_thread_list = requests.get(
                "https://a.4cdn.org/" + board_code + "/threads.json",
                headers=self._format_if_mod_since_header(
                    self._last_requested[board_code]["board"]
                ),
            )
=======
        This function allows updating the list of boards to include or exclude from the monitoring process.
        If no boards are included and `exclude_boards` is False, the checking for new boards is turned off.

        :param include_boards: A list of board codes to include in the monitoring process.
                              Defaults to None (no change in inclusion).
        :param exclude_boards: If True, exclude the specified boards from monitoring.
                              If False and no boards are included, new board checking is turned off.

        Note:
        - This function is currently not being used, but it seems to be designed for adding new boards to monitor
          without stopping the current program.
        - Use this function to modify the list of boards being monitored.
        """
        # the function is not used!! seems to be a function that can accept command to add new board for monitoring without stopping the current program
        self.logger.info("Updating boards to monitor")
        self._include_boards = include_boards
        self._exclude_boards = exclude_boards
        if include_boards is None and not exclude_boards:
            self._check_new_boards = False
        else:
            self._check_new_boards = True
>>>>>>> develop


<<<<<<< HEAD
    def get_thread(self, board_code:str, op_ID:int):
        self._check_time_and_wait()
        if board_code not in self._last_requested[board_code]["threads"]:
            r_thread = requests.get(
                "https://a.4cdn.org/" + board_code + "/thread/" + str(op_ID) + ".json"
            )
        else:
            r_thread = requests.get(
                "https://a.4cdn.org/" + board_code + "/thread/" + str(op_ID) + ".json",
                headers=self._format_if_mod_since_header(
                    self._last_requested[board_code]["threads"][op_ID]
                ),
            )
        self._last_requested[board_code]["threads"][op_ID] = datetime.now().timetuple()

        countdown = 1
        while r_thread.status_code not in [200, 304]:
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
                ),
            )
            self._last_requested[board_code]["threads"][
                op_ID
            ] = datetime.now().timetuple()
            countdown += 1
        if r_thread.status_code == 304: 
            self._logger.debug(f"Thread {op_ID} not updated since last request") 
            return None
        elif r_thread.status_code == 200:
            self._logger.debug("Recieved answer")
        time.sleep(self._request_time_limit)
        return r_thread.json()
=======
    def end_monitoring(self):
        """
        Terminate the monitoring process and close the monitoring thread.

        This function allows for terminating the monitoring process by setting the `monitor` attribute to False.
        It also waits for the `_monitor_thread` to complete using the `join` method, ensuring that the thread is closed.

        Note:
        - The `monitor` attribute controls the monitoring loop.
        - The `_monitor_thread` is joined to ensure its completion.
        - This function is currently not being used and can be utilized to terminate monitoring externally.
        """
        self.logger.info("Ending loop and closing monitoring thread")
        self.monitor = False
        self._monitor_thread.join()
        self.logger.info("Closed monitoring thread")
>>>>>>> develop

    def get_and_save_chan_info(self, outpath:Path=None, filename:str=None):
        """
        Fetches 4chan board information and saves it to a JSON file.

        This function sends a request to the 4chan API to retrieve information about all boards.
        The board information is then saved to a JSON file in the specified output path with the provided filename.

        :param outpath: The directory path where the JSON file will be saved.
                        Defaults to the base save path with appropriate subdirectories.
        :param filename: The name of the JSON file to be saved. Defaults to "boards.json".
        
        Note:
        - This function is currently not being used but can be utilized to fetch and save board information.
        """
        timestamp = self._get_day()
        if outpath is None:
            outpath = self._base_save_path / "saves" / timestamp
        if filename is None:
            filename = "boards.json"
        outpath.mkdir(parents=True, exist_ok=True)
        with open(outpath / filename, "w") as outfile:
            json.dump(self.get_chan_info_json(), outfile, indent=2)
<<<<<<< HEAD

    def get_and_save_single_board_threadlist(
        self, board_code:str, outpath:Path=None, filename:str=None, with_return:bool=False
    ):
        timestamp = self._get_day()
        if outpath is None:
            outpath = self._base_save_path / "saves" / timestamp / "threads_on_boards"
        if filename is None:
            filename = board_code + self._get_time() + ".json"
        outpath.mkdir(parents=True, exist_ok=True)
        threadlist = self.get_single_board_threadlist(board_code)
        if threadlist is None:
            return None
        for threads in outpath.iterdir():
            if threads.name.split("_")[0] == str(board_code):
                threads.unlink()
        with open(outpath / filename, "w") as outfile:
            json.dump(threadlist, outfile, indent=2)
        if with_return:
            return threadlist

    def get_and_save_thread(self, board_code:str, op_ID:int, outpath:Path=None, filename:str=None):
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
            if int(threads.name.split("_")[0]) == int(op_ID):
                with open(threads, "r+") as outfile:
                    try:
                        data = json.load(outfile)
                    except json.decoder.JSONDecodeError as jerror:
                        self._logger.warning(
                            f"Loading JSON file {threads} caused error {jerror}, continuing to writing new file rather than append. Board {board_code}, post {op_ID}"
                        )
                        continue
                    else:
                        to_update = self.get_thread(board_code, op_ID)
                        if to_update is None:
                            self._logger.warning(
                                f"Likely 404 caused no return for, skipping | board {board_code}, post {op_ID}"
                            )
                            new_thread = False
                            continue
                        data.update(to_update) 

                        outfile.seek(0)
                        json.dump(data, outfile, indent=2)
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
=======
'''
>>>>>>> develop
