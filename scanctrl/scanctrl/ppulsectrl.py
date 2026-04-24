
import os

import scanctrl.sshctrl as sshctrl
from scanctrl.logger import logger # Import the global logger

class PPULSECtrl(sshctrl.SSHCtrl):
    """
    Controller for the pulse generator used in the scanning setup.
    Inherits from SSHCtrl to manage remote command execution.
    """
    def __init__(self, pulser_config: dict, username: str = None, hostname: str = None, password_env_var: str = None):
        
        self.config = pulser_config
        
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

        try:
            self._set_config()
        except Exception as e:
            logger.error(f"Failed to set pulser configuration: {e}")

    def _check_server_status(self):
        """
        Checks if the pulser server is reachable by running a simple command.
        """
        try:
            response = self.run_command("ppulse server-status")
            if "Server available!" in response:
                logger.info("Pulser server is available and responding.")
            else:
                logger.error(f"Pulser server is not responding as expected: {response}")
                raise ConnectionError("Pulser server is not responding as expected.")
        except Exception as e:
            logger.error(f"Failed to connect to pulser server: {e}")
            raise ConnectionError(f"Failed to connect to pulser server")

    def _set_config(self):
        """
        Sets the pulser configuration on the remote server.
        
        If 'config_file' key exists: Check if the path exists, if yes, load that file else load 's_params', 'p_params' and 'channels'.
        
        e.g {
                "host" : "130.92.128.165",
                "username" : "pi",
                "config_file": "pulser_config.json", or "s_params": [s1, s2,...], "p_params": [p1, p2, ...], "channels": [ch`1, ch2,...]],
                "period": 10, # [ms]
                "duration": 30 # [s]
            }
        
            Note: Channel numbers are 1 to 16, s is from 0 to 255 and p is from 0 to 255.

        Args:
            config_path (str): Path to the main config.json file.
        """

        # Check if a config file was given or the singles parmaeters
        if "config_file" in self.config:
            pulser_config_file = os.path.abspath(self.config["config_file"])
            logger.debug(f"Using pulser configuration file: {pulser_config_file}.")

            # Check if the external file exists
            if os.path.exists(pulser_config_file):
                command = 'ppulse set-channels-file -f {pulser_config_file}' 
                self.run_command(command)
            else:
                logger.error(f"Specified pulser config file not found: {pulser_config_file}.")
                raise FileNotFoundError(f"Specified pulser config file not found.")
        
        elif "s_params" in self.config and "p_params" in self.config and "channels" in self.config:
            logger.debug("Using pulser configuration parameters from config file")
            for i, channel in enumerate(self.config["channels"]):
                s_param = int(self.config["s_params"][i])
                p_param = int(self.config["p_params"][i])

                if s_param is None or p_param is None:
                    logger.error(f"Missing s_param or p_param for channel {channel} in config.")
                    raise ValueError(f"Missing s_param or p_param for channel {channel} in config.")
                
                command = f"ppulse ... --channel {channel} --s_param {s_param} --p_param {p_param}"
                logger.debug(f"Setting pulser configuration for channel {channel}: s_param={s_param}, p_param={p_param}")
                self.run_command(command)

        else:
            logger.error("Pulser configuration must include either 'config_file' or 's_params', 'p_params', and 'channels'.")
            raise ValueError("Pulser configuration must include either 'config_file' or 's_params', 'p_params', and 'channels'.")

        # Set period parameter
        self.period = int(self.config.get("period"))
        command = f"ppulse set-trigger -p {self.period}"
        self.run_command(command)

        # Get duration parameter
        self.duration = int(self.config.get("duration"))

    def run_pulser(self):
        """
            Runs the pulser with the specified configuration.
        """
        command = f"ppulse run-trigger -d {self.duration}"
        logger.debug(f"Running pulser for duration: {self.duration} seconds with period: {self.period} ms")
        self.run_command(command)
