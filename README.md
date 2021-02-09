# . How-To connection_ubuntu
### (1) import ubuntu connection
    import connection_ubuntu
### (2) create ubuntu instance
    uss = connection_ubuntu.UbuntuSession(ubuntu_ip="10.10.10.1")
#### below is the connection __init__ function, if the default value is not desired, change your code accordingly
    def __init__(self, ubuntu_ip="10.10.10.1", ubuntu_port=22, username='demon', password='letmein', logfile="ubuntu_session.log", prompt=None):
### (3) method ubuntu connection provides
    shell(self, cmd, toList=False, timeout=None)
    scp_to_ubuntu(self, local_file, remote_file, scp_from_ubuntu=False, scp_timeout=None)
#### parameter info, please check the cEdge help, it is similar
1. `local_file`, it is relative path. If upload to ubuntu server, this must be file, if download from ubuntu server, it could be directory. `remote_file`, it must be absolute path. If upload to ubuntu server, it could be directory, if download from ubuntu server, it must be file.  `scp_from_ubuntu` switch to change upload or download, default is upload. `scp_timeout`, the wait timer for upload or download. If it is not give, default is 1h, if 1h upload/download not finished, error will return.
### (4) basic function usage demo
```python

import connection_ubuntu
uss = connection_ubuntu.UbuntuSession('10.10.10.1')
res = uss.shell('pwd')
res = uss.shell('sudo ls /root')
res = uss.scp_to_ubuntu(local_file='README.md',remote_file='/home/demon/testDir/ ',scp_from_ubuntu=False)
res = uss.scp_to_ubuntu(local_file='test_files.log',remote_file='/home/demon/testDir/test_files.log',scp_from_ubuntu=True)

```

<details><summary>Python interactive detail demo</summary>
<p>
    
```python
>>> import connection_ubuntu
>>> uss = connection_ubuntu.UbuntuSession('10.10.10.1')
>>> uss.shell('pwd')
[True, '/home/demon']
>>> uss.shell('cd /home/demon/testDir')
[True, '']
>>> uss.shell('pwd')
[True, '/home/demon/testDir']
>>> uss.shell('ls')
[True, 'test_files.log']
>>> uss.shell('ls /root')
[False, 'ls: cannot open directory /root: Permission denied']
>>> uss.shell('sudo ls /root')
[True, 'App-Asciio-1.51.3\t\t asciio_1.51.3.orig.tar.ddgz\nAsciio.pm\t\t\t cacert.pem\nDesktop\t\t\t\t epel-release-latest-7.noarch.rpm\nDocuments\t\t\t google-chrome-stable_current_x86_64.rpm\nDownloads\t\t\t google-chrome-stable_current_x86_64.rpm.1\nMusic\t\t\t\t initial-setup-ks.cfg\nPictures\t\t\t nohup.out\nPublic\t\t\t\t perl5\nTemplates\t\t\t serect.txt\nVideos\t\t\t\t test.sh\nanaconda-ks.cfg\t\t\t thinclient_drives\nansible-2.9.13-1.el7.noarch.rpm']
>>> uss.scp_to_ubuntu(local_file='README.md',remote_file='/home/demon/testDir/ ',scp_from_ubuntu=False)
[True, 'scp is sucessfully done!']
>>> uss.shell('ls')
[True, 'README.md  test_files.log']
>>> import os.path
>>> os.path.isfile('test_files.log')
False
>>> uss.scp_to_ubuntu(local_file='test_files.log',remote_file='/home/demon/testDir/test_files.log',scp_from_ubuntu=True)
][True, 'scp is sucessfully done!']
>>> os.path.isfile('test_files.log')
True
>>>
### If you really need to run interactive CMD, follow the below, please notice: 
### If you are running interactive CMD, mode will be changed to interactive MODE, you must finish the CMD before run shell, but SCP is not impacted
demon@vtest02-demyang:~$ cat test.sh
#!/usr/bin/env bash
while true
do
 echo "send your name"
 read passwd
 if [ $passwd = 'exit' ]
  then
    break
  fi
 echo "hello $passwd"
done
demon@vtest02-demyang:~$ ./test.sh
send your name
demon
hello demon
send your name
xiaojian
hello xiaojian
send your name
exit
### demo how to use above python to interactivate with above shell
>>> import connection_ubuntu
>>> uss = connection_ubuntu.UbuntuSession('10.75.28.150')
]>>> uss.interactive_cmd('./test.sh')
>>> uss.interact_cmd_output
'./test.sh\r\nsend your name\r\n'
>>> uss.interact_cmd_send('demon')
[True, 'CMD is sent']
>>> uss.interact_cmd_output
'./test.sh\r\nsend your name\r\ndemon\r\nhello demon\r\nsend your name\r\n'
>>> uss.interact_cmd_send('xiaojian')
[True, 'CMD is sent']
>>> uss.interact_cmd_output
'./test.sh\r\nsend your name\r\ndemon\r\nhello demon\r\nsend your name\r\nxiaojian\r\nhello xiaojian\r\nsend your name\r\n'
>>> uss.interact_cmd_stop()
[True, 'Exit interactive mode']
>>> uss.shell("ls")
```
</details>

