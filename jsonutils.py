import dbus

# Global variables to manage JSON packets
MAX_PACKET_SIZE = 185  # Max size of BLE packet
json_packets = []
json_index = 0
def load_json_file():
    """Load and split the JSON file."""
    global json_packets, json_index
    json_index = 0

    try:
        with open("json_test.json", "r") as file:
            data = file.read()

        # Slicing in MAX_SIZE packets
        json_packets = [data[i:i + MAX_PACKET_SIZE] for i in range(0, len(data), MAX_PACKET_SIZE)]
        json_packets.append("END")  # Setting the end of a file 
        print(f"Json file loaded in  ({len(json_packets)} packets)")
    except Exception as e:
        print(f"Error while loading the file : {e}")
        json_packets = ["ERR"]  # If error in the file, we sent only ERR

def get_next_json_packet():
    """Send the next paquet and update the global index"""
    global json_index
    if json_index < len(json_packets):
        value = json_packets[json_index]
        json_index += 1
    else:
        value = "END"  # Security : send END if we overflow

    return [dbus.Byte(ord(c)) for c in value]