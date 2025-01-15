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

@click_shell.shell(prompt='drunc-process-launcher > ')
def launcher():
    global processes
    signal.signal(signal.SIGHUP, terminate_all)


@launcher.command()
@click.argument("cmd")
def launch(cmd:str):
    global processes
    proc = subprocess.Popen(cmd, shell=True)
    print(f"Started process with pid {proc.pid}")
    processes.append(proc)


if __name__ == '__main__':
    launch()