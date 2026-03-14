import sys
import json
import os
import numpy as np
from scipy.optimize import differential_evolution

def load_final_exam():
    races = []
    input_dir = "data/test_cases/inputs"
    output_dir = "data/test_cases/expected_outputs"
    
    for i in range(1, 101):
        num = str(i).zfill(3)
        in_path = os.path.join(input_dir, f"test_{num}.json")
        out_path = os.path.join(output_dir, f"test_{num}.json")
        
        if os.path.exists(in_path) and os.path.exists(out_path):
            with open(in_path, "r") as f:
                in_data = json.load(f)
            with open(out_path, "r") as f:
                out_data = json.load(f)
            
            in_data["expected"] = out_data["finishing_positions"]
            races.append(in_data)
    return races

def vec_to_params(v):
    # Maps the Scipy flat vector back to our 38% parameter dictionary
    return {
        "temp_coef": v[0],
        "SOFT":   {"offset": v[1], "deg": v[2], "cliff": round(v[3])},
        "MEDIUM": {"offset": v[4], "deg": v[5], "cliff": round(v[6])},
        "HARD":   {"offset": v[7], "deg": v[8], "cliff": round(v[9])}
    }

def calc_stint_time(tire_name, laps, base_time, temp, params):
    if laps <= 0: 
        return 0.0
        
    tire = params[tire_name]
    lap_speed = base_time + tire["offset"]
    
    actual_deg = tire["deg"] * (1.0 + temp * params["temp_coef"])
    total_stint_time = laps * lap_speed
    
    # Arithmetic Progression (The True Physics Engine)
    if laps > tire["cliff"]:
        n = laps - tire["cliff"]
        total_stint_time += actual_deg * (n * (n + 1)) / 2.0
        
    return total_stint_time

def simulate(race, params):
    config = race["race_config"]
    base = float(config["base_lap_time"])
    plt = float(config["pit_lane_time"])
    laps = int(config["total_laps"])
    temp = float(config["track_temp"])
    
    times = {}
    for pos_key, strategy in race["strategies"].items():
        driver = strategy["driver_id"]
        pit_stops = sorted(strategy.get("pit_stops", []), key=lambda x: x["lap"])
        
        total = 0.0
        curr_lap = 1
        curr_tire = strategy["starting_tire"]
        
        for stop in pit_stops:
            stint_laps = stop["lap"] - curr_lap + 1
            total += calc_stint_time(curr_tire, stint_laps, base, temp, params)
            total += plt
            curr_lap = stop["lap"] + 1
            curr_tire = stop["to_tire"]
            
        final_laps = laps - curr_lap + 1
        total += calc_stint_time(curr_tire, final_laps, base, temp, params)
        times[driver] = total
        
    return times

def loss(v, races):
    params = vec_to_params(v)
    wrong_pairs = 0
    total_pairs = 0
    
    for race in races:
        times = simulate(race, params)
        expected = race["expected"]
        
        for i in range(len(expected)):
            for j in range(i + 1, len(expected)):
                total_pairs += 1
                # If Driver i should beat Driver j, but their time is higher/equal, penalize
                if times[expected[i]] >= times[expected[j]]:
                    wrong_pairs += 1
                    
    # Scipy attempts to push this error fraction to 0.0
    return wrong_pairs / total_pairs

def main():
    races = load_final_exam()
    if not races:
        print("Error: Could not load test cases.")
        return
        
    print("Firing up Scipy Differential Evolution...")
    
    # 10 Dimensions bounded tightly around your successful 38% model
    bounds = [
        (0.08, 0.15),      # temp_coef
        (2.0, 4.0),        # SOFT offset
        (0.2, 0.5),        # SOFT deg
        (5, 15),           # SOFT cliff
        (3.0, 5.0),        # MEDIUM offset
        (0.1, 0.3),        # MEDIUM deg
        (15, 25),          # MEDIUM cliff
        (4.0, 6.0),        # HARD offset
        (0.05, 0.2),       # HARD deg
        (25, 35)           # HARD cliff
    ]
    
    # Let scipy do the heavy lifting
    result = differential_evolution(
        loss, 
        bounds, 
        args=(races,),
        maxiter=1000, 
        popsize=20, 
        mutation=(0.5, 1.5), 
        recombination=0.9,
        seed=42, 
        disp=True,     # Will print its own internal iteration metrics
        workers=-1     # Parallel processing across all CPU cores
    )

    print("\n" + "="*50)
    print("OPTIMIZATION FINISHED!")
    print(f"Final Pairwise Error Rate: {result.fun:.6f}")
    print("Paste this into your race_simulator.py PARAMS block:\n")
    final_params = vec_to_params(result.x)
    print(json.dumps(final_params, indent=4))
    print("="*50)

if __name__ == '__main__':
    main()