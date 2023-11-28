import os
import time

class FileChecker:
    def __init__(self, timeout=10, wait_interval=1):
        self.timeout = timeout
        self.wait_interval = wait_interval

    def wait_for_file_creation(self, file_path):
        elapsed_time = 0
        while elapsed_time < self.timeout:
            if os.path.exists(file_path):
                print(f"File found: {file_path}")
                return True
            else:
                print(f"Waiting for file: {file_path}")
                time.sleep(self.wait_interval)
                elapsed_time += self.wait_interval

        print(f"Timeout reached, file not found: {file_path}")
        return False