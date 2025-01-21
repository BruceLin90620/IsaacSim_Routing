from Vector import Vector3,calculateDistance
class Node:
    def __init__(self,id:str="DEFAULT_NODE",locallocation:Vector3=Vector3(),mapid:str="DEFAULT_MAP",edges:list[str]=[],isentrypoint:bool=False,entrytonodeid:str="DEFAULT_ENTRY_TO_NODE"):
        self.id=id
        self.edges=edges
        self.localLocation=locallocation
        self.mapId=mapid
        self.isEntryPoint=isentrypoint
        self.entryToNodeId=entrytonodeid
    
    def setEntryPointById(self,nodeid:str):
        self.isEntryPoint=True
        self.entryToNodeId=nodeid


def generateNodeId(mapindex,nodeindex):
    nodeId = "{:03}".format(mapindex) + "_" + "{:03}".format(nodeindex)
    return nodeId

def convertToNodeId(mapid:any,nodeindex:any)->str:
    mapname,mapindex=mapid.split("_")
    if(type(nodeindex)==str):
        nodeindex=int(nodeindex)
    if(type(mapindex)==str):
        mapindex=int(mapindex)
    nodeId="{:03}".format(mapindex)+"_"+"{:03}".format(nodeindex)
    return nodeId

def getMapIdByNodeId(nodeid):
    mapid,_=nodeid.split("_")
    return mapid

def convertJSONnodeToNode(id,nodedata):
    x=float(nodedata["local_location"][0])
    y=float(nodedata["local_location"][1])
    z=float(nodedata["local_location"][2])
    location=Vector3(x,y,z)
    mapId=getMapIdByNodeId(id)
    return Node(id,location,mapId,nodedata["edges"])

def calculateDistanceBetweenNodes(node1:Node,node2:Node):
    return calculateDistance(node1.localLocation,node2.localLocation)

def connectTwoNodes(node1:Node,node2:Node):
    if(len(node1.edges)==0):
        node1.edges=[node2.id]
    else:
        node1.edges.append(node2.id)

    if (len(node2.edges) == 0):
        node2.edges = [node1.id]
    else:
        node2.edges.append(node1.id)

    #return node1,node2