import json
import os

# The 41% Parameters
PARAMS = {
    "temp_coef": 0.11209581339306575,
    "SOFT":   {"offset": 2.959679, "deg": 0.393913, "cliff": 10},
    "MEDIUM": {"offset": 3.9286983231419623, "deg": 0.2008786040520899, "cliff": 20},
    "HARD":   {"offset": 4.726468, "deg": 0.101575, "cliff": 30}
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
    test_id = "test_001"
    input_file = f"data/test_cases/inputs/{test_id}.json"
    expected_file = f"data/test_cases/expected_outputs/{test_id}.json"

    if not os.path.exists(input_file):
        print(f"Error: Could not find {input_file}")
        return

    # 1. Run the simulation
    with open(input_file, 'r') as f:
        test_case = json.load(f)

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
            total += calc_stint_time(curr_tire, stint_laps, base, temp)
            total += pit_time
            curr_lap = stop['lap'] + 1
            curr_tire = stop['to_tire']
            
        final_laps = config['total_laps'] - curr_lap + 1
        total += calc_stint_time(curr_tire, final_laps, base, temp)
        
        results.append({
            'driver': driver,
            'time': total,
            'grid_pos': grid_pos
        })

    # Sort by time, then grid pos
    results.sort(key=lambda x: (x['time'], x['grid_pos']))
    predicted_positions = [r['driver'] for r in results]

    # 2. Get expected
    with open(expected_file, 'r') as f:
        expected_data = json.load(f)
        expected_positions = expected_data['finishing_positions']

    # 3. Print the breakdown
    print(f"\n=== DEEP DIVE: {test_id} ===")
    print(f"{'Pos':<4} | {'Expected':<8} | {'Predicted':<9} | {'Match?':<6} | {'Total Time (Calculated)':<25} | {'Grid Pos'}")
    print("-" * 80)
    
    for i in range(len(expected_positions)):
        exp = expected_positions[i]
        act_driver = results[i]['driver']
        act_time = results[i]['time']
        act_grid = results[i]['grid_pos']
        
        match = "✅" if exp == act_driver else "❌"
        
        # Highlight D003 and D009
        if act_driver in ['D003', 'D009']:
            print(f"{i+1:<4} | {exp:<8} | > {act_driver:<7} | {match:<6} | {act_time:<25.8f} | Started P{act_grid}")
        else:
            print(f"{i+1:<4} | {exp:<8} | {act_driver:<9} | {match:<6} | {act_time:<25.8f} | Started P{act_grid}")

if __name__ == '__main__':
    main()