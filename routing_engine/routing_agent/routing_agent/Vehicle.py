from WaypointGraph import WaypointGraph
class Vehicle:
    def __init__(self,locationnode,capcity=1):
        self.locationNode=locationnode
        self.capacity=capcity

def loadVehiclesData(waypointGraph:WaypointGraph,vehicledata):
    vehicleSize=len(vehicledata["vehicle_locations"])
    fleet=[]
    for i in range(vehicleSize):
        node=waypointGraph.getNodeById(vehicledata["vehicle_locations"][i])
        capacity=vehicledata["vehicle_locations"][i]
        fleet.append(Vehicle(node,capacity))
    return fleet
