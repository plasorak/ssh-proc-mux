import click
import click_shell
from sh.contrib import ssh
import sys
import time
import sh
import logging
import getpass
import threading
import os
ssh_sessions = {}

aggregated = ""
command_buffer = ""
ssh_logger = logging.getLogger('ssh_stdout')

class SSHLauncherProcessWatcherThread(threading.Thread):
    def __init__(self, host, process):
        threading.Thread.__init__(self)
        self.host = host
        self.process = process

    def run(self):
        global ssh_sessions

        try:
            self.process.wait()

        except sh.SignalException_SIGKILL as e:
            pass

        except sh.ErrorReturnCode as e:
            print(e)

        finally:
            print(f'Host {self.host} process exited')
            if self.host in ssh_sessions:
                del ssh_sessions[self.host]


def watch_process(host, process):
    t = SSHLauncherProcessWatcherThread(host, process)
    t.start()


def ssh_interact(char, stdin):
    global aggregated, command_buffer

    ssh_logger.info(char) # We print all the stdout in the shell

    if "local-process-launcher > " in char:
        time.sleep(0.1)
        return

    if command_buffer == "":
        time.sleep(0.1)
        return

    stdin.put(f'launch "{command_buffer}"\r')
    command_buffer = ""


@click_shell.shell(prompt='ssh-proc-mux > ')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], case_sensitive=False), default='INFO')
@click.pass_context
def ssh_client(ctx, log_level:str):
    logging.basicConfig(format='%(name)s: %(message)s', level=log_level.upper())
    sh_logger = logging.getLogger('sh')
    sh_logger.setLevel(logging.WARNING)

    def cleanup():
        global ssh_sessions
        for session in ssh_sessions.values():
            session.kill()
        ssh_sessions = {}

    ctx.call_on_close(cleanup)


@ssh_client.command()
@click.argument("cmd")
@click.argument("host")
def launch(cmd:str, host:str):
    global ssh_sessions, command_buffer
    pwd = os.getcwd()
    username = getpass.getuser()
    ssh_arguments = [
        '-tt',
        f'{username}@{host}',
        f'cd {pwd} && source venv/bin/activate && python3 launcher.py',
    ]

    if host not in ssh_sessions:
        try:
            ssh_sessions[host] = sh.ssh(*ssh_arguments, _bg=True, _out=ssh_interact)
            watch_process(host, ssh_sessions[host])
        except Exception as e:
            print(e)
            return

    print(f"Host {host} processes are children of {ssh_sessions[host].pid}")

    command_buffer = cmd


@ssh_client.command()
def kill():
    global ssh_sessions
    for session in ssh_sessions.values():
        session.kill()
    ssh_sessions = {}


if __name__ == '__main__':
    ssh_client()