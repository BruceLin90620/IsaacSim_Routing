from Vector import Vector3
import math

def generate_intermediate_nodes_index(startVector, endVector, spacing):
    """
    Generate intermediate nodes between two points with a given spacing.

    Args:
    startVector (tuple): Coordinates of the starting node (startVector.x, startVector.y).
    endVector (tuple): Coordinates of the ending node (endVector.x, endVector.y).
    spacing (float): Desired spacing between consecutive nodes.

    Returns:
    list: A list of tuples representing the intermediate nodes, including the start and end nodes.
    """

    # Calculate the distance between the two nodes
    distance = math.sqrt((endVector.x - startVector.x) ** 2 + (endVector.y - startVector.y) ** 2)

    # Determine the number of segments
    if distance == 0 or spacing <= 0:
        raise ValueError("Spacing must be greater than 0 and nodes must not be the same.")

    num_segments = int(distance // spacing)

    # Generate intermediate points
    intermediate_nodes = [
        Vector3(
            startVector.x + i * spacing * (endVector.x - startVector.x) / distance,
            startVector.y + i * spacing * (endVector.y - startVector.y) / distance
        )
        for i in range(num_segments + 1)
    ]
    # Add the endpoint if it's not exactly at spacing distance
    if intermediate_nodes[-1] != endVector:
        intermediate_nodes.append(endVector)

    return intermediate_nodes


