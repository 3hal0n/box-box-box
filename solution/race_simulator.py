#!/usr/bin/env python3
import json
import sys
# Tried a One More Physics Based Constant to Achieve 56%
# Tuning the parameters currently 
# ==============================================================
# 60% MILESTONE PARAMETERS (Rank Error: 202)
# ==============================================================
PARAMS = {
    "SOFT": {
        "offset": 2.958962002059359, 
        "cliff": 10, 
        "deg": 0.3938052242423563
    }, 
    "MEDIUM": {
        "offset": 3.9262504324101357, 
        "cliff": 20, 
        "deg": 0.2005977212786465
    }, 
    "HARD": {
        "offset": 4.7244861975727845, 
        "cliff": 30, 
        "deg": 0.10319025698674321
    }, 
    "temp_coef": 0.112095, 
    "evol": 0.00010257806706596489
}
def calc_stint_time(tire_name, laps, base_time, temp, start_lap):
    """
    Iterates through each lap to account for the linear fuel burn (evol).
    """
    if laps <= 0:
        return 0.0, 0.0
        
    tire = PARAMS[tire_name]
    actual_deg = tire["deg"] * (1.0 + temp * PARAMS["temp_coef"])
    total_stint_time = 0.0
    last_lap_time = 0.0
    
    for i in range(laps):
        # Current absolute lap in the race (1, 2, 3...)
        current_abs_lap = start_lap + i
        
        # Physics: Base + Offset - (Fuel Burn * Current Lap)
        lap_time = base_time + tire["offset"] - (PARAMS['evol'] * current_abs_lap)
        
        # Add degradation if beyond the cliff
        laps_on_this_tire = i + 1
        if laps_on_this_tire > tire["cliff"]:
            lap_time += (laps_on_this_tire - tire["cliff"]) * actual_deg
            
        total_stint_time += lap_time
        last_lap_time = lap_time
        
    return total_stint_time, last_lap_time

def main():
    # Read STDIN
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

    for strategy in test_case['strategies'].values():
        driver = strategy['driver_id']
        pit_stops = sorted(strategy.get('pit_stops', []), key=lambda x: int(x['lap']))

        total = 0.0
        curr_lap = 1
        curr_tire = strategy['starting_tire']
        final_lap_val = 0.0

        # Calculate each stint + pit stop
        for stop in pit_stops:
            stint_laps = stop['lap'] - curr_lap + 1
            s_time, l_lap = calc_stint_time(curr_tire, stint_laps, base, temp, curr_lap)
            
            total += s_time
            total += pit_time
            
            final_lap_val = l_lap
            curr_lap = stop['lap'] + 1
            curr_tire = stop['to_tire']

        # Final stint to the flag
        final_laps = config['total_laps'] - curr_lap + 1
        s_time, l_lap = calc_stint_time(curr_tire, final_laps, base, temp, curr_lap)
        
        total += s_time
        final_lap_val = l_lap

        # Store for sorting: (Total Time, Last Lap Tie-Breaker, Driver ID)
        results.append((total, final_lap_val, driver))

    # Sort by total time, then last lap time, then driver ID
    results.sort(key=lambda x: (x[0], x[1], x[2]))

    output = {
        'race_id': test_case['race_id'],
        'finishing_positions': [r[2] for r in results]
    }

    print(json.dumps(output))

if __name__ == '__main__':
    main()