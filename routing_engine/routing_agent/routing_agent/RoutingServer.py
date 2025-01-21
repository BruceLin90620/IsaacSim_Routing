from routing_agent_interfaces.srv import RoutingServiceMsg,MergeWaypointGraphServiceMsg,LoadWaypointGraphServiceMsg,NavServiceMsg
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

import routing_agent.RoutingAgent as RoutingAgent
import json
from ConvertDataFormat import convertJSONToStr,convertStrToJSON,saveJSONAt
from WaypointGraph import WaypointGraph,mergeWaypointGraph,loadWaypointGraphData
from RoutingEngine import RoutingEngine
from Task import loadTasksData
from Vehicle import loadVehiclesData
from waypoint_visualizer import WaypointVisualizer
import sys

class RoutingServer(Node):
    isWaypointGraphLoaded=False
    waypointGraph:WaypointGraph
    routingEngine:RoutingEngine

    def __init__(self):
        super().__init__('routing_server')

        qos = QoSProfile(
        depth=1,
        reliability=ReliabilityPolicy.RELIABLE,
        durability=DurabilityPolicy.TRANSIENT_LOCAL)
        
        self.loadWaypointGraphService=self.create_service(LoadWaypointGraphServiceMsg,"LoadWaypointGraphService",self.LoadWaypointGraphServiceCallBack)
        self.mergeWaypointGraphService=self.create_service(MergeWaypointGraphServiceMsg,"MergeWaypointGraphService",self.MergeWaypointGraphServiceCallBack)
        self.routingService = self.create_service(RoutingServiceMsg, 'RoutingService', self.RoutingServiceCallBack)
        # self.navService=self.create_service(NavServiceMsg,'NavService',self.NavServiceCallBack)
        self.navService=self.create_service(NavServiceMsg,'NavService',self.NavServiceCallBack, qos_profile = qos)

        self.visualizer = WaypointVisualizer(self)


    def MergeWaypointGraphServiceCallBack(self,request,response):
        mapsConfigData=json.loads(request.maps_config_data)
        mapSaveLocation=mapsConfigData["merged_file_location"]
        try:
            self.waypointGraph=mergeWaypointGraph(mapsConfigData)
            response.global_waypoint_graph_file_data=convertJSONToStr(self.waypointGraph.convertToJSON())
            saveJSONAt(self.waypointGraph.convertToJSON(),mapSaveLocation)
            response.global_waypoint_graph_file_location=mapSaveLocation
            response.can_merge=True
        except:
            response.can_merge=False

        self.isWaypointGraphLoaded=response.can_merge
           
        return response
    
    def LoadWaypointGraphServiceCallBack(self,request,response):
        #load 
        print(request.waypoint_graph_data)
        try:
            self.waypointGraph=loadWaypointGraphData(convertStrToJSON(request.waypoint_graph_data))
            response.can_load=True
        except:
            response.can_load=False
        self.isWaypointGraphLoaded=response.can_load
        return response
    
    def RoutingServiceCallBack(self, request, response):
        if(self.isWaypointGraphLoaded):
            try:
                tasks=loadTasksData(self.waypointGraph,convertStrToJSON(request.task_data))
            except:
                raise KeyError("Failed to load tasks into routing Engine")
            try:
                vehicles=loadVehiclesData(self.waypointGraph,convertStrToJSON(request.vehicle_data))
            except:
                raise KeyError("Failed to load vehicles into routing Engnine")
            try:
                self.routingEngine=RoutingEngine(self.waypointGraph,tasks,vehicles)
                response.response_data=str(self.routingEngine.taskSequence)
            except:
                raise KeyError("Failed to findpath")

        else:
            #change it to log... something
            raise KeyError("Please Load WaypointGraph First, use command loadGraph <waypoint_graph_file_location>")
        return response
    
    def NavServiceCallBack(self,request,response):
        if(request.can_arrive):
            self.routingEngine.update(request.i_am_at)
            response.path_to_next_task=convertJSONToStr(self.routingEngine.response())
        else:
            #set occupied
            self.routingEngine.update(request.i_am_at)
            response.path_to_next_task="Failed"

        # Visualize the graph based on current location
        if hasattr(self, 'waypointGraph'):
            self.visualizer.visualize_graph(
                self.waypointGraph.convertToJSON(),
                request.i_am_at
            )

        return response


        

def main(args=None):
    rclpy.init(args=args)

    routing_server = RoutingServer()

    rclpy.spin(routing_server)

    rclpy.shutdown()

if __name__ == '__main__':
    main()