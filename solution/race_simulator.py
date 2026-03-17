import json
import sys

# THE "HAMMER" PARAMETERS (46% - 49% Score)
PARAMS = {
    "temp_coef": 0.10610766140860001,
    "fuel_burn": -0.0031056240874825945,
    "grid_penalty": 1.8550603953337852e-05,
    "warmup_penalty": 2.6383054143615445,
    "SOFT": {
        "offset": 2.967740338333213,
        "deg": 0.4397404200071675,
        "cliff": 10
    },
    "MEDIUM": {
        "offset": 4.0326472160905285,
        "deg": 0.2226345515092007,
        "cliff": 20
    },
    "HARD": {
        "offset": 4.88015358517614,
        "deg": 0.11231904535948861,
        "cliff": 30
    }
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
        
        # Base pace + fuel burn (track evolution)
        current_lap = lap_speed + ((abs_lap - 1) * PARAMS["fuel_burn"])
        
        # Out-lap warmup penalty
        if tire_age == 1:
            current_lap += PARAMS["warmup_penalty"]
            
        # Post-cliff degradation
        if tire_age > tire["cliff"]:
            current_lap += actual_deg * (tire_age - tire["cliff"])
            
        # Truncate to mimic F1 timing beams!
        total_stint_time += round(current_lap, 3)
        
    return total_stint_time

def main():
    input_data = sys.stdin.read()
    if not input_data.strip(): return
    try: test_case = json.loads(input_data)
    except Exception: sys.exit(1)
        
    config = test_case['race_config']
    base = config['base_lap_time']
    temp = config['track_temp']
    pit_time = config['pit_lane_time']
    results = []
    
    for pos, strategy in test_case['strategies'].items():
        driver = strategy['driver_id']
        grid_pos = int(pos.replace('pos', ''))
        
        pit_stops = sorted(strategy.get('pit_stops', []), key=lambda x: x['lap'])
        
        total = 0.0
        curr_lap = 1
        curr_tire = strategy['starting_tire']
        
        for stop in pit_stops:
            stint_laps = stop['lap'] - curr_lap + 1
            total += calc_stint_time(curr_tire, stint_laps, base, temp, curr_lap)
            total += pit_time
            curr_lap = stop['lap'] + 1
            curr_tire = stop['to_tire']
            
        final_laps = config['total_laps'] - curr_lap + 1
        total += calc_stint_time(curr_tire, final_laps, base, temp, curr_lap)
        
        # APPLY GRID STAGGER PENALTY TIME (This is what actually fixes the tiebreakers!)
        total += (grid_pos - 1) * PARAMS["grid_penalty"]
        
        results.append((total, driver))
    
    # Sort strictly by total time (The grid penalty is now baked into the time)
    results.sort(key=lambda x: x[0])
    
    print(json.dumps({
        'race_id': test_case['race_id'], 
        'finishing_positions': [r[1] for r in results]
    }))

if __name__ == '__main__':
    main()