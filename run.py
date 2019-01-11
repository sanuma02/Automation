import re

class Neighbor: 
	def __init__(self, port, address):
		self.port = port
		self.address = address

	def pretty_print(self):
		print(f"Port: {self.port}, Address {self.address}")

def user_input():
	while(True):
		print("Choose to parse:")
		print("1. Parse OSPF File")
		print("2. Parse Spanning Tree File")
		print("3. Parse Version File")
		option = input()
		if option in ["1","2","3"]:
			read_option(option)
			break
		else:
			print ("Wrong option, try again!")

def read_option(option):
	if option == '1':
		parse_ospf()
	elif option == '2':
		parse_spanning()
	else:
		parse_version()

def parse_ospf():
	ospf_neighbor_patter = re.compile(r"(v\d{2})(\s*)(\b(?:\d{1,3}\.){3}\d{1,3}\b)")
	ospf_file = open("show_ip_ospf_neighbor.txt", "r")
	ospf_output = ospf_file.read()
	ospf_file.close()
	matches = re.findall(ospf_neighbor_patter, ospf_output)
	neighbors = [Neighbor(x[0],x[2]) for x in matches]
	for neighbor in neighbors:
		neighbor.pretty_print()

def parse_spanning():
	root_patter = re.compile(r"(Root ID).+?(\n)(.*\n)")
	bridge_patter = re.compile(r"(Bridge ID).+?(\n)(.*\n)")
	spanning_file = open("show_spanning-tree.txt","r")
	spanning_output = spanning_file.read()
	spanning_file.close()
	root = re.search(root_patter, spanning_output)
	bridge = re.search(bridge_patter, spanning_output)
	if bridge and root:
		if bridge.group(3) == root.group(3):
			print("This SW is the Root :)")
		else:
			print(f"This Sw is not the root, the root is {root.group(3)}")

def parse_version():
	model_dummy_patter = re.compile(r"(Model number:)(\s*)(.*)")
	version_file = open("show_version.txt","r")
	version_output = version_file.read()
	version_file.close()
	model = re.search(model_dummy_patter, version_output)
	if model:
		print(f"The model fo the device is {model.group(3)}")
	else:
		print("we could not find the model, we may need a better regex!")

user_input()