import json
import sys
import math

# ---------------------------------------------------------
# CURRENT BEST PHYSICS PARAMETERS (39% Baseline)
# ---------------------------------------------------------
PARAMS = {
      'SOFT':   {'offset': 2.959679, 'cliff': 10, 'deg': 0.393913, 'warmup': 0.0},
      'MEDIUM': {'offset': 3.928766, 'cliff': 20, 'deg': 0.200049, 'warmup': 0.0},
      'HARD':   {'offset': 4.726468, 'cliff': 30, 'deg': 0.101575, 'warmup': 0.0},
      'temp_coef': 0.112732
}

def calc_stint_time(tire_name, laps, base_time, temp):
    if laps <= 0: 
        return 0.0
        
    tire = PARAMS[tire_name]
    lap_speed = base_time + tire["offset"]
    actual_deg = tire["deg"] * (1.0 + temp * PARAMS["temp_coef"])
    
    total_stint_time = 0.0
    
    # Calculate lap-by-lap to simulate F1 Timing Systems exactly
    for lap_of_stint in range(1, laps + 1):
        current_lap_time = lap_speed
        
        # 1. Warm-up penalty (Only applies to the 1st lap on new tires)
        if lap_of_stint == 1:
            current_lap_time += tire['warmup']
            
        # 2. Degradation penalty (Only applies after the cliff)
        if lap_of_stint > tire["cliff"]:
            n = lap_of_stint - tire["cliff"]
            current_lap_time += (actual_deg * n)
            
        # 3. Lap-by-Lap F1 Truncation (Rounds to 3 decimal places per lap)
        # Using round(..., 3) simulates how an F1 timing beam records the time
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
            total += calc_stint_time(curr_tire, stint_laps, base, temp)
            total += pit_time
            curr_lap = stop['lap'] + 1
            curr_tire = stop['to_tire']
            
        final_laps = config['total_laps'] - curr_lap + 1
        total += calc_stint_time(curr_tire, final_laps, base, temp)
        
        results.append((total, driver))
    
    # Sort strictly by total time. 
    # Because we already rounded lap-by-lap, we use the exact sum here.
    results.sort(key=lambda x: (x[0], x[1]))
    
    output = {
        'race_id': test_case['race_id'], 
        'finishing_positions': [r[1] for r in results]
    }
    
    print(json.dumps(output))

if __name__ == '__main__':
    main()