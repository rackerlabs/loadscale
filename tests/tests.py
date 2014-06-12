import unittest
import mock
from loadscale import loadscale as ls
from loadscale.settings import settings
import pyrax


class testGetters(unittest.TestCase):

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

		# some unknown policy:
		self.pol = FakePolicy("raiseError", "raise error policy")

	@patch("ls.LOAD_BAL_NAME", 'sdkcjnscskcksncksd') 
	def testLoadBal(self):
		self.assertRaises(ls.get_load_bal(self.clb))


	@patch("ls.AUTO_SCALE_NAME", 'sdkcbskcsknsksknksd')
	def testScaleGroup(self):
		self.assertRaises(ls.get_au_scale_group(self.au))

	def testCurrentConnections(self):
		try:
			ls.get_total_connections(self.load_bal)
		except:
			print "the user must create a load balancer for this to work"

	def testNodesPerGroup(self):
		act_nodes = ls.get_scaling_active_nodes(self.au.list()[0])
		des_nodes = ls.get_scaling_desired_nodes(self.au.list()[0])	

		self.assertTrue(act_nodes >= 0)
		self.assertTrue(des_nodes >= 0)

	@patch("ls.MAX_CONN", self.MAX_CONN)
	@patch("ls.MIN_CONN", self.MIN_CONN)
	def testShouldScale(self):
		# need to spin more servers up
		self.assertEquals(ls.out_of_range(60, 1), "scale_up")

		# need to destroy some servers
		self.assertEquals(ls.out_of_range(5, 1), "scale_down")

		#no need to scale
		self.assertFalse(ls.out_of_range(30, 1))

	def testExecutePolicy(self):
		# execute a faulty policy
		self.assertFalse(ls.execute_policy(self.pol))
		
		# execute a regular policy
		self.pol.type = "execute_normally"
		self.pol.name = "execute normally policy"
		self.assertTrue(ls.execute_policy(self.pol))

	def testScalingLogic(self):
		# TODO - have to create fake load balancer and scaling group



class FakePolicy():
	def __init__(type_of_policy, name):
		self.type = type_of_policy
		self.name = name

	def execute():
		if self.type == "raiseError":
			raise Exception("FakeException")
		else:
			pass