import subprocess
import threading
import os
import pty
import select
import time
from collections import deque

class ShellSh:
    def __init__(self, name):
        self.name = name
        self.output_buffer = deque()
        self.buffer_lock = threading.Lock()
        self.running = True
        self.blocking = False  # Default to non-blocking mode
        self.last_output_time = time.time()  # Track when we last received output

        # Create pseudo-terminal for proper terminal emulation
        self.master, self.slave = pty.openpty()

        # Start bash process
        self.process = subprocess.Popen(
            ['/bin/bash'],
            stdin=self.slave,
            stdout=self.slave,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
            env=os.environ.copy()
        )

        # Close slave fd in parent process
        os.close(self.slave)

        # Start background thread for reading output
        self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
        self.reader_thread.start()

    def _read_output(self):
        """Background thread that continuously reads output from the shell"""
        while self.running:
            try:
                # Check if there's data to read (with timeout to allow thread termination)
                readable, _, _ = select.select([self.master], [], [], 0.1)
                if readable:
                    data = os.read(self.master, 4096)
                    if data:
                        with self.buffer_lock:
                            self.output_buffer.append(data.decode('utf-8', errors='replace'))
                            self.last_output_time = time.time()  # Update last output time
            except OSError:
                # Process has terminated or pipe is broken
                break

    def typeenter(self, line):
        """Send a command to the shell - blocks if setblocking(True) was called"""
        if not self.running:
            raise RuntimeError("Shell process has terminated")

        # Write command to master fd
        os.write(self.master, (line + '\n').encode())

        # If in blocking mode, wait for command to complete
        if self.blocking:
            # Wait until no new output for a certain period (indicating command completion)
            timeout = 300  # 5 minute timeout for long-running commands
            idle_threshold = 0.5  # Consider command done after 0.5 seconds of no output
            start_time = time.time()

            # Give initial time for command to start producing output
            time.sleep(0.1)

            while (time.time() - start_time) < timeout:
                with self.buffer_lock:
                    time_since_output = time.time() - self.last_output_time

                # If no output for idle_threshold seconds, assume command is done
                if time_since_output > idle_threshold:
                    break

                time.sleep(0.05)  # Small sleep to avoid busy waiting
        # Otherwise returns immediately

    def flush(self):
        """Retrieve new output since last flush - non-blocking"""
        with self.buffer_lock:
            if not self.output_buffer:
                return ""

            # Get all accumulated output and clear the buffer
            output = ''.join(self.output_buffer)
            self.output_buffer.clear()
            return output

    def setblocking(self, blocking):
        """Set blocking mode for typeenter() method

        Args:
            blocking (bool): If True, typeenter() will wait for command completion.
                           If False, typeenter() returns immediately (default).
        """
        self.blocking = blocking

    def stop(self):
        """Kill the currently running command (send Ctrl+C)"""
        if not self.running:
            raise RuntimeError("Shell process has terminated")

        # Send Ctrl+C (SIGINT) to the process group
        os.write(self.master, b'\x03')  # Ctrl+C character

    def close(self):
        """Clean up resources"""
        self.running = False
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        os.close(self.master)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Usage example
if __name__ == "__main__":
    print("=== Non-blocking mode (default) ===")
    sh = ShellSh("demo")

    # Execute ls command (non-blocking)
    sh.typeenter("ls")
    time.sleep(0.5)  # Give it a moment to execute
    print("ls output:")
    print(sh.flush())

    # Execute a command with delayed output (non-blocking)
    sh.typeenter("echo 'Starting...'; sleep 2; echo 'Done!'")
    print("Immediate return from typeenter()")
    time.sleep(3)
    print("After waiting 3 seconds:")
    print(sh.flush())

    print("\n=== Blocking mode ===")
    sh.setblocking(True)

    # This will block until command completes
    print("Running 'sleep 1; echo Done' in blocking mode...")
    start = time.time()
    sh.typeenter("sleep 1; echo 'Done from blocking'")
    elapsed = time.time() - start
    print(f"typeenter() returned after {elapsed:.2f} seconds")
    print("Output:", sh.flush())

    # Switch back to non-blocking
    print("\n=== Back to non-blocking mode ===")
    sh.setblocking(False)
    sh.typeenter("echo 'Non-blocking again'")
    time.sleep(0.5)
    print(sh.flush())

    # Clean up
    sh.close()

