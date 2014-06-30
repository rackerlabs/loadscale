import unittest
import mock
from mock import patch
from loadscale import loadscale as ls
ls = ls.loadscale
settings = ls.settings
import pyrax


class test_Everything(unittest.TestCase):

	def setUp(self):
		"""
		Method called when the test case gets built
		""" 
		self.MIN_CONN = 10
		self.MAX_CONN = 50

		self.curr_nodes = 3
		pyrax.set_credential_file(settings["RACK_CRED_FILE"])

		# shorten the variables - make shortcuts
		self.clb = pyrax.cloud_loadbalancers
		self.cs = pyrax.cloudservers
		self.au = pyrax.autoscale

		# get current load balancer
		self.load_bal = self.clb.list()[0]

		self.list_policies = [FakePolicy("sub_off", "sub_off"), FakePolicy("add_on","add_on")]
		self.load_bal_fake = FakeLoadBalancer(9, 1)
		self.sg = FakeAutoGroup(2, 0, self.list_policies)

		# some unknown policy:
		self.pol = FakePolicy("raiseError", "raise error policy")


	def test_LoadBal(self):
		ls.LOAD_BAL_NAME = 'sdkcjnscskcksncksd'
		with self.assertRaises(Exception):
			ls.get_load_bal(self.clb)


	def test_ScaleGroup(self):
		ls.AUTO_SCALE_NAME = 'sdkcbskcsknsksknksd'
		with self.assertRaises(Exception):
			ls.get_au_scale_group(self.au)

	def test_CurrentConnections(self):
		try:
			ls.get_total_connections(self.load_bal)
		except:
			print "the user must create a load balancer for this to work"

	def testNodesPerGroup(self):
		act_nodes = ls.get_scaling_active_nodes(self.au.list()[0])
		des_nodes = ls.get_scaling_desired_nodes(self.au.list()[0])	

		self.assertTrue(act_nodes >= 0)
		self.assertTrue(des_nodes >= 0)


	def test_ShouldScale(self):

		ls.MAX_CONN = self.MAX_CONN
		ls.MIN_CONN = self.MIN_CONN

		# need to spin more servers up
		self.assertEquals(ls.out_of_range(60, 1), "scale_up")

		# need to destroy some servers
		self.assertEquals(ls.out_of_range(5, 1), "scale_down")

		#no need to scale
		self.assertFalse(ls.out_of_range(30, 1))

	
	def test_ExecutePolicy(self):
		# execute a faulty policy
		self.assertFalse(ls.execute_policy(self.pol))
		
		# execute a regular policy
		pol_fake = FakePolicy("execute_normally", "execute normally policy")
		self.assertTrue(ls.execute_policy(pol_fake))


	
	def test_ScalingLogic(self):
		"""
		By manipulating values we inject in, we can test the main logic of the script.
		We inject in Fake* (described below) objects and lambdas 
		"""
		# patch in all the values and redefine methods
		ls.MAX_CONN = self.MAX_CONN
		ls.MIN_CONN = self.MIN_CONN
		ls.ADD_ON_POLICY = "add_on"
		ls.SUB_OFF_POLICY = "sub_off"
		ls.execute_policy = lambda pol: pol.name
		ls.get_scaling_active_nodes = lambda sg: sg.get_scaling_active_nodes()
		ls.get_scaling_desired_nodes = lambda sg: sg.get_scaling_desired_nodes()
		ls.get_total_connections = lambda load_bal_fake: self.load_bal_fake.get_total_connections()
		ls.get_total_nodes = lambda load_bal_fake: self.load_bal_fake.get_total_nodes()


		# TODO - have to create fake load balancer and scaling group
		self.list_policies = [FakePolicy("sub_off", "sub_off"), FakePolicy("add_on","add_on")]
		self.load_bal_fake = FakeLoadBalancer(9, 1)
		self.sg = FakeAutoGroup(2, 2, self.list_policies)

		# should return a "sub_off"
		self.assertEquals(ls.scaling(self.load_bal_fake, self.sg), "sub_off")

		# should return a false because we have mismatch in desired vs. active nodes
		self.sg.desired = 1
		self.assertFalse(ls.scaling(self.load_bal_fake, self.sg))


		self.load_bal_fake.totalConn = 70
		self.sg.desired = 2
		# should return "add_on"
		self.assertEquals(ls.scaling(self.load_bal_fake, self.sg), "add_on")

		# in the safe range, should return false
		self.load_bal_fake.totalConn = 30
		self.assertFalse(ls.scaling(self.load_bal_fake, self.sg))



class FakeAutoGroup():

	def __init__(self, active, desired, list_policies):
		self.active = active
		self.desired = desired
		self.list_of_policies = list_policies

	def get_scaling_active_nodes(self):
		return self.active

	def get_scaling_desired_nodes(self):
		return self.desired

	def list_policies(self):
		return self.list_of_policies



class FakeLoadBalancer():

	def __init__(self, totalConn, totalNodes):
		self.totalConn = totalConn
		self.totalNodes = totalNodes

	def get_total_connections(self):
		return self.totalConn

	def get_total_nodes(self):
		return self.totalNodes


class FakePolicy():
	def __init__(self, type_of_policy, name):
		self.type = type_of_policy
		self.name = name

	def execute(self):
		print "fake policy executeing"
		if self.type == "raiseError":
			raise Exception("FakeException")
		else:
			return self.name
