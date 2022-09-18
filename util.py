import os

def fixcwd():
    """ Set current working directory to script path"""
    os.chdir(os.path.dirname(__file__))
