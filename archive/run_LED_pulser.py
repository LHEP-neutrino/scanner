import paramiko
import time
class pulser:
    def run_pulser(hostname, username, password, duration):
        # Connect to the remote server
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname, username=username, password=password, allow_agent=False, look_for_keys=False)
        
        # Execute the script
        _, stdout, stderr = ssh_client.exec_command(f'ppulse run-trigger -d {duration}', get_pty=True)  

        # Print the output
        #for line in stdout.readlines():
        #    print(line.strip())

        # Close the connection
        time.sleep(2)

        ssh_client.close()

    def setting_of_pulser(hostname, username, password, channel, s, p):
        # Connect to the remote server
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname, username=username, password=password, allow_agent=False, look_for_keys=False)
        
        # Execute the script
        _, stdout, stderr = ssh_client.exec_command(f'ppulse set-channel -ch {channel} -s {s} -p {p} ', get_pty=True) 

        # Print the output
        for line in stdout.readlines():
            print(line.strip())

        # Close the connection
        time.sleep(2)

        ssh_client.close()

    def period_of_puls(hostname, username, password, period):
        # Connect to the remote server
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname, username=username, password=password, allow_agent=False, look_for_keys=False)
        
        # Execute the script
        _, stdout, stderr = ssh_client.exec_command(f'ppulse set-trigger -p {period} ', get_pty=True) 

        # Print the output
        for line in stdout.readlines():
            print(line.strip())

        # Close the connection
        time.sleep(2)

        ssh_client.close()

# Pulser settings
hostname = '130.92.128.165'
username = 'pi'
password = 'altisidora'
#duration = '10' #s
#channel = '1' 
#s = '200' 
#p = '0' #only put p larger than zero if s is at zero
#period = '10' #ms

#pulser.run_pulser(hostname, username, password, duration)
#pulser.setting_of_pulser(hostname, username, password, channel, s, p)
#pulser.period_of_puls(hostname, username, password, period)
