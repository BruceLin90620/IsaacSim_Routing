#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
from std_msgs.msg import ColorRGBA
import json

class WaypointVisualizer(Node):
    def __init__(self):
        super().__init__('waypoint_visualizer')
        
        # Create publisher for marker array
        self.marker_publisher = self.create_publisher(
            MarkerArray,
            'waypoint_markers',
            10
        )
        
        # Load waypoint data
        self.waypoints = self.load_waypoints()
        
        # Create timer for publishing markers
        self.timer = self.create_timer(1.0, self.publish_markers)
        
        self.get_logger().info('Waypoint visualizer node started')

    def load_waypoints(self):
        # In practice, you might want to use a parameter or command line argument for the file path
        with open('/home/bruce/IsaacSim/IsaacSim-ros_workspaces/humble_ws/src/routing_engine/graph_collector_and_visualization/waypointgraph_000_20250120_142806.json', 'r') as f:
            return json.load(f)

    def create_waypoint_marker(self, waypoint_id, position):
        # Create sphere marker
        sphere_marker = Marker()
        sphere_marker.header.frame_id = "map"  # Assuming the coordinates are in map frame
        sphere_marker.header.stamp = self.get_clock().now().to_msg()
        sphere_marker.ns = "waypoints"
        sphere_marker.id = hash(waypoint_id) % 2147483647  # Convert string ID to integer
        sphere_marker.type = Marker.SPHERE
        sphere_marker.action = Marker.ADD
        
        # Set position (z = 0)
        sphere_marker.pose.position.x = position[0]
        sphere_marker.pose.position.y = position[1]
        sphere_marker.pose.position.z = 0.0
        sphere_marker.pose.orientation.w = 1.0
        
        # Set scale
        sphere_marker.scale.x = 0.3
        sphere_marker.scale.y = 0.3
        sphere_marker.scale.z = 0.3
        
        # Set color (blue for all waypoints)
        color = ColorRGBA()
        color.r = 0.0
        color.g = 0.0
        color.b = 1.0
        color.a = 1.0
        sphere_marker.color = color

        # Create text marker
        text_marker = Marker()
        text_marker.header.frame_id = "map"
        text_marker.header.stamp = self.get_clock().now().to_msg()
        text_marker.ns = "waypoint_labels"
        text_marker.id = hash(waypoint_id + "_text") % 2147483647
        text_marker.type = Marker.TEXT_VIEW_FACING
        text_marker.action = Marker.ADD

        # Position text at the same height as sphere
        text_marker.pose.position.x = position[0]
        text_marker.pose.position.y = position[1]
        text_marker.pose.position.z = 0.3

        text_marker.pose.orientation.w = 1.0

        # Set text properties
        text_marker.text = waypoint_id
        text_marker.scale.z = 0.3  # Text height

        # White color for text
        text_marker.color.r = 1.0
        text_marker.color.g = 1.0
        text_marker.color.b = 1.0
        text_marker.color.a = 1.0
        
        return [sphere_marker, text_marker]

    def create_edge_marker(self, edge_id, start_pos, end_pos):
        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "edges"
        marker.id = edge_id
        marker.type = Marker.LINE_STRIP
        marker.action = Marker.ADD
        
        # Add start and end points
        point_start = Point()
        point_start.x = start_pos[0]
        point_start.y = start_pos[1]
        point_start.z = 0.0
        
        point_end = Point()
        point_end.x = end_pos[0]
        point_end.y = end_pos[1]
        point_end.z = 0.0
        
        marker.points = [point_start, point_end]
        
        # Set scale (line width)
        marker.scale.x = 0.05
        
        # Set color (white)
        color = ColorRGBA()
        color.r = 1.0
        color.g = 1.0
        color.b = 1.0
        color.a = 0.8
        marker.color = color
        
        return marker

    def publish_markers(self):
        marker_array = MarkerArray()
        edge_id = 0
        
        # Create markers for all waypoints
        for waypoint_id, waypoint_data in self.waypoints.items():
            # Create waypoint markers (sphere and text)
            markers = self.create_waypoint_marker(
                waypoint_id,
                waypoint_data['local_location']
            )
            marker_array.markers.extend(markers)
            
            # Create edge markers
            for edge in waypoint_data['edges']:
                if edge > waypoint_id:  # Only create edge once
                    edge_marker = self.create_edge_marker(
                        edge_id,
                        waypoint_data['local_location'],
                        self.waypoints[edge]['local_location']
                    )
                    marker_array.markers.append(edge_marker)
                    edge_id += 1
        
        # Publish marker array
        self.marker_publisher.publish(marker_array)

def main():
    rclpy.init()
    node = WaypointVisualizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()