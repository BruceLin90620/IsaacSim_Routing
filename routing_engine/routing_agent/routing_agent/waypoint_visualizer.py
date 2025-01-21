from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
from std_msgs.msg import ColorRGBA
from rclpy.node import Node

class WaypointVisualizer:
    def __init__(self, node: Node):
        self.node = node
        self.marker_publisher = self.node.create_publisher(
            MarkerArray,
            'waypoint_markers',
            10
        )

    def create_waypoint_marker(self, waypoint_id, position, is_current=False):
        # Create sphere marker
        sphere_marker = Marker()
        sphere_marker.header.frame_id = "map"
        sphere_marker.header.stamp = self.node.get_clock().now().to_msg()
        sphere_marker.ns = "waypoints"
        sphere_marker.id = hash(waypoint_id) % 2147483647
        sphere_marker.type = Marker.SPHERE
        sphere_marker.action = Marker.ADD
        
        sphere_marker.pose.position.x = position[0]
        sphere_marker.pose.position.y = position[1]
        sphere_marker.pose.position.z = 0.0
        sphere_marker.pose.orientation.w = 1.0
        
        sphere_marker.scale.x = 0.3
        sphere_marker.scale.y = 0.3
        sphere_marker.scale.z = 0.3
        
        # Set color (red for current waypoint, blue for others)
        color = ColorRGBA()
        if is_current:
            color.r = 1.0
            color.g = 0.0
            color.b = 0.0
        else:
            color.r = 0.0
            color.g = 0.0
            color.b = 1.0
        color.a = 1.0
        sphere_marker.color = color

        # Create text marker
        text_marker = Marker()
        text_marker.header.frame_id = "map"
        text_marker.header.stamp = self.node.get_clock().now().to_msg()
        text_marker.ns = "waypoint_labels"
        text_marker.id = hash(waypoint_id + "_text") % 2147483647
        text_marker.type = Marker.TEXT_VIEW_FACING
        text_marker.action = Marker.ADD

        text_marker.pose.position.x = position[0]
        text_marker.pose.position.y = position[1]
        text_marker.pose.position.z = 0.3
        text_marker.pose.orientation.w = 1.0

        text_marker.text = waypoint_id
        text_marker.scale.z = 0.3

        text_marker.color.r = 0.0
        text_marker.color.g = 0.0
        text_marker.color.b = 0.0
        text_marker.color.a = 1.0
        
        return [sphere_marker, text_marker]

    def create_edge_marker(self, start_id, end_id, start_pos, end_pos):
        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = self.node.get_clock().now().to_msg()
        marker.ns = "edges"
        # Create unique ID for edge using both start and end waypoint IDs
        marker.id = hash(f"{start_id}_{end_id}") % 2147483647
        marker.type = Marker.LINE_STRIP
        marker.action = Marker.ADD
        
        point_start = Point()
        point_start.x = start_pos[0]
        point_start.y = start_pos[1]
        point_start.z = 0.0
        
        point_end = Point()
        point_end.x = end_pos[0]
        point_end.y = end_pos[1]
        point_end.z = 0.0
        
        marker.points = [point_start, point_end]
        marker.scale.x = 0.05
        
        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 1.0
        marker.color.a = 0.8
        
        return marker

    def create_deletion_markers(self):
        """Create markers to delete all previous markers"""
        deletion_markers = []
        
        # Delete all markers in each namespace
        for ns in ["waypoints", "waypoint_labels", "edges"]:
            marker = Marker()
            marker.header.frame_id = "map"
            marker.header.stamp = self.node.get_clock().now().to_msg()
            marker.ns = ns
            marker.id = 0
            marker.action = Marker.DELETEALL
            deletion_markers.append(marker)
            
        return deletion_markers

    def visualize_graph(self, waypoint_data, current_waypoint_id):
        if not waypoint_data:
            return

        # Create marker array and add deletion markers first
        marker_array = MarkerArray()
        marker_array.markers.extend(self.create_deletion_markers())

        # Get the prefix (e.g., "000" from "000_000")
        current_prefix = current_waypoint_id.split('_')[0]
        
        # Filter waypoints based on prefix and create markers
        for waypoint_id, waypoint_info in waypoint_data.items():
            prefix = waypoint_id.split('_')[0]
            if prefix == current_prefix:
                # Create waypoint markers
                is_current = (waypoint_id == current_waypoint_id)
                markers = self.create_waypoint_marker(
                    waypoint_id,
                    waypoint_info['local_location'],
                    is_current
                )
                marker_array.markers.extend(markers)
                
                # Create edge markers
                for edge in waypoint_info['edges']:
                    edge_prefix = edge.split('_')[0]
                    if edge_prefix == current_prefix and edge > waypoint_id:
                        edge_marker = self.create_edge_marker(
                            waypoint_id,  # Start waypoint ID
                            edge,         # End waypoint ID
                            waypoint_info['local_location'],
                            waypoint_data[edge]['local_location']
                        )
                        marker_array.markers.append(edge_marker)
        
        # Set lifetime for all markers
        for marker in marker_array.markers:
            marker.lifetime.sec = 0  # 0 means forever
            marker.lifetime.nanosec = 0
        
        # Publish marker array
        self.marker_publisher.publish(marker_array)