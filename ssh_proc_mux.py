import click
import click_shell
import time
import sh
import logging
import signal
import getpass
import threading
from functools import partial
import os
import queue
from ctypes import cdll


ssh_sessions = {}
ssh_session_ready = {}
interrupted = False
command_buffer = {}
platform = os.uname().sysname.lower()
macos = "darwin" in platform


ssh_logger = logging.getLogger("ssh_stdout")

# ------------------------------------------------
# Credits to Alessandro Thea for the following
# pexpect.spawn(...,preexec_fn=on_parent_exit('SIGTERM'))

# Constant taken from http://linux.die.net/include/linux/prctl.h
PR_SET_PDEATHSIG = 1


class PrCtlError(Exception):
    pass


def pre_execution_hook(signal_parent_exit, ignore_signals=[]):
    """
    Return a function to be run in a child process which will trigger
    SIGNAME to be sent when the parent process dies
    """

    def set_parent_exit_signal():
        for ignore_signal in ignore_signals:
            signal.signal(ignore_signal, signal.SIG_IGN)

        if macos:
            return

        # http://linux.die.net/man/2/prctl
        result = cdll["libc.so.6"].prctl(PR_SET_PDEATHSIG, signal_parent_exit)
        if result != 0:
            raise PrCtlError("prctl failed with error code %s" % result)

    return set_parent_exit_signal
# ------------------------------------------------


class SSHLauncherProcessWatcherThread(threading.Thread):
    def __init__(self, host, process):
        threading.Thread.__init__(self)
        self.host = host
        self.process = process

    def run(self):
        global ssh_sessions

        try:
            self.process.wait()

        except sh.SignalException_SIGKILL:
            pass

        except sh.ErrorReturnCode as e:
            print(f"Host {self.host} process exited with error {e}")
            ssh_session_ready[self.host] = -abs(e.exit_code)

        finally:
            print(f"Host {self.host} process exited")
            if self.host in ssh_sessions:
                del ssh_sessions[self.host]

            if self.host in ssh_session_ready and ssh_session_ready[self.host] > 0:
                ssh_session_ready[self.host] = 0


def watch_process(host, process):
    t = SSHLauncherProcessWatcherThread(host, process)
    t.start()


def ssh_interact(host, char):
    global ssh_session_ready

    this_logger = logging.getLogger(f"ssh_stdout.{host}")
    this_logger.info(char[:-1])  # We print all the stdout in the shell

    if "Starting launcher" in char:
        ssh_session_ready[host] = 1


@click_shell.shell(
    prompt="ssh-proc-mux > ", hist_file=os.path.expanduser("~/.ssh_proc_mux.history")
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    default="INFO",
)
@click.pass_context
def ssh_proc_mux_shell(ctx, log_level: str):
    logging.basicConfig(format="%(name)s: %(message)s", level=log_level.upper())
    sh_logger = logging.getLogger("sh")
    sh_logger.setLevel(logging.WARNING)

    def cleanup():
        global ssh_sessions, interrupted, ssh_session_ready

        interrupted = True

        for host in ssh_session_ready:
            ssh_session_ready[host] = -1
        ssh_session_ready = {}

        for session in ssh_sessions.values():
            session.kill()
        ssh_sessions = {}

    ctx.call_on_close(cleanup)


def init_ssh_session(host):
    global ssh_sessions, command_buffer, ssh_session_ready
    pwd = os.getcwd()
    username = getpass.getuser()
    ssh_arguments = [
        "-tt",
        f"{username}@{host}",
        f"cd {pwd} && source venv/bin/activate && python3 launcher.py",
    ]

    if host not in ssh_sessions:
        try:
            print(f"Starting ssh session for {host}")

            command_buffer[host] = queue.Queue()
            ssh_session_ready[host] = 0

            ssh_sessions[host] = sh.ssh(
                *ssh_arguments,
                _bg=True,
                _bg_exc=False,
                _err_to_out=True,
                _out=partial(ssh_interact, host),
                _in=command_buffer[host],
                _preexec_fn=pre_execution_hook(signal.SIGTERM, [signal.SIGINT]),
                _new_session=True,
            )

            watch_process(host, ssh_sessions[host])

            print(f"Host {host} processes are children of {ssh_sessions[host].pid}")

        except Exception as e:
            raise e


    max_wait = 20

    while ssh_session_ready[host] <= 0:
        time.sleep(0.1)
        max_wait -= 1
        if max_wait <= 0:
            print(f"SSH could not start on {host}")
            return


@ssh_proc_mux_shell.command()
@click.argument("cmd")
@click.argument("host")
@click.option("--id", type=str, default=None)
def launch(cmd: str, host: str, id:str=None):
    global command_buffer
    init_ssh_session(host)
    if id is not None:
        command_buffer[host].put(f'launch "{cmd}" --id {id}\r')
    else:
        command_buffer[host].put(f'launch "{cmd}"\r')


@ssh_proc_mux_shell.command()
@click.argument("host")
def ps(host: str):
    global command_buffer
    init_ssh_session(host)
    command_buffer[host].put("ps\r")


@ssh_proc_mux_shell.command()
@click.argument("host")
def killall(host: str):
    global command_buffer
    init_ssh_session(host)
    command_buffer[host].put("killall\r")


@ssh_proc_mux_shell.command()
@click.argument("pid", type=int)
@click.argument("host", type=str)
def kill(pid: int, host:str):
    global command_buffer
    init_ssh_session(host)
    command_buffer[host].put(f"kill {pid}\r")


@ssh_proc_mux_shell.command()
@click.argument("host")
def disconnect(host: str):
    global ssh_sessions
    if host in ssh_sessions:
        ssh_sessions[host].kill()
        del ssh_sessions[host]


if __name__ == "__main__":
    ssh_proc_mux_shell()
