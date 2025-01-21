from routing_agent_interfaces.srv import RoutingServiceMsg               # CHANGE
import sys
import rclpy
from rclpy.node import Node
import ConvertDataFormat


class RoutingClient(Node):

    def __init__(self):
        super().__init__('routing_client')
        self.cli = self.create_client(RoutingServiceMsg, 'RoutingService')       # CHANGE
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = RoutingServiceMsg.Request()
        

    def send_request(self):
        orders_file_location=sys.argv[1]
        vehicle_data_location=sys.argv[2]
        self.req.task_data,self.req.vehicle_data=self.readFiles(orders_file_location,vehicle_data_location)
        self.future = self.cli.call_async(self.req)

    def readFiles(self,orders_file_location,vehicle_data_location):
        orderData=ConvertDataFormat.loadJSONFileToStr(orders_file_location)
        vehicleData=ConvertDataFormat.loadJSONFileToStr(vehicle_data_location)
        return orderData,vehicleData


def main(args=None):
    rclpy.init(args=args)
    routingClient = RoutingClient()
    routingClient.send_request()

    while rclpy.ok():
        rclpy.spin_once(routingClient)
        if routingClient.future.done():
            try:
                response = routingClient.future.result()
            except Exception as e:
                routingClient.get_logger().info(
                    'Service call failed %r' % (e,))
            else:
                #response_data=json.loads(response.response_data)
                routingClient.get_logger().info(
                    'Routes: '+str(response.response_data)
                    )  # CHANGE
            break

    rclpy.shutdown()

                
    

