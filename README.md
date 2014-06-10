#AUTOSCALE USING LOADBALANCER AS TRIGGER

##Overall architecture:
Use autoscale(otter) api and load balancer api to know when to scale. API calls mediated through pyrax. 

##Assumptions that I used to build this (Eventually, they might will be taken out as time goes on)
1. Load balancer is rackspace owned
2. only one loadbalancer 
3. all the same type of nodes in scaling group (which it most likely should be already)
4. load balancer algorithm lends itself to be such that it balances itself out across servers.

##Setup:
1. pip install the requirements ->  `pip install -r requirements.txt`
2. open up settings.py and fill in the values that pertain to you
	1. You need to also create a rackspace credential file [The "Rackspace Public Cloud" one](https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md#authenticating). Follow the example.
	2. You need to also create a .pyrax.cfg file [Instructions](https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md#available-configuration-settings). You can look at the example on below the graph
3. To run python script: `python loadscale.py`

##Load Testing:
Configure the locustfile.py included or just the barebones I provided to run [Locust](http://docs.locust.io/en/latest/). 

1. To run `locust -f locust/locustfile.py`
2. Then go to `127.0.0.1:8089`
3. Type in whatever you