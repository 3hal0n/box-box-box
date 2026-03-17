import json
import sys

# THE "HAMMER" PARAMETERS (Expected ~52% Score)
PARAMS = {
    "temp_coef": 0.03973,
    "SOFT":   {"offset": -2.23057, "deg": 0.80175, "cliff": 10},
    "MEDIUM": {"offset": -1.21587, "deg": 0.40635, "cliff": 20},
    "HARD":   {"offset": -0.39491, "deg": 0.20274, "cliff": 30}
}

def calc_stint_time(tire_name, laps, base_time, temp):
    if laps <= 0: return 0.0
    tire = PARAMS[tire_name]
    lap_speed = base_time + tire["offset"]
    actual_deg = tire["deg"] * (1.0 + temp * PARAMS["temp_coef"])
    total_stint_time = 0.0
    for i in range(laps):
        tire_age = i + 1
        current_lap_time = lap_speed
        if tire_age > tire["cliff"]:
            current_lap_time += actual_deg * (tire_age - tire["cliff"])
        total_stint_time += current_lap_time
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
        grid_pos = int(pos.replace('pos', '')) # TIEBREAKER
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
        results.append((total, grid_pos, driver))
    
    # Sort strictly by time (x[0]), tiebreaker is grid position (x[1])
    results.sort(key=lambda x: (x[0], x[1]))
    
    print(json.dumps({
        'race_id': test_case['race_id'], 
        'finishing_positions': [r[2] for r in results]
    }))

if __name__ == '__main__':
    main()