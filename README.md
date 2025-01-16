# SSH Process Multiplexer

This is a simple tool to run multiple processes over SSH and interact with them.

## Installation
```bash
git clone https://github.com/plasorak/ssh-proc-mux.git
cd ssh-proc-mux
python3 -m venv venv # You are not allowed to change the name of the venv!
source venv/bin/activate
pip install -r requirements.txt
# Play
```
Note there _has to_ be a `venv` directory in the `PWD` for this to work. The `venv` directory is hardcoded in the `ssh_proc_mux.py` file.

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
ssh-proc-mux > launch 'echo \"Hello World ABC\" && sleep 10 && echo \"Now touching ABC\" && touch ABC' localhost
ssh-proc-mux > launch 'echo \"Hello World DEF\" && sleep 10 && echo \"Now touching DEF\" && touch DEF' localhost
ssh-proc-mux > launch 'echo \"Hello World GHI\" && sleep 10 && echo \"Now touching GHI\" && touch GHI' localhost
ssh-proc-mux > launch 'echo \"Hello World JKL\" && sleep 10 && echo \"Now touching JKL\" && touch JKL' localhost
ssh-proc-mux > launch 'echo \"Hello World MNO\" && sleep 10 && echo \"Now touching MNO\" && touch MNO' localhost
ssh-proc-mux > launch '{ echo \"Hello World MNO\" && sleep 10 && echo \"Now touching MNO\"; } &> MNO' localhost
```
Hopefully, you now have 5 files in your current directory, named ABC, DEF, GHI, JKL and MNO, and MNO contains the output of the command. You should also see the stdout of the commands, they start with `ssh_stdout.localhost:`.

Always useful to check the processes:
```bash
ssh-proc-mux > ps
```

To kill all the processes on a host:
```bash
ssh-proc-mux > killall localhost
```

To kill a specific process on a host:
```bash
ssh-proc-mux > kill 123 localhost
```

To disconnect from a host (and kill all the processes on it):
```bash
ssh-proc-mux > disconnect localhost
```

This program has a `stdout` asynchronous with the prompt, so you may need to hit enter to get back to the prompt.

And finally a word of caution, this program is _experimental_...

## Description

This tool uses a python launcher `launcher.py` to start subprocesses on the remote host. `ssh_proc_mux.py` just waits for the python prompt in `launcher.py` to start and then stdin command to it. The upshot is that there isn't any socket opened by `launcher.py`, so it can be run on a remote host without any firewall rules.

## Known issues
- On Mac, the launcher process cannot be tied to the `ssh_proc_mux` process. This means if you `SIGQUIT` the `ssh_proc_mux` process, the launcher process will not be killed. That shouldn't be the case on Linux.
