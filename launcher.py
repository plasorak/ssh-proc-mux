import signal
import os
import subprocess
import click
import click_shell


def terminate_all(sig, frame):
    print("SIGHUP received")
    pgrp = os.getpgid(os.getpid())
    os.killpg(pgrp, signal.SIGKILL)


processes = []
pid_to_command = {}


@click_shell.shell(
    prompt="local-process-launcher > ", hist_file=os.path.expanduser("~/.local_process_launcher.history")
)
def launcher():
    global processes
    signal.signal(signal.SIGHUP, terminate_all)


@launcher.command()
def echo():
    print("echo")


@launcher.command()
@click.argument("cmd")
def launch(cmd: str):
    global processes, pid_to_command
    print(f"Launching {cmd}")
    proc = subprocess.Popen(cmd, shell=True)
    print(f"Started process with pid {proc.pid} ({cmd})")
    processes.append(proc)
    pid_to_command[proc.pid] = cmd


@launcher.command()
def ps():
    global processes, pid_to_command
    for proc in processes:
        print(
            f"Process {proc.pid} ({pid_to_command[proc.pid]})"
            + (
                " is running"
                if proc.poll() is None
                else f" exited with code {proc.poll()}"
            )
        )


@launcher.command()
def killall():
    global processes
    for proc in processes:
        if proc.poll() is not None:
            continue
        proc.kill()
        pid_to_command.pop(proc.pid)
    processes = []


if __name__ == "__main__":
    print("Starting launcher")
    launcher()
