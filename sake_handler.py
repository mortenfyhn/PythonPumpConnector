from log_manager import LogManager

class SakeHandler():
    
    pump_enabled:bool = False

    def __init__(self):
        self.logger = LogManager.get_logger(self.__class__.__name__)
        return

    def notify_callback(self, is_notifying:bool, char):
        if is_notifying and not self.pump_enabled:
            self.logger.warning("pump wants to be friends with us!")
            self.pump_enabled = True

        if is_notifying == False:
            self.pump_enabled = is_notifying
            self.logger.error(f"pump disabled notifications!")
        
        return


    def write_callback(self, value:bytearray, options:dict):
        """
        options has fields: device, link, mtu
        """
        self.logger.info(f"write cb: {value} {options}")
        return