import sys
import pexpect
import re
import time

class UbuntuSession():

    def __init__(self, ubuntu_ip="8.8.8.8", ubuntu_port=22, username='xiaojian', password='letmein', logfile="linux_session.log", prompt=None):
        self.ip = ubuntu_ip
        self.interact_mode = False
        if logfile is not None:
            self.logfile = open(logfile, 'a')
        else:
            self.logfile = None
        self.port = ubuntu_port
        self.username = username
        if self.username == "root":
            self.isroot = True
        else:
            self.isroot = False

        self.ssh_multiplex = True
        if self.ssh_multiplex:
            if logfile is None and logfile != sys.stdout:
                self.control_path =  str(logfile)+".path"
            else:
                self.control_path = "~/.ssh/control.path"
        self.password = password
        self.timeout = 10
        self.scp_session = None
        self.loguser_input = False
        if prompt is None:
            self.prompt = "connection_ubuntu#"
        else:
            self.prompt = prompt
        self.PS1 = 'export PS1="{}" '.format(self.prompt)
        self.prompt = str(self.prompt).replace('-','\-')
        self.session = self.create_ubuntu_session()
        self.current_mode = 'exec'
 
        self.total_log = ""
        self.tmp_log = ""
        self.log_new = ""
        self.stop_thread = False
        self.wait = False
        self.wait_mode = False

    def create_ubuntu_session(self):
        self.interact_mode = False
        ubuntu_ip, username, password, logfile, timeout = self.ip, self.username, self.password, self.logfile, self.timeout
        """create new session for cedge"""
        cmd = 'ssh -o StrictHostKeyChecking=no '
        cmd += '-o UserKnownHostsFile=/dev/null '
        cmd += '-o ConnectTimeout=10 '
        if self.ssh_multiplex:
            cmd += '-M -S {} '.format(self.control_path)
        cmd += '-o LogLevel=QUIET -l %s %s' % (username, ubuntu_ip)
        

        pySession = pexpect.spawn(cmd, timeout=timeout)
        if logfile is None:
            logfile = self.logfile
        if logfile is not None:
            if self.loguser_input:
                pySession.logfile = sys.stdout
                pySession.logfile = logfile
            else:
                pySession.logfile_read = sys.stdout
                pySession.logfile_read = logfile
        else:
            if self.loguser_input:
                pySession.logfile = sys.stdout
            else:
                pySession.logfile_read = sys.stdout
        promptMatchedID = pySession.expect(['[pP]assword:', '.*[#$]', pexpect.TIMEOUT], timeout)
        if promptMatchedID == 0:
            pySession.sendline(password)
            promptMatchedID = pySession.expect(['.*[#$]', pexpect.TIMEOUT], timeout)
            if promptMatchedID:
                print("Incorrect credential")
                sys.exit(1)
            pySession.sendline(self.PS1)
            promptMatchedID = pySession.expect([self.prompt, pexpect.TIMEOUT], timeout)
            if promptMatchedID:
                print("export PS1 failed 01")
                sys.exit(1)
            self.clear_session_cache(pySession)
            pySession.sendline("")
            promptMatchedID = pySession.expect([self.prompt, pexpect.TIMEOUT], timeout)
            if promptMatchedID:
                print("export PS1 failed 01")
                sys.exit(1)
            return pySession
        elif promptMatchedID == 1:
            pySession.sendline(self.PS1)
            promptMatchedID = pySession.expect([self.prompt, pexpect.TIMEOUT], timeout)
            if promptMatchedID:
                print("export PS1 failed 02")
                sys.exit(1)
            self.clear_session_cache(pySession)
            pySession.sendline("")
            promptMatchedID = pySession.expect([self.prompt, pexpect.TIMEOUT], timeout)
            if promptMatchedID:
                print("export PS1 failed 01")
                sys.exit(1)
            return pySession          
        else:
            print("Couldn't connect to Node, please manually test ssh!")
        return pySession

    def relogin_ubuntu_session(self):
        self.session.close()
        self.session = self.create_ubuntu_session()
        self.interact_mode = False
        if not self.session.isalive():
            print("Could not relogin")
            self.clear_session_cache()
            return False   
        else:
            return True

    def send_control(self, str):
        status = self.session.sendcontrol(str)
        return [True, status]

    def clear_session_cache(self, session=None):
        if session is None:
            session = self.session
        if not session.isalive():
            return [False, 'session is down']

        buffer = ''
        while not session.expect([r'.+', pexpect.TIMEOUT], timeout=0.5):
            buffer += session.after
        return [True, buffer]

    def shell(self, cmd, toList=False, timeout=None):
        if self.interact_mode:
            return [False, "You are in interactive Mode, SHELL is not available"]
        if not self.session.isalive():
            if not self.relogin_ubuntu_session():
                return [False, "Ubuntu could not login"]

        if timeout is None:
            timeout = self.timeout

        self.session.sendline(cmd)
        promptMatchedID = self.session.expect([self.prompt, '[pP]assword', pexpect.TIMEOUT], timeout)
        if promptMatchedID == 0:
            cmd_output_raw = self.session.before
            cmd_output = cmd_output_raw.replace("\r\n","\n").replace("\r","").split("\n")[1:-1]
            if not toList:
                cmd_output = '\n'.join(cmd_output)
            debug = self.session.before + self.session.after

        elif promptMatchedID == 1:

            self.session.sendline(self.password)
            promptMatchedID = self.session.expect([self.prompt, '[pP]assword', pexpect.TIMEOUT], timeout)
            if promptMatchedID == 0:
                cmd_output_raw = self.session.before
                cmd_output = cmd_output_raw.replace("\r\n","\n").replace("\r","").split("\n")[1:-1]
                if not toList:
                    cmd_output = '\n'.join(cmd_output)
                debug = self.session.before + self.session.after
            elif promptMatchedID == 1:
                print("Unexpected interactive command is met, issue!!!")
                self.send_control("c")
                return [False, "interactive command needs passwd, seems you try to switch to other user, it is not supported, use sudo instead!"] 
            else:
                print("It seems you login to other user account, it is not supported, use su -c to exec other user command")
                self.session.sendline("exit")
                return [False, "Timeout to wait for the command excution"]    
                  
        else:
            self.clear_session_cache()
            return [False, self.session.before + self.session.after]

        self.session.sendline("echo $?")
        promptMatchedID = self.session.expect([self.prompt, pexpect.TIMEOUT], timeout)
        if promptMatchedID !=0:
            print("Unknow error, could not get shell exec state")
            self.clear_session_cache()
            return [False, debug] 
        state = self.session.before
        state = state.replace("\r\n","\n")
        state = state.replace("\r","")
        code = state.split("\n")[1:-1][0]

        self.clear_session_cache()
        if code != '0':
            return [False, cmd_output]
        else:
            return [True, cmd_output]

    def scp_to_ubuntu(self, local_file, remote_file, scp_from_ubuntu=False, recursive=False, scp_timeout=None):
        ## Notice, currently only linux server to linux server scp is supported, router <-> server is not supported!
        if not self.session.isalive():
            if not self.relogin_ubuntu_session():
                return [False, "Ubuntu could not login"] 

        import subprocess
        use_ssh_session=True

        local_file=local_file.strip().rstrip('/')
        remote_file=remote_file.strip().rstrip('/')
        if remote_file.startswith('/'):
            remote_file = '/' + remote_file

        if use_ssh_session and self.ssh_multiplex:
            option = '-o ControlPath={}'.format(self.control_path)
            if scp_from_ubuntu:
                source = '{}@{}:{}'.format(self.username, self.ip, remote_file)
                target = local_file
            else:
                source = local_file
                target = '{}@{}:{}'.format(self.username, self.ip, remote_file)
            
            if not recursive:
                process = subprocess.Popen(['scp', option, source, target], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                process = subprocess.Popen(['scp', '-r', option, source, target], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if scp_timeout is None:
                scp_timeout = 3600
            try:
                if sys.version_info[0] == 2:
                    return_code = process.wait()
                else:
                    return_code = process.wait(scp_timeout)
                if return_code == 0:
                    return [True, "scp is sucessfully done!"]
                else:
                    return [False, process.stderr.read()]
            except:
                return [False, "scp is timeout"]
        else:
            return [False, "Currently only use_ssh_session is supported"]

    # def interactive_cmd(self, cmd):
    #     self.interact_mode = True
    #     ## Notice, if you use sudo, make sure sudo do not need passwd, or use root login session instead
    #     if not self.session.isalive():
    #         if not self.relogin_ubuntu_session():
    #             return [False, "Ubuntu could not login"] 
    #     import subprocess
    #     ## Notice, currently only linux server to linux server scp is supported, router <-> server is not supported!
    #     option = '-o ControlPath={}'.format(self.control_path)
    #     target = '{}@{}'.format(self.username, self.ip)
    #     process = subprocess.Popen(['ssh', option, target, cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIP)
    #     return process
    def interactive_cmd(self, cmd):
        self.total_log = ""
        self.tmp_log = ""
        self.log_new = ""
        self.stop_thread = False
        self.wait = False
        self.wait_mode = False

        self.session.sendline(cmd)

        import Queue
        from threading import Thread
        q = Queue.Queue()
        self.q = q

        def interactive_thread(queue):
            self.interact_mode = True
            while True:
                self.wait_mode = False

                if not q.empty():
                    cmd = q.get()
                    self.session.sendline(cmd)

                if self.stop_thread:
                    self.interact_mode = False
                    break

                if not self.session.isalive():
                    self.relogin_ubuntu_session()
                    print("SSH session Unexpected down, exit interactive mode")
                    break

                while not self.session.expect([r'.+', pexpect.TIMEOUT], timeout=0.01):
                    self.log_new += self.session.after
                    self.tmp_log += self.session.after

                ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
                tmp_log = ansi_escape.sub('', self.tmp_log)
                if re.search(self.prompt, tmp_log):
                    print("Interactive cmd seems stopped!")
                    self.interact_mode = False
                    return

                if self.wait:
                    while True:
                        self.wait_mode = True

                        if self.stop_thread:
                            self.interact_mode = False
                            return
                        time.sleep(0.01)

                        if not self.wait:
                            self.tmp_log = self.total_log
                            break

        conn_thread = Thread(target = interactive_thread, args = (q, ))
        conn_thread.setDaemon(True)
        conn_thread.start()

    def request_interact_thread_wait(self):
        self.wait = True

        for second in range(1000):
            if self.wait_mode:
                return [True, 'Interact thread is in wait mode']
            time.sleep(0.01)
        else:
            return [False, "could not put interact thread to wait"]        

    def request_interact_thread_work(self):
        self.wait_mode = True
        self.wait = False

        for second in range(1000):
            if not self.wait_mode:
                return [True, 'Interact thread is in working mode']
            time.sleep(0.01)
        else:
            return [False, "could not put interact thread to working mode"] 

    @property
    def new_output_since_last_read(self):
        if not self.request_interact_thread_wait()[0]:
            print("Error: Not able to read output")
            return ""

        new_log = self.log_new
        self.log_new = ""
        self.total_log += new_log
        self.request_interact_thread_work()
        ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
        return ansi_escape.sub('', new_log)

    @property
    def interact_cmd_output(self):
        # Since Log is stored in memory, if long run might be too big, but it might not need solve now. 
        # self.total_log  = self.toal_log[-10000:] will solve the issue.

        if not self.request_interact_thread_wait()[0]:
            print("Error: Not able to read output")
            return ""
        self.total_log +=  self.log_new
        self.log_new = ""
        self.request_interact_thread_work()
        ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
        return ansi_escape.sub('', self.total_log)

    def force_no_interactive_mode(self):
        self.interact_mode = False

    def interact_cmd_stop(self):
        self.stop_thread = True

        for second in range(3000):
            if not self.interact_mode:
                break
            time.sleep(0.01)
        else:
            return [False, "Interactive Thread could not be stopped"]

        self.send_control("c")
        promptMatchedID = self.session.expect([self.prompt, pexpect.TIMEOUT], self.timeout)
        if promptMatchedID == 0:
            return [True, "Exit interactive mode"]
        else:
            return [False, "Could not exit interactive mode"]

    def interact_cmd_send(self, cmd):
        if type(cmd) != str:
            return [False, "CMD only support String"]

        if not self.interact_mode:
            print("Method only use in interact cmd!")
            return [False, "It is not in interace mode!"]

        self.q.put(cmd)

        return [True, "CMD is sent"]

