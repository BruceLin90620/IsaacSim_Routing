from Vector import Vector3
from Node import Node,convertToNodeId,convertJSONnodeToNode,calculateDistanceBetweenNodes,generateNodeId,connectTwoNodes
import ConvertDataFormat
from ConvertDataFormat import loadJSONFile,saveJSONAt,loadYAMLFile
from pathlib import Path
import FindPath
import PreprocessToolkit
class WaypointGraph:
    graph={}
    def __init__(self,nodeid:list[str]=[],nodes:list[Node]=[]):
        #load files and convert it into 
        for index,id in enumerate(nodeid):
            self.addNode(nodes[index])

    def getNodeLocalLocationById(self,id):
        return self.graph[id].localLocation

    def getNodeById(self,id)->Node:
        return self.graph[id]

    def addNode(self,node):
        self.graph[node.id]=node

    def setEntryPoints(self,fromId,toId):
        fromNode=self.getNodeById(fromId)
        toNode=self.getNodeById(toId)
        if(fromNode.entryToNodeId!=toId):
            fromNode.setEntryPointById(toId)
        if(toNode.entryToNodeId!=fromId):
            toNode.setEntryPointById(fromId)

    
    def convertToDistanceMatrix(self):
        nodeIdIndex,graph=self.convertToDijGraph()
        #print(graph)
        costmatrix,pathmatrix=FindPath.findAllShortestPath(graph)
        #print(pathmatrix)
        return nodeIdIndex,costmatrix

    def convertToDijGraph(self):
        nodeIdIndex,offsets,edges,weights=self.__convertToCSR()
        dijGraph=self.__convertFromCSRToDijGraph(nodeIdIndex,offsets,edges,weights)
        return nodeIdIndex,dijGraph
    

    def convertToJSON(self):
        jsondata={}
        for nodeid,node in self.graph.items():
            jsondata[nodeid]={
                "edges":node.edges,
                "local_location":node.localLocation.toList()
            }
            if(node.isEntryPoint and node.entryToNodeId not in jsondata[nodeid]["edges"]):
                #noramally convert to CSR should add entry point to edges
                jsondata[nodeid]["edges"].append(node.entryToNodeId)

        return jsondata


    def __calculateDistanceOfEdges(self,fromnode):
        edges=fromnode.edges
        weights=[]
        for toNodeid in edges:
            toNode=self.getNodeById(toNodeid)
            weights.append(calculateDistanceBetweenNodes(fromnode,toNode))
        
        return weights

    def __convertToCSR(self):
        nodeIdIndex=list(self.graph.keys())
        offsets=[]
        edges=[]
        weights=[]
        for _,thisNode in self.graph.items():
            offsets.append(len(edges))
            edges+=thisNode.edges
            weights+=self.__calculateDistanceOfEdges(thisNode)
            #connect entry points
            if thisNode.isEntryPoint:
                edges.append(thisNode.entryToNodeId)
                weights.append(0)
        return nodeIdIndex,offsets,edges,weights

    def __convertFromCSRToDijGraph(self,nodeIdIndex,offsets,edges,weights):
        graph = {}
        for offsetindex in range(len(offsets)-1):
            startnode=offsetindex
            targetsAtThisIndex,weightsAtThisIndex=self.__getTargetsAndWeightsByIndex(offsetindex,offsets,edges,weights)

            if (startnode not in graph):
                graph[startnode] = {}
            for i in range(len(targetsAtThisIndex)):

                targetnode=nodeIdIndex.index(targetsAtThisIndex[i])
                weight=weightsAtThisIndex[i]

                if (targetnode not in graph):
                    graph[targetnode] = {}

                if (weight == float("inf")):
                    continue
                elif (weight < 0):
                    weight = abs(float(weight))
                
                graph[startnode][targetnode] = float(weight)

                # connect both ways of nodes
                if not(startnode in graph[targetnode]):
                    graph[targetnode][startnode] = float(weight)
                elif(graph[targetnode][startnode]>weight):
                         graph[targetnode][startnode] = float(weight)
        return graph
    
    def __getTargetsAndWeightsByIndex(self,offsetindex,offsets,edges,weights):
        valueindexto=self.__calculateOffsetRange(offsetindex, offsets)
        valueindexfrom=offsets[offsetindex]
        targets=edges[valueindexfrom:valueindexto]
        weights=weights[valueindexfrom:valueindexto]
        return targets,weights

    def __calculateOffsetRange(self,offsetindex,offsets):
        offsetrange=0
        if(offsetindex==len(offsets)-1):
            offsetrange=len(offsets)
        else:
            offsetrange=offsets[offsetindex+1]
        return offsetrange
    

