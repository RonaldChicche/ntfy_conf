# import opce ua
from opcua import Client, ua

# create a client
client = Client("opc.tcp://ronald_desk:62640/IntegrationObjects/ServerSimulator")

# connect to the server
client.connect()

# define node id
node_id = "ns=2;s=Tag10"

# read node value
node = client.get_node(node_id)
value = node.get_value()

# print value
print(value)

# disconnect from the server
client.disconnect()