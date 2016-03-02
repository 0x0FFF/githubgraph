import sys
import os

def execute_os(command):
    out = ''
    err = ''
    ret = 0
    try:
        pid = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        (out, err) = pid.communicate()
        ret = pid.returncode
    except:
        logger.error('Exception ' + str(sys.exc_info()[1]))
        sys.exit(3)
    return (ret, out, err)

git clone %f