def mergeWaypointGraph(value)->WaypointGraph:
    allmaps=value["merged_file_data"]
    meredGraph=WaypointGraph()
    for mapid,value in allmaps.items():
        map=value["file_data"]
        graph=map["graph"]
        nodeLocations=map["node_locations"]
        #setup all nodes
        for nodeindex,nodeValue in graph.items():
            nodeid=convertToNodeId(mapid,int(nodeindex))
            x=float(nodeLocations[int(nodeindex)][0])
            y=float(nodeLocations[int(nodeindex)][1])
            z=float(nodeLocations[int(nodeindex)][2])
            location=Vector3(x,y,z)
            edgesNewId=[]
            for edgesNodeIndex in nodeValue["edges"]:
                edgesNodeId=convertToNodeId(mapid,edgesNodeIndex)
                edgesNewId.append(edgesNodeId)
            newNode=Node(nodeid,location,mapid,edgesNewId)
            meredGraph.addNode(newNode)
    #setup all entry points
    for mapid,value in allmaps.items():
        entrypoints=value["entry_points"]
        for nodeindex,value in entrypoints.items():
            fromNodeId=convertToNodeId(mapid,nodeindex)
            toNodeId=convertToNodeId(value["map_id"],value["node_index"])
            meredGraph.setEntryPoints(fromNodeId,toNodeId)
    return meredGraph

def loadWaypointGraphData(waypointgraphdata:dict)->WaypointGraph:
    idlist=[]
    nodeList=[]
    for nodeid,value in waypointgraphdata.items():
        idlist.append(nodeid)
        nodeList.append(convertJSONnodeToNode(nodeid,value))

    return WaypointGraph(idlist,nodeList)




def testLoadMap():
    data=loadJSONFile("/home/csl/ros2_ws/test_run/sample_data/waypointgraph.json")
    graph=loadWaypointGraphData(data)
    #print(convertWaypointGraphToJSON(graph))
    return graph

def preprocess():

    spacing=5
    filepath = Path("src/routing_agent/routing_agent/preprocess_maps/waypoint_graph_raw.yaml")

    yamlFile=ConvertDataFormat.loadYAMLFile(filepath)
    maps = yamlFile["entry_points"]
    graph=WaypointGraph()
    for map in maps:
        mapId = map["map_id"]
        id = []
        index=0
        nodeList = []
        lastEnd=Vector3(-1,-1,-1)
        for i in range(len(map["points"]) - 1):
            start = Vector3(map["points"][i]["coordinates"][0], map["points"][i]["coordinates"][1])
            end = Vector3(map["points"][i + 1]["coordinates"][0], map["points"][i + 1]["coordinates"][1])
            nodes = PreprocessToolkit.generate_intermediate_nodes_index(start, end, spacing)
            if(lastEnd==start):
                nodes=nodes[1::]

            for n in nodes:
                nodeid=generateNodeId(mapId,index)
                node=Node(id=nodeid,locallocation=n,mapid=mapId,isentrypoint=False)
                nodeList.append(node)
                index+=1

            lastEnd=end

        for i in range(len(nodeList)-1):
            connectTwoNodes(nodeList[i],nodeList[i+1])
            print(nodeList[i].id)
            print(nodeList[i].edges)
            graph.addNode(nodeList[i])
        graph.addNode(nodeList[len(nodeList)-1])

    print(graph.convertToJSON())

    graph.setEntryPoints("000_005","001_000")
    graph.setEntryPoints("001_008", "003_000")
    graph.setEntryPoints("001_015", "002_000")
    graph.setEntryPoints("003_019", "004_000")
    graph.setEntryPoints("004_012", "003_019")

    print(graph.convertToJSON())
    saveJSONAt(graph.convertToJSON(), "test.json")
    return graph



        #for i in id:
    #new={}
    #new["merged_file_data"]=yamlFile
    #new["merged_file_location"]="test"
    #print(convertWaypointGraphToJSON(graph))
    
    #graph=mergeWaypointGraph(new)
   # print(graph.convertToJSON())
    #saveJSONAt(graph.convertToJSON(),"test.json")
    #return graph
    
    


if __name__=="__main__":
   preprocess()

        






