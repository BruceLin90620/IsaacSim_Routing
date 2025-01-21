import numpy as np
from typing import Tuple

def initDist(graph):
    dist = {}
    for n in graph:
        dist[n] = float('inf')
    return dist

def dijkstra(graph, start):
    path = {}

    shortestdist = initDist(graph)

    shortestdist[start] = 0

    for _ in range(len(graph) - 1):
        for node in graph:
            for near, w in graph[node].items():
                if shortestdist[node] + w < shortestdist[near]:
                    shortestdist[near] = shortestdist[node] + w
                    path[near] = node

    return shortestdist, path

def getPathToDest(dijpath, destination):
    path = [destination]
    target = dijpath[destination]
    while target in dijpath:
        path.append(target)
        target = dijpath[target]
    
    path.reverse()
    return path



def convertFromShortestDistToNpArray(shortestdist):
    dist=[]
    for key in shortestdist:
        dist.append(shortestdist[key])
    return np.array(dist)

def getShortestPath(dijpath, target):
    path = []
    while target in dijpath:
        path.append(target)
        target = dijpath[target]
    path.append(target)
    path.reverse()
    return path


def putDijPathIntoPathMatrix(dijpath,pathmatrix):
    for i in range(len(dijpath)):
        shortestpath = getShortestPath(dijpath, i)
        shortestpath=list(map(int,shortestpath))
        source=shortestpath[0]
        destination=shortestpath[-1]
        pathmatrix[source][destination]=shortestpath
    return pathmatrix

def initPathMatrix(matrixsize):
    pathmatrix=[]
    for i in range(matrixsize):
        row=[]
        for j in range(matrixsize):
            row.append([])
        pathmatrix.append(row)
    return pathmatrix


def findAllShortestPath(graph)->Tuple[np.array,list[list[str]]]:
    costmatrix=[]
    pathmatrix=initPathMatrix(len(graph))
    
    for start in range(len(graph)):
        ## traverse every node in graph and get every shortestpath from every node
        shortestdist, dijpath=dijkstra(graph,start)
        row=convertFromShortestDistToNpArray(shortestdist)
        pathmatrix=putDijPathIntoPathMatrix(dijpath,pathmatrix)
        if(len(costmatrix)==0):
            costmatrix=row
        else:
            costmatrix=np.vstack((costmatrix,row))

    return costmatrix,pathmatrix


def calculateOffsetRange(offsetindex,offsets):
    offsetrange=0
    if(offsetindex==len(offsets)-1):
        offsetrange=len(offsets)
    else:
        offsetrange=offsets[offsetindex+1]
    return offsetrange

def getTargetsAndWeightsFromStart(offsetindex,offsets,edges,weights):
    valueindexto=calculateOffsetRange(offsetindex, offsets)
    valueindexfrom=offsets[offsetindex]
    targets=edges[valueindexfrom:valueindexto]
    weights=weights[valueindexfrom:valueindexto]
    return targets,weights


def convertFromCSRToDijGraph(offsets,edges,weights):
    graph = {}
    for offsetindex in range(len(offsets)-1):
        startnode=offsetindex
        targetsAtThisIndex,weightsAtThisIndex=getTargetsAndWeightsFromStart(offsetindex,offsets,edges,weights)

        if (startnode not in graph):
            graph[startnode] = {}
        for i in range(len(targetsAtThisIndex)):

            targetnode=targetsAtThisIndex[i]
            weight=weightsAtThisIndex[i]

            if (targetnode not in graph):
                graph[targetnode] = {}
            if (weight == float("inf")):
                continue
            elif (weight < 0):
                graph[targetnode][startnode] = abs(float(weight))
            else:
                graph[startnode][targetnode] = float(weight)
    return graph


