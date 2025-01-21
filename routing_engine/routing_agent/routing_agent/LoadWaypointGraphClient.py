from routing_agent_interfaces.srv import LoadWaypointGraphServiceMsg               # CHANGE
import sys
import rclpy
from rclpy.node import Node
import ConvertDataFormat
import json


class LoadWaypointGraphClient(Node):

    def __init__(self):
        super().__init__('load_waypointgraph')
        self.cli = self.create_client(LoadWaypointGraphServiceMsg, 'LoadWaypointGraphService')       # CHANGE
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = LoadWaypointGraphServiceMsg.Request()
        
                                           # CHANG

    def send_request(self):
        self.req.waypoint_graph_data=ConvertDataFormat.loadJSONFileToStr(sys.argv[1])
        self.future = self.cli.call_async(self.req)
        

def main(args=None):
    rclpy.init(args=args)
    loadClient = LoadWaypointGraphClient()
    loadClient.send_request()

    while rclpy.ok():
        rclpy.spin_once(loadClient)
        if loadClient.future.done():
            try:
                response = loadClient.future.result()
            except Exception as e:
                loadClient.get_logger().info(
                    'Service call failed %r' % (e,))
            else:
                if(response.can_load):
                    loadClient.get_logger().info(
                    'Load WaypointGraph Successfully')
                else:
                    loadClient.get_logger().info(
                    'Load WaypointGraph Failed')
            break

    loadClient.destroy_node()
    rclpy.shutdown()
    
                
    

