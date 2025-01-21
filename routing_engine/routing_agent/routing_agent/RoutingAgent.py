import json
import ConvertDataFormat
import OR
import RoutingAgentExport
graph_file_location= "./og_data/waypoint_graph.json"
orders_file_location= "./og_data/orders_data.json"
vehicle_file_location="./og_data/vehicle_data.json"
export_file_location="./og_data/OR_response.json"

def runORAgentByFile(graph_file_location,orders_file_location,vehicle_file_location,export_file_location):
    ##preprocess
    offsets,edges,weights,orders=ConvertDataFormat.preprocess(graph_file_location,orders_file_location)

    costmatrix,pathmatrix=OR.generateMatrix(offsets,edges,weights)


    solution,totalCost=OR.solveTSP(costmatrix,orders)
    solutionPath=OR.generateSolution(pathmatrix, solution)
    RoutingAgentExport.exportFormat(solutionPath,totalCost,export_file_location)
    ##costmatrix as argument

def runORAgentByROS(waypoint_graph_locations,waypoint_graph_edges,waypoint_graph_offsets,task_locations,vehicle_start_location):
    weights,orders=ConvertDataFormat.preprocessROS(waypoint_graph_locations,waypoint_graph_edges,waypoint_graph_offsets,task_locations,vehicle_start_location)

    costmatrix,pathmatrix=OR.generateMatrix(waypoint_graph_offsets,waypoint_graph_edges,weights)

    solution,totalCost=OR.solveTSP(costmatrix,orders)
    solutionPath=OR.generateSolution(pathmatrix, solution)
    solPathLocations=ConvertDataFormat.convertSolutionPathToLocation(solutionPath,waypoint_graph_locations)

    return solutionPath,solPathLocations

def runRoutingAgent(waypoint_graph_data,task_locations_data,vehicle_start_locations_data):
    print(waypoint_graph_data)
    waypoint_graph_data=json.loads(waypoint_graph_data)
    task_locations_data=json.loads(task_locations_data)
    vehicle_start_locations_data=json.loads(vehicle_start_locations_data)
    
    #temp
    waypoint_graph_locations=waypoint_graph_data["node_locations"]
    waypoint_graph_locations=list(map(float,ConvertDataFormat.convertFrom2DListTo1D(waypoint_graph_locations)))

    waypoint_graph_edges,waypoint_graph_offsets=ConvertDataFormat.convertGraphFileToCSR(waypoint_graph_data)
    waypoint_graph_edges=waypoint_graph_edges.tolist()
    waypoint_graph_offsets=waypoint_graph_offsets.tolist()

    task_locations=task_locations_data["task_locations"]
    task_locations=list(map(float,ConvertDataFormat.convertFrom2DListTo1D(task_locations)))

    vehicle_start_location=list(map(float,vehicle_start_locations_data["vehicle_locations"][0]))
    
    weights,orders=ConvertDataFormat.preprocessROS(waypoint_graph_locations,waypoint_graph_edges,waypoint_graph_offsets,task_locations,vehicle_start_location)

    costmatrix,pathmatrix=OR.generateMatrix(waypoint_graph_offsets,waypoint_graph_edges,weights)

    solution,totalCost=OR.solveTSP(costmatrix,orders)
    solutionPath=OR.generateSolution(pathmatrix, solution)
    solPathLocations=ConvertDataFormat.convertSolutionPathToLocation(solutionPath,waypoint_graph_locations)
    return json.dumps(waypoint_graph_data)
    


if __name__=="__main__":
    runORAgentByFile(graph_file_location,orders_file_location,vehicle_file_location,export_file_location)