# ShellSh

A Python library for managing persistent shell sessions programmatically with non-blocking I/O.

## Features

- **Non-blocking command execution** - Commands return immediately without waiting for completion
- **Command status tracking** - Check if commands are still running with `is_alive()`
- **Flexible waiting** - Wait for command completion with optional timeouts using `wait()`
- **Persistent shell sessions** - Maintain environment variables, working directory, and state between commands
- **Real-time output streaming** - Capture output from long-running processes incrementally
- **Interactive program support** - Works with curses-based programs like `top`, `vim`, etc.
- **Process control** - Stop running commands with Ctrl+C programmatically

## Installation

```bash
pip install shellsh
```

## Quick Start

```python
from shellsh import ShellSh
import time

# Create a shell session
sh = ShellSh("my_session")

# Non-blocking mode (default)
sh.typeenter("ls -la")
time.sleep(0.5)
print(sh.flush())  # Get the output

# Wait for command completion
sh.typeenter("echo 'Processing...'; sleep 2; echo 'Done'")
sh.wait()  # Blocks until command finishes
print(sh.flush())

# Check if command is running
sh.typeenter("sleep 5")
print(sh.is_alive())  # True - command is running
sh.wait(2)  # Wait 2 seconds
print(sh.is_alive())  # True - still running after timeout
sh.stop()  # Stop the command

# Blocking mode - waits for command completion
sh.setblocking(True)
sh.typeenter("sleep 2; echo 'Done'")  # This will block for ~2 seconds
print(sh.flush())  # Output is ready immediately after typeenter returns

# Back to non-blocking
sh.setblocking(False)
sh.typeenter("echo 'Non-blocking'")
time.sleep(0.1)
print(sh.flush())

# Environment persists between commands
sh.typeenter("cd /tmp")
sh.typeenter("pwd")
sh.wait()
print(sh.flush())  # Prints: /tmp

# Stop long-running commands
sh.typeenter("sleep 100")
time.sleep(1)
sh.stop()  # Sends Ctrl+C

# Clean up
sh.close()
```

## API Reference

### `ShellSh(name)`
Create a new shell session with the given name.

### `typeenter(line)`
Send a command to the shell. By default, returns immediately without waiting for execution. If `setblocking(True)` was called, blocks until the command completes.

### `flush()`
Retrieve new output since the last flush. Returns only unread output.

### `wait(seconds=None)`
Block until the current command completes or timeout is reached.
- `seconds=None`: Wait indefinitely until command completes (default)
- `seconds=float`: Maximum time to wait in seconds before returning
- Note: Timeout does not kill the command, it just stops waiting

### `is_alive()`
Check if a command is currently running.
- Returns `True` if a command is still executing
- Returns `False` if the last command has completed or no command was run

### `setblocking(blocking)`
Set blocking mode for `typeenter()`.
- `blocking=True`: `typeenter()` waits for command completion before returning
- `blocking=False`: `typeenter()` returns immediately (default)

### `stop()`
Send Ctrl+C to stop the currently running command.

### `close()`
Terminate the shell session and clean up resources.

## Context Manager

ShellSh supports context manager protocol:

```python
with ShellSh("session") as sh:
    sh.typeenter("echo Hello")
    time.sleep(0.5)
    print(sh.flush())
# Automatically closed
```

## Use Cases

- Automating shell interactions
- Building terminal-based tools
- Testing command-line applications
- Managing long-running processes
- Creating interactive shell wrappers

## Requirements

- Python 3.7+
- Unix-like operating system (Linux, macOS)

## License

MIT