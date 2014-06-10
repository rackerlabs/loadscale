import time
import pyrax
import datetime as dt
import settings

#authenticate the user
pyrax.set_credential_file(settings.RACK_CRED_FILE)

# shorten the variables - make shortcuts
clb = pyrax.cloud_loadbalancers
cs = pyrax.cloudservers
au = pyrax.autoscale

# name of adding on server policy:
ADD_ON_POLICY = settings.ADD_ON_POLICY
SUB_OFF_POLICY = settings.SUB_OFF_POLICY

# set max number of mconnections per server. If goes up, then add in a new server
MAX_CONN = settings.MAX_CONN
# set min number of connections per server. If goes below, then kill a server
MIN_CONN = settings.MIN_CONN

# load balancer name
LOAD_BAL_NAME = settings.LOAD_BAL_NAME

# autoscaling Group name
AUTO_SCALE_NAME = settings.AUTO_SCALE_NAME


def get_load_bal(clb):
	for load_bal in clb.list():
		if LOAD_BAL_NAME == load_bal.name:
			return load_bal
	raise Exception("load balancer not found")



def get_au_scale_group(au):
	for sg in au.list():
		if AUTO_SCALE_NAME == sg.name:
			return sg
	raise Exception("auto scaling group was not found")



def run(): 
	load_bal = get_load_bal(clb)
	prev_execute_time = dt.datetime.now()
	execuetion_locked = False
	sg = get_au_scale_group(au)
	cooldown = sg.cooldown # in seconds
	while True:
		currentConn =  load_bal.manager.get_stats(load_bal.id)['currentConn']
		currentConnSsl = load_bal.manager.get_stats(load_bal.id)['currentConnSsl']
		totalConn = currentConn + currentConnSsl

		print "TOTAL CONNECTIONS - " , totalConn

		# take into account what the cooldown and the prev. policy execuetion
		execuetion_locked = (prev_execute_time + dt.timedelta(seconds=cooldown)) > (dt.datetime.now())

		if execuetion_locked:
			print "TIME LEFT until cooldown: ", (prev_execute_time + dt.timedelta(seconds=cooldown)) - dt.datetime.now()

		current_number_of_nodes = len(get_load_bal(clb))
		print "Current number of nodes: ", current_number_of_nodes

		au_active_nodes = sg.get_state()["active_capacity"]
		au_desired_nodes = sg.get_state()["desired_capacity"]

		if ((totalConn+0.0)/current_number_of_nodes > MAX_CONN):
			# scale up 
			autoscaler_pols = sg.list_policies()
			for pol in autoscaler_pols:
				if pol.name == ADD_ON_POLICY and not execuetion_locked and (au_desired_nodes == au_active_nodes):
					print "executed policy to add on"
					try:
						pol.execute()
						prev_execute_time = dt.datetime.now()
					except:
						print "can't carry out policy to add on" # because we hit the limit or other reasons
					break

		elif ((totalConn+0.0)/current_number_of_nodes < MIN_CONN):
			# scale down
			autoscaler_pols = sg.list_policies()
			for pol in autoscaler_pols:
				if pol.name == SUB_OFF_POLICY and not execuetion_locked and (au_desired_nodes == au_active_nodes):
					print "execueted policy to subtract off"
					try:
						pol.execute()
						prev_execute_time = dt.datetime.now()
					except:
						print "Can't execute policy subtract off"
					break

		else:
			print "Connections is in a good range"

		print "Process is going to sleep for 5 minutes"
		time.sleep(5*60) # load balancer api cache gets updated every 5 minutes so just let this sleep
		print "Checking the load...."
	


if __name__ == "__main__":
	run()