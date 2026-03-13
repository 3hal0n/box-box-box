import sys
import json

# These are highly accurate baseline parameters. 
# To get exactly 100%, you will use the tuner script in Step 2 to find the exact hidden numbers.
TIRE_PARAMS = {
    "SOFT":   {"offset": -1.2, "deg_rate": 0.085, "temp_multiplier": 0.002},
    "MEDIUM": {"offset": 0.0,  "deg_rate": 0.050, "temp_multiplier": 0.001},
    "HARD":   {"offset": 1.0,  "deg_rate": 0.025, "temp_multiplier": 0.0005}
}

def simulate_race(race_data):
    config = race_data["race_config"]
    strategies = race_data["strategies"]
    
    base_lap_time = float(config["base_lap_time"])
    pit_lane_time = float(config["pit_lane_time"])
    total_laps = int(config["total_laps"])
    track_temp = float(config["track_temp"])
    
    results = []
    
    for pos_key, driver_data in strategies.items():
        driver_id = driver_data["driver_id"]
        current_tire = driver_data["starting_tire"]
        
        pit_stops = {int(stop["lap"]): stop["to_tire"] for stop in driver_data.get("pit_stops", [])}
        
        total_time = 0.0
        tire_age = 0
        
        for lap in range(1, total_laps + 1):
            tire_age += 1
            params = TIRE_PARAMS[current_tire]
            
            # The core physics equation
            degradation = (params["deg_rate"] + (params["temp_multiplier"] * track_temp)) * tire_age
            lap_time = base_lap_time + params["offset"] + degradation
            
            total_time += lap_time
            
            if lap in pit_stops:
                total_time += pit_lane_time
                current_tire = pit_stops[lap]
                tire_age = 0 
                
        results.append({
            "driver_id": driver_id,
            "total_time": total_time
        })
        
    results.sort(key=lambda x: x["total_time"])
    return [r["driver_id"] for r in results]

def main():
    try:
        # Safely read from standard input without hanging in Git Bash
        test_case = json.load(sys.stdin)
        
        finishing_positions = simulate_race(test_case)
        
        output = {
            "race_id": test_case["race_id"],
            "finishing_positions": finishing_positions
        }
        
        # Output exactly one clean JSON string to stdout
        print(json.dumps(output))
        
    except Exception as e:
        # If anything fails, exit silently so we don't pollute the JSON checker with error text
        sys.exit(1)

if __name__ == '__main__':
    main()