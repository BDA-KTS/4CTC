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

        # Setup request time interval variables
        self._last_request = None
        self._request_time_limit: float = request_time_limit

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
'''