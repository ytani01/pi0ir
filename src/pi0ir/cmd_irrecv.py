#
# (c) 2025 Yoichi Tanibayashi
#
import time

from .irrecv import IrRecv
from .utils.mylogger import get_logger


class CmdIrRecv:
    def __init__(self, pi, pin, verbose=False, debug=False):
        self.__debug = debug
        self.__log = get_logger(__class__.__name__, self.__debug)
        self.__log.debug("pin=%d, verbose=%s", pin, verbose)

        self.receiver = IrRecv(pi, pin, verbose=verbose, debug=self.__debug)

    def main(self):
        self.__log.debug("")

        while True:
            print("# -")
            raw_data = self.receiver.recv()
            self.receiver.print_pulse_space(raw_data)
            print("# /")
            time.sleep(0.5)

    def end(self):
        self.__log.debug("")
        self.receiver.end()
