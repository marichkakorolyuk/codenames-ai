import sys

class Tee(object):
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()  # Ensure output appears immediately

    def flush(self):
        for f in self.files:
            f.flush()


def set_stdout_dup_to_file(logfile_name):
    # Open your log file in append or write mode
    logfile = open(logfile_name, 'w')
    sys.stdout = Tee(sys.__stdout__, logfile)
