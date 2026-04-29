import os
import shutil
import json
import csv

import scanctrl.sshctrl as sshctrl  
from scanctrl.logger import logger # Import the global logger


class SUPPLRCtrl(sshctrl.SSHCtrl):
    """
    Controller for the SiPM bias voltage (SUPPLR) used in the scanning setup.
    Inherits from SSHCtrl to manage remote command execution.
    """
    def __init__(self, supplr_config: dict, username: str = None, hostname: str = None, password_env_var: str = None):
        
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
        
        self.biased_channels = {}
        self.board = self.config.get("board", None)
        self.set_default_bias(self.board)


    def __close__(self):
        """
        Ensure the SSH connection is closed when the object is destroyed.
        """
        self.set_default_bias()
        self.close()

    #-----------------------
    # Helper functions
    # -----------------------  

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
        
        
    def _reset_folder(self, path : str):
        """
        Resets a folder by deleting all its contents and recreating it. If the folder does not exist,
        it will be created.

        Args:
            path (str): The path to the folder to reset.
        """
        if os.path.exists(path):
            # Recursively delete everything inside and the folder itself
            shutil.rmtree(path)
    
        # Recreate the folder with default permissions
        os.makedirs(path, exist_ok=True)


    def _load_bias_config(self, csv_path : str) -> dict:
        """
        Reads a CSV file (chan, voltage) and returns a dict: {channel: voltage}.

        Args:
            csv_path (str): The path to the CSV configuration file.
        """
        config = {}
        try:
            with open(csv_path, mode='r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row_num, row in enumerate(reader, start=1):
                    # Skip empty lines
                    if not row or all(cell.strip() == '' for cell in row):
                        continue
                    
                    if len(row) < 2:
                        logger.warning(f"Skipping row {row_num}: Not enough columns.")
                        continue

                    try:
                        channel = int(row[0].strip())
                        voltage = float(row[1].strip())
                        config[channel] = voltage
                    except ValueError:
                        logger.warning(f"Skipping row {row_num}: Invalid number format.")
                        continue
                        
            if not config:
                logger.warning(f"No valid data found in {csv_path}")
                
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {csv_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading {csv_path}: {e}")
            raise

        return config


    def _save_biased_channels(self):
        """
        Saves the current biased channels information to a JSON file in the temporary folder.
        """
        # reset folder
        print(f'\n{self.config.get("tmp_config_folder")} type: {type(self.config.get("tmp_config_folder"))}')
        self._reset_folder(path = self.config.get("tmp_config_folder"))
        # write the updated file
        with open(os.path.join(self.config.get("tmp_config_folder"), "biased_channels.json"), 'w') as f:
            json.dump(self.biased_channels, f)


    def _set_bias_file(self, board: int, config_file: str = None, default_voltage: bool = False):
        """
        Helper function to set the bias voltage using a configuration file for a specific board.

        Args:
            board (int): The board number.
            config_file (str, optional): The path to the CSV supplr configuration file.
            default_voltage (bool, optional): If True, sets all channels to the default voltage instead of using a config file.
        """

        if default_voltage:
            desired_bias = {chan: self.config.get("default_voltage") for chan in range(1, 129)}
        else:
            desired_bias = self._load_bias_config(config_file)
        
        if self.biased_channels.get(board, {}) == desired_bias:
            logger.debug(f"The board {board} is already set to the desired bias configuration. Skipping command.")
            return
         
        if default_voltage:
            config_file_remote = self.config.get("default_config_file_remote")
            
        else:
            # Pass the config file to the raspi
            config_folder_remote = self.config.get("tmp_config_folder_remote")
            self.transfer_file(config_file, config_folder_remote, os.path.basename(config_file))
            config_file_remote = os.path.join(config_folder_remote, os.path.basename(config_file))

        command = f"supplr set-channel-file --board {board} --file {config_file_remote}"
        self.run_command(command)
        self.biased_channels[board] = desired_bias
        logger.debug(f"Set bias voltage for board {board} using config file: {config_file}")

        self._save_biased_channels()


    def _set_bias_channel(self, board: int, channel: int, voltage: float):
        """
        Helper function to set the bias voltage for a specific channel on a specific board.

        Args:            
            board (int): The board number.
            channel (int): The channel number.
            voltage (float): The desired bias voltage.
        """
        if self.biased_channels.get(board, {}).get(channel, None) == voltage:
            logger.debug(f"Channel {channel} on board {board} is already set to {voltage} V. Skipping command.")
            return
        
        command = f"supplr set-channel --board {board} --channel {channel} --voltage {voltage}"
        self.run_command(command)

        self.biased_channels[board][channel] = voltage
        logger.debug(f"Set bias voltage for board {board} channel {channel} to {voltage} V")

        self._save_biased_channels()


    def _set_bias_channels(self, board: int, voltage: float):
        """
        Helper function to set the same bias voltage for all channels on a specific board.

        Args:
            board (int): The board number.
            voltage (float): The desired bias voltage.
        """
        desired_bias = {chan: voltage for chan in range(1, 129)}

        if self.biased_channels.get(board, {}) == desired_bias:
            logger.debug(f"All channels on board {board} are already set to {voltage} V. Skipping command.")
            return

        command = f"supplr set-channels --board {board} --voltage {voltage}"
        self.run_command(command)
        self.biased_channels[board] = desired_bias
        logger.debug(f"Set bias voltage for all channels on board {board} to {voltage} V")

        self._save_biased_channels()
    
    #-----------------------
    # Main functions
    #-----------------------
       
    def set_default_bias(self, board: int = None, channels: list[int] = None):
        """
        Sets the bias voltage to a default value (e.g., 1V).

        1. If no arguments are provided, the default bias will be applied to all channels
            on the board where at least one channel is biased.
        2. If only `board` is provided, the default bias will be applied to all channels on the specified board.
        3. If both `board` and `channels` are provided, the default bias will be applied only to the specified
            channels on the specified board. e.g. board15 and [chan2, chan5] will result in chan2 of board 15 and chan5 of board 16 to be biased.

        Args:
            board (int, optional): The board number.
            channels (list[int], optional): The channel number(s).
        """
        if board is None:
            logger.debug("Setting default bias voltage for biased board.")
            for board in self.biased_channels.keys():
                self._set_bias_file(board, default_voltage = True)
        elif board is not None:
            if channels is None:
                logger.debug(f"Setting default bias voltage for all channels on board: {board}.")

                self._set_bias_file(board, default_voltage = True)
        
            elif board is not None and channels is not None:
                
                for channel in channels:
                    self._set_bias_channel(board, channel, self.config.get("default_voltage"))

        
    def set_bias_voltage_file(self, board: int = None, supplr_config_path :str = None):
        """
        Sets the SiPM bias voltage on the remote server using configuration files. 

        If the arguments are not provided, the method will use the ones from the initialization config.

        Args:
            board (int, optional): The board number.        
            supplr_config_path (str, optional): Path to the SUPPLR configuration file for the specified board.
        """

        if supplr_config_path is None:
            supplr_config_path = self.config.get('config_file')

        if board is None:
            board = self.config.get("board")

        for config_file in supplr_config_path:
            self._set_bias_file(board, config_file=config_file)

        
    def set_bias_voltage_channels(self, board: int = None, channels: list[int] = None, bias_voltages: float | list[float] = None):
        """
        Sets the SiPM bias voltage on the remote server for the specified channels, one channel at a time.
    
        If the arguments are not provided, the method will use the ones from the initialization config.

        Args:
            board (int, optional): The board number.
            channels (list[int], optional): The channel number(s).
            bias_voltages (float | list[float], optional): The bias voltage.
        """
        # Set the values
        if board is None:
            board = self.config.get("board")

        if channels is None:
            channels = self.config.get("channels")

        if bias_voltages is None:
            bias_voltages = self.config.get("bias_voltages")

        if isinstance(bias_voltages, float):
            bias_voltages = [bias_voltages] * len(channels)
       
        # Check that the lengths of the channel and bias_voltages lists match
        if len(bias_voltages) != len(channels):
            logger.error(f"Length of bias_voltages {{len(bias_voltages)}} must match length of channels {{len(channels)}}.")
            raise ValueError("Length of bias_voltages must match length of channels.")

        # Set the bias voltages for each channel individually
        for channel, voltage in zip(channels, bias_voltages):
            self._set_bias_channel(board, channel, voltage)
        
