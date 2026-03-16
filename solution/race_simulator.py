import json
import sys

# ---------------------------------------------------------
# THE GRAND UNIFICATION PARAMETERS (Fuel Burn Included)
# ---------------------------------------------------------
PARAMS = {
    "temp_coef": 0.11311484948260649,
    "SOFT": {
        "offset": 2.984863194118973,
        "deg": 0.38441487853368894,
        "cliff": 10
    },
    "MEDIUM": {
        "offset": 3.9329610206245578,
        "deg": 0.19537522963297882,
        "cliff": 20
    },
    "HARD": {
        "offset": 4.713546397285239,
        "deg": 0.10054740819469717,
        "cliff": 30
    },
    "fuel_burn": -0.000137964660469094
}

def calc_stint_time(tire_name, laps, base_time, temp, race_start_lap):
    if laps <= 0: 
        return 0.0
        
    tire = PARAMS[tire_name]
    lap_speed = base_time + tire["offset"]
    actual_deg = tire["deg"] * (1.0 + temp * PARAMS["temp_coef"])
    
    total_stint_time = 0.0
    
    # Calculate lap-by-lap to simulate F1 Timing Systems exactly
    for i in range(laps):
        lap_of_stint = i + 1
        absolute_race_lap = race_start_lap + i
        
        # 1. Base speed + Fuel Burn (Car gets lighter/faster every lap)
        current_lap_time = lap_speed + ((absolute_race_lap - 1) * PARAMS["fuel_burn"])
            
        # 2. Degradation penalty (Only applies after the cliff)
        if lap_of_stint > tire["cliff"]:
            n = lap_of_stint - tire["cliff"]
            current_lap_time += (actual_deg * n)
            
        # 3. Lap-by-Lap F1 Truncation (Rounds to 3 decimal places per lap)
        total_stint_time += round(current_lap_time, 3)
        
    return total_stint_time

def main():
    input_data = sys.stdin.read()
    if not input_data.strip():
        return
        
    try: 
        test_case = json.loads(input_data)
    except Exception: 
        sys.exit(1)
        
    config = test_case['race_config']
    base = config['base_lap_time']
    temp = config['track_temp']
    pit_time = config['pit_lane_time']
    
    results = []
    
    for pos, strategy in test_case['strategies'].items():
        driver = strategy['driver_id']
        pit_stops = sorted(strategy.get('pit_stops', []), key=lambda x: x['lap'])
        
        total = 0.0
        curr_lap = 1
        curr_tire = strategy['starting_tire']
        
        for stop in pit_stops:
            stint_laps = stop['lap'] - curr_lap + 1
            # Pass curr_lap so the engine knows how much fuel is burned
            total += calc_stint_time(curr_tire, stint_laps, base, temp, curr_lap)
            total += pit_time
            curr_lap = stop['lap'] + 1
            curr_tire = stop['to_tire']
            
        final_laps = config['total_laps'] - curr_lap + 1
        total += calc_stint_time(curr_tire, final_laps, base, temp, curr_lap)
        
        results.append((total, driver))
    
    # Sort strictly by total time. 
    results.sort(key=lambda x: (x[0], x[1]))
    
    output = {
        'race_id': test_case['race_id'], 
        'finishing_positions': [r[1] for r in results]
    }
    
    print(json.dumps(output))

if __name__ == '__main__':
    main()