import os
import paramiko
from scanctrl.logger import logger  # Import the global logger
import os
from typing import List, Optional


class SSHCtrl:
    """
    A class to manage commands on a remote hardware via SSH.
    Handles connection lifecycle, authentication, and command execution.
    """

    def __init__(self, username: str, hostname: str, password_env_var: str = "SSH_PASSWORD"):
        """
        Initializes the controller and establishes the SSH connection.
        
        Args:
            hostname (str): The IP address or domain of the remote server.
            username (str): The SSH username.
            password_env_var (str): The name of the environment variable containing the password.
        """
        self.hostname = hostname
        self.username = username
        self.password_env_var = password_env_var
        self._ssh_client = None
        self._connected = False
        
        self._connect()

    def __del__(self):
        """
            Destructor to ensure connection is closed when object is garbage collected.
        """
        if self._connected:
            self.close()

    def __enter__(self):
        """
            Context manager entry.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
            Context manager exit (ensures close).
        """
        self.close()
    

    #-----------------------
    # Helper functions
    #-----------------------

    def _connect(self):
        """
            Establishes the SSH connection.
        """
        if self._connected:
            logger.warning("Connection already established.")
            return

        try:
            # Retrieve password securely from environment
            password = os.getenv(self.password_env_var)
            if not password:
                raise EnvironmentError(
                    f"Environment variable '{self.password_env_var}' is not set. "
                    "Please export SSH_PASSWORD before running the script."
                )

            self._ssh_client = paramiko.SSHClient()
            self._ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())
            
            self._ssh_client.connect(
                hostname=self.hostname,
                username=self.username,
                password=password,
                allow_agent=True,
                look_for_keys=True,
                timeout=10
            )
            
            self._connected = True
            logger.info(f"Successfully connected to {self.hostname} as {self.username}")

        except paramiko.AuthenticationException:
            logger.error("Authentication failed. Check username/password.")
            raise
        except paramiko.SSHException as e:
            logger.error(f"SSH connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            raise

    def _ensure_connected(self):
        """
            Helper to ensure connection exists before running commands.
        """
        if not self._connected or not self._ssh_client:
            self._connect()

    #-----------------------
    # Command execution functions
    #-----------------------

    def run_command(self, command: str) -> str:
        """
            Generic method to run any shell command on the remote server.
            
            Args:
                command (str): The shell command to execute.
                
            Returns:
                str: The stdout output.
        """
        self._ensure_connected()
        
        logger.info(f"Executing generic command: {command}")
        
        try:
            stdin, stdout, stderr = self._ssh_client.exec_command(command, get_pty=True)
            output = stdout.read().decode('utf-8')
            error_output = stderr.read().decode('utf-8')
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                logger.error(f"Command failed: {exit_status} - {error_output}")
                raise RuntimeError(f"Command failed: {error_output}")
                
            return output
            
        except Exception as e:
            logger.error(f"Error executing generic command: {e}")
            raise

    def transfer_file(self, local_path: str, remote_dir: str, remote_filename: str = None):
        """
        Transfers a file from the local machine to the remote server using SFTP over the existing SSH connection.
        
        Args:
            local_path (str): The path to the file on the local machine (e.g., "data.csv").
            remote_dir (str): The directory on the remote server where the file should be saved.
            remote_filename (str, optional): The name of the file on the remote server. By default, it will use
                                            the same name as the local file.
        """
        self._ensure_connected()

        if remote_filename is None:
            remote_filename = os.path.basename(local_path)
        
        # Construct the full remote path
        remote_full_path = os.path.join(remote_dir, remote_filename)
        
        logger.debug(f"Starting file transfer: {local_path} -> {remote_full_path}")
        
        try:
            # Open an SFTP session over the existing SSH connection
            sftp = self._ssh_client.open_sftp()
            
            # Perform the upload
            sftp.put(local_path, remote_full_path)
            
            logger.debug(f"File transfer successful: {remote_full_path}")
            
        except FileNotFoundError:
            logger.error(f"Local file not found: {local_path}")
            raise
        except paramiko.SFTPError as e:
            logger.error(f"SFTP transfer error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during file transfer: {e}")
            raise
        finally:
            # Close the SFTP session, but keep the main SSH connection open
            sftp.close()


    def close(self):
        """
            Closes the SSH connection.
        """
        if self._connected and self._ssh_client:
            try:
                self._ssh_client.close()
                self._connected = False
                logger.info("SSH connection closed.")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
