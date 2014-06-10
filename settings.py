# SETTINGS.py PAGE:


# Maximum and minimum number of connections wanted per server (ex: 3 servers, and 90 connections = 30 per server)
# If outside range, scale up or down appropriately
MAX_CONN = 50
MIN_CONN = 40

# Name of the scaling up and scaling down policies (only support 1 of each right now)
ADD_ON_POLICY = "add_on"
SUB_OFF_POLICY = "remove_1"

# name of rackspace cred. file with path:
from os.path import expanduser
home_dir = expanduser("~")
RACK_CRED_FILE = home_dir+"/.rackspace_cred"

# name of load balancer (only support one right now)
LOAD_BAL_NAME = "load_balancer"

# auto scale name
AUTO_SCALE_NAME = "Group01"


# LOAD BALANCER IP ADDRESS