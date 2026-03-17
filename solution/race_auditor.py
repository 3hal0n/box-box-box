import json
import os
import sys

# ---------------------------------------------------------
# THE 43% PHYSICS BASELINE
# ---------------------------------------------------------
PARAMS = {
    "temp_coef": 0.10084708792573656,
    "SOFT":   {"offset": 2.940339658164721, "deg": 0.40838371713557964, "cliff": 10},
    "MEDIUM": {"offset": 3.893908510501542, "deg": 0.2060938369164799, "cliff": 20},
    "HARD":   {"offset": 4.654949320493497, "deg": 0.10527266868872637, "cliff": 30},
    "fuel_burn": -0.00018346227813866148 # Using the fuel burn from your best run
}

def calc_stint_time(tire_name, stint_laps, base_time, temp, race_start_lap):
    if stint_laps <= 0: return 0.0
    tire = PARAMS[tire_name]
    lap_speed = base_time + tire["offset"]
    actual_deg = tire["deg"] * (1.0 + temp * PARAMS["temp_coef"])
    total_stint_time = 0.0
    
    for i in range(stint_laps):
        tire_age = i + 1
        abs_lap = race_start_lap + i
        current_lap = lap_speed + ((abs_lap - 1) * PARAMS["fuel_burn"])
        
        if tire_age > tire["cliff"]:
            current_lap += actual_deg * (tire_age - tire["cliff"])
            
        total_stint_time += round(current_lap, 3)
    return total_stint_time

def format_strategy(strategy, total_laps):
    """Formats the pit strategy into a readable string like S(15) -> H(35)"""
    stops = sorted(strategy.get("pit_stops", []), key=lambda x: x["lap"])
    curr_tire = strategy["starting_tire"][0] # Just the first letter S, M, or H
    curr_lap = 1
    
    strat_str = ""
    for stop in stops:
        stint_laps = stop["lap"] - curr_lap + 1
        strat_str += f"{curr_tire}({stint_laps}) -> "
        curr_lap = stop["lap"] + 1
        curr_tire = stop["to_tire"][0]
        
    final_laps = total_laps - curr_lap + 1
    strat_str += f"{curr_tire}({final_laps})"
    return strat_str

def main():
    # Load Test 001 explicitly
    in_path = "data/test_cases/inputs/test_001.json"
    out_path = "data/test_cases/expected_outputs/test_001.json"
    
    if not os.path.exists(in_path) or not os.path.exists(out_path):
        print("Error: Could not find test_001.json in the data folders.")
        sys.exit(1)
        
    with open(in_path, "r") as f: test_case = json.load(f)
    with open(out_path, "r") as f: expected_data = json.load(f)
    
    expected_order = expected_data["finishing_positions"]
    config = test_case['race_config']
    base = float(config['base_lap_time'])
    temp = float(config['track_temp'])
    plt = float(config['pit_lane_time'])
    total_laps = int(config['total_laps'])

    print(f"=== AUDIT REPORT: TEST_001 ===")
    print(f"Track Temp: {temp}°C | Laps: {total_laps} | Base Time: {base}s | Pit Time: {plt}s\n")

    results = []
    strats = {}
    
    for pos, strategy in test_case['strategies'].items():
        driver = strategy['driver_id']
        grid_pos = int(pos.replace('pos', ''))
        strats[driver] = format_strategy(strategy, total_laps)
        
        pit_stops = sorted(strategy.get('pit_stops', []), key=lambda x: x['lap'])
        total_time = 0.0
        curr_lap = 1
        curr_tire = strategy['starting_tire']
        
        for stop in pit_stops:
            stint_laps = stop['lap'] - curr_lap + 1
            total_time += calc_stint_time(curr_tire, stint_laps, base, temp, curr_lap)
            total_time += plt
            curr_lap = stop['lap'] + 1
            curr_tire = stop['to_tire']
            
        final_laps = total_laps - curr_lap + 1
        total_time += calc_stint_time(curr_tire, final_laps, base, temp, curr_lap)
        
        results.append({"driver": driver, "time": total_time, "grid": grid_pos})

    # Sort by our predicted time, tie-breaking with grid position
    results.sort(key=lambda x: (x["time"], x["grid"]))
    
    print(f"{'Rank':<5} | {'Expected':<10} | {'Predicted':<10} | {'Pred. Time':<12} | {'Gap to Prev':<12} | {'Strategy'}")
    print("-" * 90)
    
    prev_time = results[0]["time"]
    for i in range(20):
        actual_rank = i + 1
        expected_driver = expected_order[i]
        predicted_driver = results[i]["driver"]
        pred_time = results[i]["time"]
        gap = pred_time - prev_time
        
        # Highlight mismatches
        match_flag = "✅" if expected_driver == predicted_driver else "❌"
        
        print(f"P{actual_rank:<3} | {expected_driver:<10} | {predicted_driver:<10} | {pred_time:<12.3f} | +{gap:<11.3f} | {match_flag} {strats[predicted_driver]}")
        prev_time = pred_time

if __name__ == '__main__':
    main()