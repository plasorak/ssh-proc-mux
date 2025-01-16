import signal
import os
import time
import subprocess
import click
import click_shell

def terminate_all(sig, frame):
    print('SIGHUP received')
    pgrp = os.getpgid(os.getpid())
    os.killpg(pgrp, signal.SIGKILL)

processes = []

@click_shell.shell(prompt='local-process-launcher > ', hist_file='~/.local_process_launcher.history')
def launcher():
    global processes
    signal.signal(signal.SIGHUP, terminate_all)

@launcher.command()
def echo():
    print("echo")

@launcher.command()
@click.argument("cmd")
def launch(cmd:str):
    global processes
    proc = subprocess.Popen(cmd, shell=True)
    print(f"Started process with pid {proc.pid} ({cmd})")
    processes.append(proc)


@launcher.command()
def ps():
    global processes
    for proc in processes:
        print(f"Process {proc.pid}" if proc.poll() is None else f"Process {proc.pid} exited with code {proc.poll()}")


@launcher.command()
def killall():
    global processes
    for proc in processes:
        if proc.poll() is not None:
            continue
        proc.kill()
    processes = []


if __name__ == '__main__':
    print("Starting launcher")
    launcher()