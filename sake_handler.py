import threading
import queue

from log_manager import LogManager

from pysake.server import SakeServer
from pysake.constants import KEYDB_PUMP_EXTRACTED

class SakeHandler:

    pump_enabled: bool = False
    char = None

    def __init__(self):
        self.logger = LogManager.get_logger(self.__class__.__name__)

        self._tx_queue = queue.Queue()
        self._stop_evt = threading.Event()

        self._tx_thread = threading.Thread(
            target=self._tx_worker,
            name="sake-tx",
            daemon=True
        )
        self._tx_thread.start()
        self.server = SakeServer(KEYDB_PUMP_EXTRACTED)
        return

    def notify_callback(self, is_notifying: bool, char):
        if self.char is None:
            self.logger.info(f"sake char is first seen as {char}")
            self.char = char

        if is_notifying and not self.pump_enabled:
            self.logger.warning("pump wants to be friends with us!")
            self.pump_enabled = True
            zeroes = bytes(20)
            self.__send(zeroes)
            self.server.handshake(zeroes)

        if not is_notifying:
            self.pump_enabled = False
            self.logger.error("pump disabled notifications!")

        self.logger.info("sake notification received")
        return

    def write_callback(self, value: bytearray, options: dict):
        value = bytes(value)
        self.logger.info(
            f"sake write callback received: {value.hex()}, {options}"
        )
        output = self.server.handshake(bytes(value))
        self.__send(output)
        return

    def __send(self, data: bytes):
        # make this thread safe because we might be running in a callback context
        if self.char is None:
            raise RuntimeError("Sake char is none! You forgot to call set_char()!")
        self._tx_queue.put(data)
        return

    def _tx_worker(self):
        """
        The ONLY place where real char.set_value() is allowed.
        """
        while not self._stop_evt.is_set():
            try:
                data = self._tx_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                self.char.set_value(list(data))
                self.logger.info(f"sent data on sake port: {data.hex()}")
            except Exception as e:
                self.logger.exception(f"TX failed: {e}")

    # def close(self):
    #     self._stop_evt.set()
    #     self._tx_queue.put(b"")  # unblock