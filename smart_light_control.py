import os
import sys
import argparse

# Ensure SUMO_HOME is set in python environment so we can import traci
if 'SUMO_HOME' not in os.environ:
    os.environ['SUMO_HOME'] = r"C:\Program Files (x86)\Eclipse\Sumo"

tools_path = os.path.join(os.environ['SUMO_HOME'], 'tools')
if tools_path not in sys.path:
    sys.path.append(tools_path)

import traci
import sumolib

def get_edge_weight(edge_id):
    """
    Retrieves the weighted queue size for the given edge.
    Bus = 2.0, Truck = 2.0, Car = 1.0, Motorcycle = 0.5
    Only counts vehicles that are currently stopped or moving slowly (< 1.0 m/s).
    """
    total_weight = 0.0
    # Lanes are edge_id + _0 and edge_id + _1
    lanes = [f"{edge_id}_0", f"{edge_id}_1"]
    
    for lane in lanes:
        try:
            veh_ids = traci.lane.getLastStepVehicleIDs(lane)
            for veh_id in veh_ids:
                speed = traci.vehicle.getSpeed(veh_id)
                # Count only queued vehicles (speed < 1.0 m/s)
                if speed < 1.0:
                    vtype = traci.vehicle.getTypeID(veh_id)
                    if vtype in ["bus", "truck"]:
                        total_weight += 2.0
                    elif vtype == "motorcycle":
                        total_weight += 0.5
                    else:
                        total_weight += 1.0  # default (car)
        except traci.exceptions.TraCIException:
            pass
    return total_weight

def set_traffic_light_state(tl_id, controlled_links, active_edges, yellow=False):
    """
    Sets the traffic light state dynamically based on active edges.
    """
    state_len = len(controlled_links)
    state = ["r"] * state_len
    
    for idx, links in enumerate(controlled_links):
        for link in links:
            incoming_lane = link[0]  # e.g., "N2J0_0"
            for edge in active_edges:
                if incoming_lane.startswith(edge):
                    state[idx] = "y" if yellow else "G"
                    break
                    
    state_str = "".join(state)
    traci.trafficlight.setRedYellowGreenState(tl_id, state_str)
    return state_str

def main():
    parser = argparse.ArgumentParser(description="SmartLight Adaptive Control Engine")
    parser.add_argument("--sumocfg", type=str, default="simulation/intersection.sumocfg", help="SUMO config file")
    parser.add_argument("--gui", action="store_true", help="Run with SUMO GUI")
    parser.add_argument("--output-tripinfo", type=str, default="simulation/tripinfo_smart.xml", help="Path to save trip info")
    args = parser.parse_args()

    # Determine binary
    sumo_bin = "sumo-gui" if args.gui else "sumo"
    sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', sumo_bin)

    # SUMO Cmd
    sumo_cmd = [
        sumo_binary,
        "-c", args.sumocfg,
        "--tripinfo-output", args.output_tripinfo,
        "--no-step-log", "true",
        "--waiting-time-memory", "1000"
    ]

    print("Starting SUMO simulation with SmartLight control...")
    traci.start(sumo_cmd)

    tl_id = "J0"
    controlled_links = traci.trafficlight.getControlledLinks(tl_id)
    
    # Active lane groups
    NS_edges = ["N2J0", "S2J0"]
    EW_edges = ["E2J0", "W2J0"]

    # Parameters
    MIN_GREEN = 15      # Minimum green light duration (seconds)
    MAX_GREEN = 60      # Maximum green light duration (seconds)
    YELLOW_TIME = 4     # Yellow transition duration (seconds)
    THRESHOLD = 3.0     # Disparity threshold to trigger a switch

    # State variables
    current_phase = "NS"  # NS or EW
    green_timer = 0
    in_yellow = False
    yellow_timer = 0
    next_phase = None

    # Initial state (NS Green)
    set_traffic_light_state(tl_id, controlled_links, NS_edges, yellow=False)

    step = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        step += 1

        if in_yellow:
            yellow_timer += 1
            if yellow_timer >= YELLOW_TIME:
                # Transition to next green phase
                in_yellow = False
                current_phase = next_phase
                green_timer = 0
                active_edges = NS_edges if current_phase == "NS" else EW_edges
                set_traffic_light_state(tl_id, controlled_links, active_edges, yellow=False)
                # print(f"[{step}s] Switch complete. Current green phase: {current_phase}")
        else:
            green_timer += 1
            
            # Query weights
            ns_weight = get_edge_weight("N2J0") + get_edge_weight("S2J0")
            ew_weight = get_edge_weight("E2J0") + get_edge_weight("W2J0")

            # Check if we should switch
            should_switch = False
            
            if green_timer >= MAX_GREEN:
                should_switch = True
                reason = "Max green reached"
            elif green_timer >= MIN_GREEN:
                if current_phase == "NS" and ew_weight > ns_weight + THRESHOLD and ew_weight > 0:
                    should_switch = True
                    reason = f"EW demand ({ew_weight}) exceeds NS ({ns_weight})"
                elif current_phase == "EW" and ns_weight > ew_weight + THRESHOLD and ns_weight > 0:
                    should_switch = True
                    reason = f"NS demand ({ns_weight}) exceeds EW ({ew_weight})"

            if should_switch:
                # Start yellow transition
                in_yellow = True
                yellow_timer = 0
                next_phase = "EW" if current_phase == "NS" else "NS"
                active_edges = NS_edges if current_phase == "NS" else EW_edges
                set_traffic_light_state(tl_id, controlled_links, active_edges, yellow=True)
                # print(f"[{step}s] Initiating switch {current_phase} -> {next_phase}. Reason: {reason}")

    traci.close()
    print("Simulation finished.")

if __name__ == "__main__":
    main()
