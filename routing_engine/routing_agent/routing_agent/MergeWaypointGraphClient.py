from routing_agent_interfaces.srv import MergeWaypointGraphServiceMsg               # CHANGE
import sys
import rclpy
from rclpy.node import Node
import ConvertDataFormat
import json
from pathlib import Path

defaultFileName="MergedWaypointGraph.json"

class MergeWaypointGraphClient(Node):

    def __init__(self):
        super().__init__('merge_waypointgraph')
        self.cli = self.create_client(MergeWaypointGraphServiceMsg, 'MergeWaypointGraphService')       # CHANGE
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = MergeWaypointGraphServiceMsg.Request()
        
                                           # CHANG

    def send_request(self):
        self.req.maps_config_data=self.loadMapsConfig(sys.argv[1])
        self.future = self.cli.call_async(self.req)

    def loadMapsConfig(self,filepath):
        filepath = Path(filepath)
        configData=ConvertDataFormat.loadJSONFile(filepath)
        for mapid in configData.keys():
            mapPath=str(filepath.parent)+"/"+configData[mapid]["file_path"]
            mapData=ConvertDataFormat.loadJSONFile(mapPath)
            configData[mapid]["file_data"]=mapData
        newConfig={
        "merged_file_location":str(filepath.parent)+"/"+defaultFileName,
        "merged_file_data":configData
        }
        return ConvertDataFormat.convertJSONToStr(newConfig)



def main(args=None):
    rclpy.init(args=args)
    mergeClient = MergeWaypointGraphClient()
    mergeClient.send_request()

    while rclpy.ok():
        rclpy.spin_once(mergeClient)
        if mergeClient.future.done():
            try:
                response = mergeClient.future.result()
            except Exception as e:
                mergeClient.get_logger().info(
                    'Service call failed %r' % (e,))
            else:
                if(response.can_merge):
                    mergeClient.get_logger().info(
                    'Merge WaypointGraph Successfully,\n Stores at {}'.format(response.global_waypoint_graph_file_location))
                    
                else:
                    mergeClient.get_logger().info(
                    'Merge WaypointGraph Failed')
            break

    mergeClient.destroy_node()
    rclpy.shutdown()
    
                
    

