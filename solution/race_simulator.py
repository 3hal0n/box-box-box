import sys
import json

# PLACEHOLDER: Paste the JSON output from the Swarm Optimizer here
TIRE_PARAMS = {
    "SOFT": {
        "offset": -2.5,
        "cliff": 9,
        "deg_rate": 0.19054860543963945,
        "temp_factor": 0.007334743359827993,
        "deg_curve": 2.5
    },
    "MEDIUM": {
        "offset": -0.2008750990380187,
        "cliff": 21,
        "deg_rate": 0.09906448077314667,
        "temp_factor": 0.018438386318555627,
        "deg_curve": 2.0252954144599684
    },
    "HARD": {
        "offset": 1.7649988936225545,
        "cliff": 34,
        "deg_rate": 0.009536099407843243,
        "temp_factor": 0.02,
        "deg_curve": 1.896680645721601
    }
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
            
            # The Universal Exponential Physics Model
            deg_laps = max(0, tire_age - params["cliff"])
            degradation = (params["deg_rate"] + (track_temp * params["temp_factor"])) * (deg_laps ** params["deg_curve"])
            
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
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        return
        
    test_case = json.loads(raw_input)
    finishing_positions = simulate_race(test_case)
    
    output = {
        "race_id": test_case["race_id"],
        "finishing_positions": finishing_positions
    }
    
    print(json.dumps(output))

if __name__ == '__main__':
    main()