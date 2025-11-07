import paramiko
import time
class bias_voltage_control:
    def set_all_bias_voltage_on(hostname, username, password, voltage, board):
        # Connect to the remote server
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname, username=username, password=password, allow_agent=False, look_for_keys=False)
        
        # Execute the script
        _, stdout, stderr = ssh_client.exec_command(f'supplr set-channels --voltage {voltage} --board {board}', get_pty=True)  

        # Print the output
        #for line in stdout.readlines():
        #    print(line.strip())

        # Close the connection
        time.sleep(20)

        ssh_client.close()

    def set_channel_bias_voltage_on(hostname, username, password, voltage, board, channel):
        # Connect to the remote server
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname, username=username, password=password, allow_agent=False, look_for_keys=False)
        
        # Execute the script
        _, stdout, stderr = ssh_client.exec_command(f'supplr set-channel --channel {channel} --voltage {voltage} --board {board}', get_pty=True)  

        # Print the output
        #for line in stdout.readlines():
        #    print(line.strip())

        # Close the connection
        time.sleep(20)

        ssh_client.close()

    def set_all_bias_voltage_off(hostname, username, password, board):
        # Connect to the remote server
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname, username=username, password=password, allow_agent=False, look_for_keys=False)
        
        # Execute the script
        _, stdout, stderr = ssh_client.exec_command(f'supplr set-channels --voltage 1 --board {board}', get_pty=True)  

        # Print the output
        #for line in stdout.readlines():
        #    print(line.strip())

        # Close the connection
        time.sleep(20)

        ssh_client.close()

    def set_all_bias_voltage_from_file_on(hostname, username, password, board, file_name):
        # Connect to the remote server
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname, username=username, password=password, allow_agent=False, look_for_keys=False)
        
        # Execute the script
        _, stdout, stderr = ssh_client.exec_command(f'supplr set-channel-file --board {board} --file {file_name}', get_pty=True)  

        # Print the output
        #for line in stdout.readlines():
        #    print(line.strip())

        # Close the connection
        time.sleep(20)

        ssh_client.close()

    def restart_supplr(hostname, username, password):
        # Connect to the remote server
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname, username=username, password=password, allow_agent=False, look_for_keys=False)
        
        # Execute the script
        _, stdout, stderr = ssh_client.exec_command(f'sudo systemctl restart supplr', get_pty=True)  

        # Print the output
        #for line in stdout.readlines():
        #    print(line.strip())

        # Close the connection
        time.sleep(10)

        ssh_client.close()


  

# Bias voltage settings
hostname = '130.92.128.188'
username = 'pi'
password = 'altisidora'
VGA_board = '20'
bias_voltage = '20'

#bias_voltage_control.restart_supplr(hostname, username, password)
#bias_voltage_control.set_all_bias_voltage_on(hostname, username, password, bias_voltage, VGA_board)
#bias_voltage_control.set_all_bias_voltage_off(hostname, username, password, VGA_board)

