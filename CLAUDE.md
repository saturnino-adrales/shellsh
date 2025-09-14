# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python shell server project (`shellsh.py`) that provides a programmatic interface for interacting with persistent shell processes. The prototype demonstrates a design for managing long-running shell sessions programmatically, allowing commands to be executed and their output retrieved incrementally without blocking.

### Purpose

The `ShellSh` class aims to solve the problem of programmatically interacting with shell processes in a non-blocking manner, particularly useful for:
- Running multiple commands in the same shell session (maintaining state, environment variables, working directory)
- Capturing output from long-running or interactive programs (like `top`, `htop`, or log tails)
- Building shell automation tools that need real-time output streaming
- Creating programmatic interfaces to command-line tools that expect interactive input
- **Non-blocking execution**: Both `typeenter()` and `flush()` return immediately, allowing the caller to continue other work while commands execute

## Development Environment

- **Python Version**: 3.12.3
- **Virtual Environment**: Located in `venv/` directory
- **Activation**: Use `source activate` (symlinked to `venv/bin/activate`)

## Key Components

### ShellSh Class (`shellsh.py`)
The main class that manages persistent shell sessions with the following interface:
- `__init__(name)`: Initialize a named shell session
- `typeenter(line)`: Send a command to the shell - **returns immediately** without waiting for execution (or blocks if `setblocking(True)` was called)
- `flush()`: Retrieve new output since last flush (stateful, returns only unread output) - **non-blocking**
- `setblocking(blocking)`: Set blocking mode - if `True`, `typeenter()` waits for command completion; if `False` (default), returns immediately
- `stop()`: Send Ctrl+C to interrupt the currently running command

## Implementation Plan

### 1. Core Shell Process Management
```python
import subprocess
import threading
import queue
import os
import pty
import select

class ShellSh:
    def __init__(self, name):
        self.name = name
        self.output_buffer = []
        self.unread_position = 0
        # Use pty for proper terminal emulation (handles interactive programs)
        self.master, self.slave = pty.openpty()
        self.process = subprocess.Popen(
            ['/bin/bash'],
            stdin=self.slave,
            stdout=self.slave,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
            env=os.environ.copy()
        )
        # Start background thread for reading output
        self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
        self.reader_thread.start()
```

### 2. Non-blocking Output Reading
- Implement background thread that continuously reads from the shell process
- Use a queue or buffer to store output between flushes
- Handle both line-buffered and unbuffered output (for interactive programs)
- The reader thread runs independently, collecting output while the main thread remains free

### 3. Command Execution (`typeenter`)
**Critical**: This method must be non-blocking and return immediately, even if the command takes time to execute.
```python
def typeenter(self, line):
    # Write to master fd - this is non-blocking by design
    # The command executes in the shell process, not in this thread
    os.write(self.master, (line + '\n').encode())
    # Returns immediately - does NOT wait for command to complete
```

### 4. Incremental Output Retrieval (`flush`)
```python
def flush(self):
    # Return only new output since last flush
    new_output = self.output_buffer[self.unread_position:]
    self.unread_position = len(self.output_buffer)
    return ''.join(new_output)
```

### 5. Additional Considerations
- **Terminal Control**: Use `pty` module for proper terminal emulation
- **Signal Handling**: Implement proper cleanup on exit
- **Error Handling**: Handle process termination, broken pipes
- **Interactive Programs**: Support for programs using curses/ncurses
- **Thread Safety**: Use locks for buffer access if needed
- **Resource Management**: Implement `__enter__`/`__exit__` for context manager support

## Common Development Tasks

```bash
# Activate virtual environment
source activate

# Run the shell server
python shellsh.py
```

## Testing Strategy

1. Test basic command execution (`ls`, `echo`)
2. Test environment persistence (cd, export)
3. Test long-running commands (`sleep`, `watch`)
4. Test interactive programs (`top`, `vim`)
5. Test output buffering with large outputs
6. Test concurrent command execution edge cases