#Trigger Autoscale with LoadBalancer

##Overall architecture:
Use autoscale(otter) api and load balancer api to know when to scale. API calls mediated through pyrax. 


##Setup:
1. pip install the requirements:  `pip install -r requirements.txt`
2. open up settings.py and fill in the values that pertain to you
	1. You need to also create a rackspace credential file [The "Rackspace Public Cloud" one](https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md#authenticating). Follow the example.
	2. You need to also create a .pyrax.cfg file [Instructions](https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md#available-configuration-settings). You can look at the example below the graph
3. To run python script: `python loadscale.py`

If import errors arise. Add this repository to your PYTHONPATH. Example: `export PYTHONPATH=$HOME/loadscale:$PYTHONPATH`



##Load Testing (Warning! This will make it work directly with your Rackspace account, incurring costs!):
Configure the locustfile.py included or just the barebones I provided to run [Locust](http://docs.locust.io/en/latest/). 

1. To run `locust -f locust/locustfile.py`
2. Then go to `127.0.0.1:8089`
3. Type in whatever you want for number of users and onboarding speed



##Current Assumptions
1. only one loadbalancer 
2. all the same type of nodes in scaling group (which it most likely should be already)
3. load balancer algorithm lends itself to be such that it balances itself out across servers.