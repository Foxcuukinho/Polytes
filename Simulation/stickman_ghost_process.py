import os
import sys
import time


def set_process_title(title):
    # Optional: continue if setproctitle is not available.
    try:
        import setproctitle
        setproctitle.setproctitle(title)
    except Exception:
        pass


def wait_for_parent_windows(parent_pid):
    # Open a handle to the parent process and wait for it to exit (without
    # using CPU or polling). Keeping the handle also prevents confusing the
    # parent with another process that reuses the same PID.
    import ctypes
    from ctypes import wintypes

    SYNCHRONIZE = 0x00100000
    INFINITE = 0xFFFFFFFF

    kernel32 = ctypes.windll.kernel32

    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE

    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD

    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    handle = kernel32.OpenProcess(SYNCHRONIZE, False, parent_pid)

    # No handle means the parent no longer exists.
    if not handle:
        return

    try:
        kernel32.WaitForSingleObject(handle, INFINITE)
    finally:
        kernel32.CloseHandle(handle)


def wait_for_parent_linux(parent_pid):
    # Signal 0 does not kill anything: it only checks if the PID exists.
    while True:
        try:
            os.kill(parent_pid, 0)
        except ProcessLookupError:
            return
        except PermissionError:
            pass  # The process exists, we just cannot signal it.
        time.sleep(1)


def main():
    set_process_title(sys.argv[1])

    parent_pid = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if parent_pid is None:
        # Without a parent PID, preserve the old behavior (run indefinitely).
        while True:
            time.sleep(1)

    if sys.platform == "win32":
        wait_for_parent_windows(parent_pid)
    else:
        wait_for_parent_linux(parent_pid)

    # Reaching this point means the parent has exited; this process terminates.


if __name__ == "__main__":
    main()