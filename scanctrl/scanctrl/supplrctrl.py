import os

from scanctrl.sshctrl import SSHCtrl
from scanctrl.logger import logger # Import the global logger

class SUPPLRCtrl(SSHCtrl):
    """
    Controller for the SiPM bias voltage (SUPPLR) used in the scanning setup.
    Inherits from SSHCtrl to manage remote command execution.
    """
    def __init__(self, username: str = None, hostname: str = None, password_env_var: str = None, supplr_config: dict = None):
        
        self.config = supplr_config
        
        if username is None:
            username = self.config.get("username")
        if hostname is None:
            hostname = self.config.get("host")
        if password_env_var is None:
            password_env_var = self.config.get("password_env_var")

        super().__init__(
            username=username,
            hostname=hostname,
            password_env_var=password_env_var
        )
        self._check_server_status()
        

    def _check_server_status(self):
        """
        Checks if the SUPPLR server is reachable by running a simple command.
        """
        try:
            response = self.run_command("supplr server-status")
            if "Server available!" in response:
                logger.info("SUPPLR server is available and responding.")
            else:
                logger.error(f"SUPPLR server is not responding as expected: {response}")
                raise ConnectionError("SUPPLR server is not responding as expected.")
        except Exception as e:
            logger.error(f"Failed to connect to SUPPLR server: {e}")
            raise ConnectionError(f"Failed to connect to SUPPLR server")

    def set_bias_voltage(self, supplr_config_path : str  = None, board: int | list[int] = None, channels: list[int] = None, bias_voltage: int | float | list[float] | list[int] = None):
        """
        Sets the SiPM bias voltage on the remote server.

            The command supports multiple ways to configure the bias voltage:
        1. Use the SUPPLR configuration file at the provided path.
        2. If `bias_voltage` is not provided, look in the config passed during initialization FOR ALL PARAMETERS (can be either a supplr config file or single parameters).
        3. If `bias_voltage` is given as a list, a similar list of `channels` must be given, and each voltage will be applied to the corresponding channel.
        4. If `bias_voltage` is given as an int or float, the same bias voltage will be applied to the channels `channels`.
           Additionally if `channels` is not provided, the bias voltage will be applied to all the channels.

        Args:
            supplr_config_path (str): Path to the SUPPLR configuration file on the remote server.
            board (int | list[int]): The board number(s).
            channels (list[int]): The channel number(s).
            bias_voltage (int | float | list[float] | list[int]): The bias voltage.
        """
        self.board = int(self.config.get("board"))

        if supplr_config_path is not None:
            self.supplr_config_file = os.path.abspath(supplr_config_path)
            logger.debug(f"Using SUPPLR configuration file directly provided: {self.supplr_config_file}")

            # Check if the external file exists
            if os.path.exists(self.supplr_config_file):
                command = 'supplr set-channel-file --board {self.board} --file {self.supplr_config_file}' 
                self.run_command(command)
            else:
                logger.error(f"Specified SUPPLR config file not found: {self.supplr_config_file}.")
                raise FileNotFoundError(f"Specified SUPPLR config file not found.")

        elif bias_voltage is None:
            # Check the configuration file, is a supplr config file provided or the singles parameters
            if "config_file" in self.config:
                self.supplr_config_file = os.path.abspath(self.config["config_file"])
                logger.debug(f"Using SUPPLR configuration file from initialization: {self.supplr_config_file}")

                # Check if the external file exists
                if os.path.exists(self.supplr_config_file):
                    command = 'supplr set-channel-file --board {self.board} --file {self.supplr_config_file}' 
                    self.run_command(command)
                else:
                    logger.error(f"Specified SUPPLR config file not found: {self.supplr_config_file}.")
                    raise FileNotFoundError(f"Specified SUPPLR config file not found.")
            
            elif "bias_voltage" in self.config:
                self.bias_voltage = self.config["bias_voltage"]
                logger.debug(f"Using bias voltage from initialization config: {self.bias_voltage} V")
                if isinstance(self.bias_voltage, (int, float)):
                    if "channels" in self.config:
                        for chan in self.config["channels"]:
                            command = f"supplr set-channel --board {self.board} --channel {chan} --voltage {self.bias_voltage}"
                            self.run_command(command)
                    else:
                        command = f"supplr set-channels --board {self.board} --voltage {self.bias_voltage}"
                        logger.debug(f"Setting bias voltage for all channels to: {self.bias_voltage} V")
                        self.run_command(command)

                elif isinstance(self.bias_voltage, list) and "channels" in self.config:
                    for voltage, channel in zip(self.bias_voltage, self.config["channels"]):
                        command = f"supplr set-channel --board {self.board} --channel {channel} --voltage {voltage}"
                        self.run_command(command)

            else:
                logger.error("SUPPLR configuration must minimally include either 'config_file' or 'bias_voltage'.")
                raise ValueError("SUPPLR configuration must include either 'config_file' or 'bias_voltage' and 'channels'.")
            
        elif isinstance(bias_voltage, (int, float)):
            # TO ADD
            logger.debug(f"Not implemented yet")

        elif isinstance(bias_voltage, list) and channels is not None:
            # TO ADD
            logger.debug(f"Not implemented yet")

        else:
            logger.error("Invalid bias parameter congiguration. check --help for valid options.")
            raise ValueError("Invalid bias voltage configuration.")