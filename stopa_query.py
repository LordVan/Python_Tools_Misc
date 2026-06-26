from s7 import Client

client = Client()
client.connect("192.168.0.33", rack=0, slot=1)

# Read 4 bytes from Data Block 10, starting at offset 0
data = client.db_read(db_number=10, start=0, size=4)

client.disconnect()
