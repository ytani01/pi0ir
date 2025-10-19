#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
"""IrRecv.py"""

import queue
import threading

import pigpio

from .utils.mylogger import get_logger


class IrRecv:
    """
    赤外線信号の受信
    """

    DEF_GLITCH_USEC = 250  # usec
    LEADER_MIN_USEC = 300  # usec

    # INTERVAL_USEC_MAX = 999999  # tick == usec
    INTERVAL_USEC_MAX = 500 * 1000  # tick == usec
    INTERVAL_MSEC_MAX = int(INTERVAL_USEC_MAX / 1000)

    WATCHDOG_MSEC = INTERVAL_MSEC_MAX / 2  # msec
    WATCHDOG_CANCEL = 0

    VAL_ON = 0
    VAL_OFF = 1 - VAL_ON

    KEY_PULSE = "pulse"
    KEY_SPACE = "space"

    MSG_END = ""

    def __init__(
        self, pi, pin, glitch_usec=DEF_GLITCH_USEC, verbose=False, debug=False
    ):
        """
        Parameters
        ----------
        pi: pigpio.pi()
        pin: int
        glitch_usec: int
        verbose: bool
        debug: bool
        """
        self.__debug = debug
        self.__log = get_logger(__class__.__name__, self.__debug)
        self.__log.debug(
            "pin=%d, glitch_usec=%d, verbose=%s", pin, glitch_usec, verbose
        )

        self.pi = pi
        self.pin = pin
        self.glitch_usec = glitch_usec
        self.verbose = verbose

        self.last_tick = 0

        self.pi.set_mode(self.pin, pigpio.INPUT)
        self.pi.set_glitch_filter(self.pin, self.glitch_usec)

        self.receiving = False
        self.raw_data = []

        self.msgq = queue.Queue()

    def set_watchdog(self, ms):
        """
        受信タイムアウトの設定

        Parameters
        ----------
        ms: int
          msec
        """
        self.__log.debug("ms=%d", ms)
        self.pi.set_watchdog(self.pin, ms)

    def cb_func_recv(self, pin, val, tick):
        """
        信号受信用コールバック関数

        受信用GPIOピン``pin``が変化するか、タイムアウトすると呼び出される。

        変化を検知すると、メッセージキューに格納し、
        最小限の処理にとどめて、ほとんどの処理はサブスレッドに任せる。
        """
        self.__log.debug("pin=%d, val=%d, tick=%d", pin, val, tick)

        if not self.receiving:
            self.__log.debug("reciving=%s .. ignore", self.receiving)
            return

        self.msgq.put([pin, val, tick])

        if val == pigpio.TIMEOUT:
            # 受信終了処理
            self.set_watchdog(self.WATCHDOG_CANCEL)
            self.cb_recv.cancel()
            self.receiving = False

            self.msgq.put(self.MSG_END)

            self.__log.debug("timeout!")
            return

        self.set_watchdog(self.WATCHDOG_MSEC)

    def worker(self):
        """
        サブスレッド

        メッセージキューから``msg``(GPIOピンの変化情報)を取出し、処理する。
        実際の処理は``proc_msg()``で行う。

        """
        self.__log.debug("")

        while True:
            msg = self.msgq.get()
            self.__log.debug("msg=%s", msg)
            if msg == self.MSG_END:
                break

            self.proc_msg(msg)

        self.__log.debug("done")

    def proc_msg(self, msg):
        """
        GPIOの値の変化に応じて、
        赤外線信号のON/OFF時間を``self.raw_data``に記録する。

        self.raw_data: [[pulse1, space1], [pulse2, space2], ..]

        Parameters
        ----------
        msg: [pin, val, tick]
          GPIOピンの状態変化

        """
        self.__log.debug("msg=%s", msg)

        if not isinstance(msg, list):
            self.__log.warning("invalid msg:%s .. ignored", msg)
            return
        if len(msg) != 3:
            self.__log.warning("invalid msg:%s .. ignored", msg)
            return

        [_, val, tick] = msg

        # interval_usecを求める
        interval_usec = pigpio.tickDiff(self.last_tick, tick)
        self.__log.debug("interval_usec=%d", interval_usec)
        self.last_tick = tick

        if val == pigpio.TIMEOUT:
            self.__log.debug("timeout!")
            if len(self.raw_data) > 0:
                if len(self.raw_data[-1]) == 1:
                    self.raw_data[-1].append(interval_usec)
            self.__log.debug("end")
            return

        if interval_usec > self.INTERVAL_USEC_MAX:
            interval_usec = self.INTERVAL_USEC_MAX
            self.__log.debug("interval_usec=%d", interval_usec)

        if val == self.VAL_ON:
            # end of space
            if self.raw_data == []:
                self.__log.debug("start raw_data")
                return
            else:
                #    [ [111, 222], [333] ]
                # -> [ [111, 222], [333, interval_usec] ]
                self.raw_data[-1].append(interval_usec)

        else:  # val == self.VAL_OFF
            # end of pulse
            if self.raw_data == [] and interval_usec < self.LEADER_MIN_USEC:
                self.set_watchdog(self.WATCHDOG_CANCEL)
                self.__log.debug(
                    "%d < %d: leader is too short .. ignored",
                    interval_usec,
                    self.LEADER_MIN_USEC,
                )
                return
            else:
                #    [ [111, 222] ]
                # -> [ [111, 222], [interval_ussec] ]
                self.raw_data.append([interval_usec])

        self.__log.debug("raw_data=%s", self.raw_data)

    def recv(self):
        """
        赤外線信号の受信

        受信処理に必要なコールバックとサブスレッド``thr_worker``を生成し、
        サブスレッドが終了するまで待つ。

        """
        self.__log.debug("")

        self.raw_data = []
        self.receiving = True

        self.thr_worker = threading.Thread(target=self.worker, daemon=True)
        self.thr_worker.start()

        # self.set_watchdog(self.WATCHDOG_MSEC)
        self.cb_recv = self.pi.callback(
            self.pin, pigpio.EITHER_EDGE, self.cb_func_recv
        )

        if self.verbose:
            print("Ready")

        # スレッドが終了するまで待つ
        self.thr_worker.join()
        self.cb_recv.cancel()

        if self.verbose:
            print("Done")

        return self.raw_data

    def end(self):
        """
        終了処理

        コールバックをキャンセルし、
        ``worker``スレッドがaliveの場合は、終了メッセージを送り、終了を待つ。
        """
        self.__log.debug("")
        self.cb_recv.cancel()

        if self.thr_worker.is_alive():
            self.msgq.put(self.MSG_END)
            self.__log.debug("join()")
            self.thr_worker.join()

        self.__log.debug("done")

    def raw2pulse_space(self, raw_data=None):
        """
        リスト形式のデータをテキストに変換。

        Parameters
        ----------
        raw_data: [[p1, s1], [p2, s2], ..]
          引数で与えられなかった場合は、最後に受信したデータを使用する。

        Returns
        -------
        pulse_space: str
          pulse p1
          space s1
          pulse p2
          space s2
          :
        """
        self.__log.debug("row_data=%s", raw_data)

        if raw_data is None:
            raw_data = self.raw_data
            self.__log.debug("raw_data=%s", raw_data)

        pulse_space = ""
        for p, s in raw_data:
            pulse_space += f"{self.KEY_PULSE} {p}\n"
            pulse_space += f"{self.KEY_SPACE} {s}\n"

        return pulse_space

    def print_pulse_space(self, raw_data=None):
        """
        ``raw_data``の内容を下記の書式でテキスト出力する。

        pulse p1
        space s1
        pulse p2
        space s2
        :

        Parameters
        ----------
        raw_data: list
          [[p1, s1], [p2, s2], .. ]

        """
        self.__log.debug("raw_data=%s", raw_data)

        if raw_data is None:
            raw_data = self.raw_data
            self.__log.debug("raw_data=%s", raw_data)

        print(self.raw2pulse_space(raw_data), end="")
