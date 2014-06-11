from settings import settings

import time
import pyrax
import datetime as dt


#authenticate the user
pyrax.set_credential_file(settings["RACK_CRED_FILE"])

# shorten the variables - make shortcuts
clb = pyrax.cloud_loadbalancers
cs = pyrax.cloudservers
au = pyrax.autoscale

# name of adding on server policy:
ADD_ON_POLICY = settings["ADD_ON_POLICY"]
SUB_OFF_POLICY = settings["SUB_OFF_POLICY"]

# set max number of mconnections per server. If goes up, then add in a new server
MAX_CONN = settings["MAX_CONN"]
# set min number of connections per server. If goes below, then kill a server
MIN_CONN = settings["MIN_CONN"]

# load balancer name
LOAD_BAL_NAME = settings["LOAD_BAL_NAME"]

# autoscaling Group name
AUTO_SCALE_NAME = settings["AUTO_SCALE_NAME"]

###### GETTERS #######

def get_load_bal(clb):
	"""
	Gets the load balancer based on the name set in the settings file
	"""
	for load_bal in clb.list():
		if LOAD_BAL_NAME == load_bal.name:
			return load_bal
	raise Exception("load balancer not found")


def get_au_scale_group(au):
	"""
	Returns the autoscaling group based on the name that is defined in the settings
	"""
	for sg in au.list():
		if AUTO_SCALE_NAME == sg.name:
			return sg
	raise Exception("auto scaling group was not found")


def get_total_connections(load_bal):
	"""
	Given load balancer, this returns the total number of connections the load balancer has cached every 5 minutes
	"""
	currentConn =  load_bal.manager.get_stats(load_bal.id)['currentConn']
	currentConnSsl = load_bal.manager.get_stats(load_bal.id)['currentConnSsl']
	return currentConn + currentConnSsl

def get_total_nodes(load_bal):
	"""
	Returns the number of nodes attached to the load balancer regardless of if they are in the scaling group or not
	"""
	return len(get_load_bal(clb).nodes)

def get_scaling_active_nodes(sg):
	"""
	Returns the number of active connections associated with a scaling group
	Note: this() != get_total_connections
	"""
	return sg.get_state()["active_capacity"]

def get_scaling_desired_nodes(sg):
	"""
	Returns the number of desired nodes the scaling group will want in a short while
	"""
	return sg.get_state()["desired_capacity"]

######## LOGIC ##########

def out_of_range(totalConn, current_number_of_nodes):
	"""
	Checks if the total number of connections is out of range. 
	Returns: 
	- False --> is in range
	- "scale_up" --> need to execute scale up policy 
	- "scale_down" --> need to execute scale down policy
	"""
	if (totalConn+0.0)/current_number_of_nodes > MAX_CONN:
		return "scale_up"
	elif (totalConn+0.0)/current_number_of_nodes < MIN_CONN:
		return "scale_down"
	else:
		return False


def execute_policy(pol):
	"""
	Executes a given policy. 
	Returns:
	True - if executed correctly
	False - if there was an error
	"""
	try:
		pol.execute()
		print "Policy <", pol.name, "> has been execueted"
		return True
	except:
		print "can't carry out policy: ", pol.name 
		return False


def scaling(load_bal, sg):
	"""
	Based on parameters, checks if the group needs to scale
	Returns:
	False -- if it did not execute a policy
	True -- if it did execuete a policy
	"""
	totalConn = get_total_connections(load_bal)
	print "TOTAL CONNECTIONS - " , totalConn

	current_number_of_nodes = get_total_nodes(load_bal)
	print "Current number of nodes: ", current_number_of_nodes

	scaling = out_of_range(totalConn, current_number_of_nodes)

	if not scaling:
		print "In range of connections -- no need to scale right now"
		return False
	else:
		au_active_nodes = get_scaling_active_nodes(sg)
		au_desired_nodes = get_scaling_desired_nodes(sg)
		if au_active_nodes == au_desired_nodes:
			for pol in sg.list_policies():
				if scaling == "scale_up" and pol.name == ADD_ON_POLICY:
					# execute scale up policy	
					return execute_policy(pol)
				elif scaling == "scale_down" and pol.name == SUB_OFF_POLICY:
					# execute scale down policy
					return execute_policy(pol)
			print "Error in finding the policies to execute"
			return False
		else:
			print "There are stil changes in the nodes to be made. No need to scale right now because creation/deletion still in process"
			return False


def run(): 
	prev_execute_time = dt.datetime.now()
	execuetion_locked = True
	 # in seconds
	while True:
		
		load_bal = get_load_bal(clb)
		sg = get_au_scale_group(au)
		cooldown = sg.cooldown

		if not execuetion_locked:
			it_scaled = scaling(load_bal, sg)
			if it_scaled:
				# update the previous time it scaled 
				prev_execute_time = dt.datetime.now()
		else:
			print "Cooldown not yet done"


		print "Process is going to sleep for 5 minutes"
		time.sleep(5*60) # load balancer api cache gets updated every 5 minutes so just let this sleep
		print "Checking the load...."

		# take into account what the cooldown and the prev. policy execuetion
		execuetion_locked = (prev_execute_time + dt.timedelta(seconds=cooldown)) > (dt.datetime.now())
		if execuetion_locked:
			print "TIME LEFT until cooldown: ", (prev_execute_time + dt.timedelta(seconds=cooldown)) - dt.datetime.now()

	


if __name__ == "__main__":
	run()