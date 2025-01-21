import json
def exportAsCuOptFormat(routes,solutionCost,exportlocation):

    # Data to be written
    vehdata={"Veh-A":{"task_id": ["Depot", "0", "Break", "4", "Depot"],
                    "arrival_stamp": [6.0, 7.0, 20.0, 21.0, 29.0],
                    "route": routes,
                    "type": ["Depot", "Delivery", "w", "w", "w", "w", "w", "Break", "Delivery", "w", "w", "w", "Depot"]},
             "Veh-B": {"task_id": ["Depot", "0", "Break", "4", "Depot"],
                       "arrival_stamp": [6.0, 7.0, 20.0, 21.0, 29.0],
                       "route": routes,
                       "type": ["Depot", "Delivery", "w", "w", "w", "w", "w", "Break", "Delivery", "w", "w", "w",
                                "Depot"]}
             }

    data = {
        "response":{
            "solver_response":{
                "status": 0,
                "num_vehicles": 3,
                "solution_cost": solutionCost,
                "vehicle_data":vehdata,
                "dropped_tasks": {
              "task_id": [],
              "task_index": []
            },
            "msg": ""
            },
        "reqId": "Ass"
    }
    }

    # Serializing json
    json_object = json.dumps(data, indent=2)

    # Writing to sample.json
    with open(exportlocation, "w") as outfile:
        outfile.write(json_object)


def exportResponse():
    data={
        
    }

    json_data = json.dumps(data, indent=2)
    return str(json_data)
