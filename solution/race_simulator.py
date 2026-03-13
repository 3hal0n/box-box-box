import sys
import json

# TIRE PERFORMANCE CONSTANTS
# To score 100%, you may need to slightly tweak these 9 numbers based on your historical data.
TIRE_PARAMS = {
    "SOFT":   {"offset": -1.2, "deg_rate": 0.085, "temp_multiplier": 0.002},
    "MEDIUM": {"offset": 0.0,  "deg_rate": 0.050, "temp_multiplier": 0.001},
    "HARD":   {"offset": 1.0,  "deg_rate": 0.025, "temp_multiplier": 0.0005}
}

def simulate_race(race_data):
    config = race_data["race_config"]
    strategies = race_data["strategies"]
    
    base_lap_time = config["base_lap_time"]
    pit_lane_time = config["pit_lane_time"]
    total_laps = config["total_laps"]
    track_temp = config["track_temp"]
    
    results = []
    
    for pos_key, driver_data in strategies.items():
        driver_id = driver_data["driver_id"]
        current_tire = driver_data["starting_tire"]
        
        # Map lap number to the new tire compound for quick lookups
        pit_stops = {stop["lap"]: stop["to_tire"] for stop in driver_data.get("pit_stops", [])}
        
        total_time = 0.0
        tire_age = 0
        
        for lap in range(1, total_laps + 1):
            tire_age += 1
            
            # Calculate lap time based on base time, compound speed, and degradation
            params = TIRE_PARAMS[current_tire]
            degradation = (params["deg_rate"] + (params["temp_multiplier"] * track_temp)) * tire_age
            lap_time = base_lap_time + params["offset"] + degradation
            
            total_time += lap_time
            
            # Execute pit stop if scheduled for the end of this lap
            if lap in pit_stops:
                total_time += pit_lane_time
                current_tire = pit_stops[lap]
                tire_age = 0  # Reset tire age on fresh tires
                
        results.append({
            "driver_id": driver_id,
            "total_time": total_time
        })
        
    # Sort drivers by lowest total time
    results.sort(key=lambda x: x["total_time"])
    
    # Extract only the driver IDs for the final output
    finishing_positions = [r["driver_id"] for r in results]
    
    return {
        "race_id": race_data["race_id"],
        "finishing_positions": finishing_positions
    }

if __name__ == "__main__":
    # Read test cases from standard input as required by the submission guide
    input_json = sys.stdin.read()
    if input_json.strip():
        race_data = json.loads(input_json)
        output_data = simulate_race(race_data)
        # Write results to standard output
        print(json.dumps(output_data, indent=2))