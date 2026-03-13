import sys
import json

PARAMS = {
    "temp_coef": 0.11312339393095705,
    "SOFT": {
        "offset": 2.897605426647028,
        "cliff": 10,
        "deg": 0.39414075006187815
    },
    "MEDIUM": {
        "offset": 3.9137542461417434,
        "cliff": 20,
        "deg": 0.2002385548577139
    },
    "HARD": {
        "offset": 4.724184576079007,
        "cliff": 30,
        "deg": 0.10104690571020632
    }
}

def calc_stint_time(tire_name, laps, base_time, temp):
    if laps <= 0: 
        return 0.0
        
    tire = PARAMS[tire_name]
    lap_speed = base_time + tire["offset"]
    
    actual_deg = tire["deg"] * (1.0 + temp * PARAMS["temp_coef"])
    total_stint_time = laps * lap_speed
    
    # Arithmetic Progression (The True Physics Engine)
    if laps > tire["cliff"]:
        n = laps - tire["cliff"]
        total_stint_time += actual_deg * (n * (n + 1)) / 2.0
        
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
    
    results.sort(key=lambda x: (round(x[0], 5), x[1]))
    
    output = {
        'race_id': test_case['race_id'], 
        'finishing_positions': [r[1] for r in results]
    }
    
    print(json.dumps(output))

if __name__ == '__main__':
    main()