from abc import ABC, abstractmethod

class Collector(ABC):
    @abstractmethod
    def request(self, target):
        pass
    
    @abstractmethod
    def save(self, path):
        pass

class ThreadlistCollector:
    def request(self, target):
        board_code = target
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
