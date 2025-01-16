# SSH Process Multiplexer

This is a simple tool to run multiple processes over SSH and interact with them.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Play
```
After finishing, you can exit the virtual environment with the command `deactivate` (or just close the shell).

This tool requires password less ssh keys to be able to ssh to the remote host. To do this and be able to run the example below, you can do:
```bash
ssh-keygen
# Then press enter twice without entering a passphrase
ssh-copy-id localhost # or your remote host
# Enter your machine password one last time
# You can now check that the ssh key works by running:
ssh localhost
# You should not be prompted for a password
```

## Usage

```bash
python3 ssh_proc_mux.py
ssh-proc-mux > launch "sleep 10 && touch ABC" localhost
ssh-proc-mux > launch "sleep 10 && touch DEF" localhost
ssh-proc-mux > launch "sleep 10 && touch GHI" localhost
ssh-proc-mux > launch "sleep 10 && touch JKL" localhost
ssh-proc-mux > launch "sleep 10 && touch MNO" localhost
```
Hopefully, you now have 5 files in your current directory, named ABC, DEF, GHI, JKL and MNO.

## Description

This tool uses a python launcher `launcher.py` to start subprocesses on the remote host. `ssh_proc_mux.py` just waits for the python prompt in `launcher.py` to start and then stdin command to it. The upshot is that there isn't any socket opened by `launcher.py`, so it can be run on a remote host without any firewall rules.
