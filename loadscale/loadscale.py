from settings import settings as settings
import time
import pyrax
import datetime as dt


# authenticate the user
pyrax.set_credential_file(settings["RACK_CRED_FILE"])

# shorten the variables - make shortcuts
clb = pyrax.cloud_loadbalancers
cs = pyrax.cloudservers
au = pyrax.autoscale

# name of adding on server policy:
ADD_ON_POLICY = settings["ADD_ON_POLICY"]
SUB_OFF_POLICY = settings["SUB_OFF_POLICY"]

# set max number of mconnections per server. If goes up, then add in a new
# server
MAX_CONN = settings["MAX_CONN"]
# set min number of connections per server. If goes below, then kill a server
MIN_CONN = settings["MIN_CONN"]

# load balancer name
LOAD_BAL_NAME = settings["LOAD_BAL_NAME"]

# autoscaling Group name
AUTO_SCALE_NAME = settings["AUTO_SCALE_NAME"]


########## GETTERS #######
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
    Returns the autoscaling group based on the name that is in the settings
    """
    for sg in au.list():
        if AUTO_SCALE_NAME == sg.name:
            return sg
    raise Exception("auto scaling group was not found")


def get_total_connections(load_bal):
    """
    Returns the number of connections the load balancer has
    The number of connections is cached every 5 minutes in the load balancer
    """
    currentConn = load_bal.manager.get_stats(load_bal.id)['currentConn']
    currentConnSsl = load_bal.manager.get_stats(load_bal.id)['currentConnSsl']
    return currentConn + currentConnSsl


def get_total_nodes(load_bal):
    """
    Returns the number of nodes attached to the load balancer.
    Regardless if they are in the scaling group or not.
    """
    return len(load_bal.nodes)


def get_scaling_active_nodes(sg):
    """
    Returns the number of active connections associated with a scaling group
    Note: this() != get_total_connections
    """
    return sg.get_state()["active_capacity"]


def get_scaling_desired_nodes(sg):
    """
    Returns the numb of desired nodes the scaling group will have in the future
    """
    return sg.get_state()["desired_capacity"]


########## LOGIC ##########
def out_of_range(totalConn, totalNodes):
    """
    Checks if the total number of connections is out of range.
    Returns:
    - False --> is in range
    - "scale_up" --> need to execute scale up policy
    - "scale_down" --> need to execute scale down policy
    """
    if (totalConn + 0.0) / totalNodes > MAX_CONN:
        return "scale_up"
    elif (totalConn + 0.0) / totalNodes < MIN_CONN:
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
    except Exception, e:
        print e
        print "can't carry out policy: ", pol.name, " - probably hit min/max"
        return False


def scaling(load_bal, sg):
    """
    Based on parameters, checks if the group needs to scale
    Returns:
    False -- if it did not execute a policy
    True -- if it did execuete a policy
    """
    totalConn = get_total_connections(load_bal)
    print "TOTAL CONNECTIONS - ", totalConn

    totalNodes = get_total_nodes(load_bal)
    print "Current number of nodes: ", totalNodes

    scaling = out_of_range(totalConn, totalNodes)

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
            print "No need to scale right now b/c create/delete in progress"
            return False


def run():
    """
    Main execuetor of the script.

    In general, flow of this script goes upward.
    (i.e. run()->scaling()->execute_policy()).
    """
    prev_execute_time = dt.datetime.now()
    execuetion_locked = False
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
        # load balancer api cache gets updated every 5 minutes so just let this
        # sleep
        time.sleep(5 * 60)
        print "Checking the load...."

        # take into account what the cooldown and the prev. policy execuetion
        next_exec_time = (prev_execute_time+dt.timedelta(seconds=cooldown))
        execuetion_locked = next_exec_time > (dt.datetime.now())
        if execuetion_locked:
            print "Until cooldown: ", next_exec_time - dt.datetime.now()


if __name__ == "__main__":
    run()
