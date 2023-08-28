name = "cueNimby"

version = "0.1.0"

description = "User managed availability scheduler for OpenCue"

authors = ["Kern Attila Germain"]

requires = ["PySide2"]

cachable = True

def commands():
    env.PYTHONPATH.append("{root}")
