
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

    #-----------------------
    # Helper functions
    #-----------------------

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

    def _set_period(self):
        """
        Sets the pulser period on the remote server.
        """
        command = f'ppulse set-trigger -p {int(self.config.get("period"))}'
        self.run_command(command)


    def _set_config_file(self):
        """
        Sets the pulser configuration on the remote server using a config file.
        """
        config_file = os.path.abspath(self.config.get("config_file"))
        
        # Check if the external file exists
        if os.path.exists(config_file):
            logger.debug(f"Setting pulser configuration file: {config_file}.")
            self.transfer_file(config_file, remote_dir=self.config.get("config_folder_remote"), remote_filename=os.path.basename(config_file))
            config_file_remote = os.path.join(self.config.get("config_folder_remote"), os.path.basename(config_file))

            command = f'ppulse set-channels-file -f {config_file_remote}' 
            self.run_command(command)

        else:
            logger.error(f"Specified pulser config file not found: {config_file}.")
            raise FileNotFoundError(f"Specified pulser config file not found.")

    def _set_config(self, pulser_config: dict = None):
        """
        Sets the pulser configuration on the remote server.
        
        If 'config_file' key exists: Check if the path exists, if yes, load that file else load 's_params', 'p_params' and 'channels'.
        
        e.g {
                "host" : "130.92.128.165",
                "username" : "pi",
                "config_file": "pulser_config.json", or "s_params": [s1, s2,...], "p_params": [p1, p2, ...], "channels": [ch1, ch2,...]],
                "period": 10, 
                "duration": 30
            }
        
            Note: The parameters `s` and `p` are from 0 to 255, `channels` are from 1 to 16, 
            `period` is given in milliseconds (min. 3ms) and `duration` is given in seconds.

        Args:
            config_path (str): Path to the main config.json file.
        """
        if pulser_config is not None:
            self.config = pulser_config

        required_single_parameters = ["s_params", "p_params", "channels"]

        if "config_file" in self.config:
            self._set_config_file()
            
            
        elif all(parameter in self.config for parameter in required_single_parameters): 
                
            # Check that they have the same length
            if len(set(len(self.config[k]) for k in required_single_parameters)) > 1:
                raise ValueError("Config lists must have equal length")

            logger.debug("Using pulser configuration parameters")

            for channel, s_param, p_param in zip(self.config["channels"], self.config["s_params"], self.config["p_params"]):
                
                command = f"ppulse set-channel -ch {channel} -s {s_param} -p {p_param}"
                self.run_command(command)

                logger.debug(f"Set pulser configuration for channel {channel}: s_param={s_param}, p_param={p_param}")

        else:
            logger.error("Pulser configuration must include either 'config_file' or 's_params', 'p_params', and 'channels'.")
            raise ValueError("Pulser configuration must include either 'config_file' or 's_params', 'p_params', and 'channels'.")

        # Set period parameter
        self._set_period()

    #-----------------------
    # Main function
    #-----------------------

    def run_pulser(self, config_file: str = None, period: int = None, duration: int = None):
        """
            Runs the pulser with the specified configuration. If the arguments are provided, use them, else
            it use the ones from the initialization config.
        """ 
        if config_file is not None:
            self.config["config_file"] = config_file
            self._set_config_file()

        if period is not None:
            self.config["period"] = period
            self._set_period()

        if duration is not None:
            self.config["duration"] = duration

        command = f"ppulse run-trigger -d {int(self.config.get('duration'))}"
        logger.debug(f"Running pulser for duration: {int(self.config.get('duration'))} seconds with period: {int(self.config.get('period'))} ms")
        self.run_command(command)


