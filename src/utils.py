from datetime import datetime, timedelta
import logging
from pathlib import Path
import argparse
import os

def get_argparser():
    """
    Get argument parser for scraper tool

    :return: argument parser
    """
    argparser = argparse.ArgumentParser(description="4TCT tool")
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
    argparser.add_argument(
        "--request-time-limit",
        type=check_positive_float,
        default=1,
        help="Wait time between each request (must be greater than 1)",
    )
    argparser.add_argument(
        "--log-folder-path",
        type=str,
        default="logs",
        help="Path for log folder (default: 'logs')",
    )
    argparser.add_argument(
        "--no-save-log",
        action="store_false",
        dest="save_log", 
        help="If provided, logs will not be saved",
    )
    argparser.add_argument(
        "--no-clean-log",
        action="store_false",
        dest="clean_log", 
        help="If provided, logs older than 3 days will not be removed",
    )
    return argparser


def check_positive_float(value):
    """
    A helper function for argparser for minimum request interval, it checks if the value is bigger than 1
    :return: request interval
    """
    fvalue = float(value)
    if fvalue < 1:
        raise argparse.ArgumentTypeError(f"--request-time-limit value should be at least 1, now is {value}")
    return fvalue

class LoggerManager:
    """
    Logger class for scraper tool
    """
    def __init__(self, base_save_path: Path, logfolderpath: Path, save_log: bool):
        if save_log:
            self.logfolder = base_save_path / logfolderpath
            self.logfolder.mkdir(parents=True, exist_ok=True)
            self.save_log = save_log
        self.logfolder = base_save_path / logfolderpath
        self.logger = None

    def setup_logging(self, stream_log_level=logging.INFO):
        """
        Setup logger
        """
        self.logger = logging.getLogger("4chan_requester")
        self.logger.setLevel(logging.DEBUG)
        log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(threadName)s - %(message)s")

        streamlogs = logging.StreamHandler()
        streamlogs.setLevel(stream_log_level)
        streamlogs.setFormatter(log_formatter)
        self.logger.addHandler(streamlogs)

        if self.save_log:
            self._setup_save_logging(log_formatter)

        self.logger.debug("Logger Initialized")

    def _setup_save_logging(self, log_formatter):
        infologpath = self.logfolder / ("info_log" + self._get_full_time() + ".log")
        infologfile = logging.FileHandler(infologpath)
        infologfile.setLevel(logging.INFO)
        infologfile.setFormatter(log_formatter)
        self.logger.addHandler(infologfile)

        debuglogpath = self.logfolder / ("debug_log" + self._get_full_time() + ".log")
        debuglogfile = logging.FileHandler(debuglogpath)
        debuglogfile.setLevel(logging.DEBUG)
        debuglogfile.setFormatter(log_formatter)
        self.logger.addHandler(debuglogfile)

    def _get_full_time(self):
        now = datetime.utcnow()
        return now.strftime("%Y_%m_%d_%H_%M_%S")

    def cleanup_old_logs(self, days_to_keep: int = 3):
        """
        Clean up/Delete old logs
        """
        now = datetime.utcnow()
        threshold_date = now - timedelta(days=days_to_keep)

        for log_file in self.logfolder.glob("*.log"):
            file_date_str = log_file.name[-len("yyyy_mm_dd_hh_mm_ss.log"):-len(".log")]
            file_date = datetime.strptime(file_date_str, "%Y_%m_%d_%H_%M_%S")
            
            if file_date < threshold_date:
                os.remove(log_file)

    def get_logger(self):
        """
        :return: the logger object
        """
        if self.logger is None:
            raise RuntimeError("Logger not set up yet. Call setup_logging() first.")
        return self.logger


def get_time():
    """
    :return: time information
    """
    now = datetime.utcnow()
    return now.strftime("_%H_%M_%S")

def get_day():
    """
    :return: day time information
    """
    now = datetime.utcnow()
    return now.strftime("%Y_%m_%d")
