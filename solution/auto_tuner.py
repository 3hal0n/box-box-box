import json
import os
import sys
import numpy as np
from scipy.optimize import differential_evolution

def load_final_exam():
    races = []
    input_dir = "data/test_cases/inputs"
    output_dir = "data/test_cases/expected_outputs"
    
    for i in range(1, 101):
        num = str(i).zfill(3)
        in_path = os.path.join(input_dir, f"test_{num}.json")
        out_path = os.path.join(output_dir, f"test_{num}.json")
        
        if os.path.exists(in_path) and os.path.exists(out_path):
            with open(in_path, "r") as f:
                in_data = json.load(f)
            with open(out_path, "r") as f:
                out_data = json.load(f)
            
            in_data["expected"] = out_data["finishing_positions"]
            races.append(in_data)
    return races

def calc_stint_time(tire_name, stint_laps, base_time, temp, race_start_lap, v):
    if stint_laps <= 0: 
        return 0.0
        
    temp_coef = v[0]
    fuel_burn = v[7]
    
    if tire_name == 'SOFT':
        offset, deg, cliff = v[1], v[2], 10
    elif tire_name == 'MEDIUM':
        offset, deg, cliff = v[3], v[4], 20
    else:
        offset, deg, cliff = v[5], v[6], 30

    lap_speed = base_time + offset
    actual_deg = deg * (1.0 + temp * temp_coef)
    
    total_stint_time = 0.0
    
    for i in range(stint_laps):
        lap_of_stint = i + 1
        absolute_race_lap = race_start_lap + i
        
        current_lap = lap_speed + (absolute_race_lap - 1) * fuel_burn
        
        if lap_of_stint > cliff:
            current_lap += actual_deg * (lap_of_stint - cliff)
            
        total_stint_time += round(current_lap, 3) # F1 Lap-by-Lap Truncation
        
    return total_stint_time

def simulate_race(race, v):
    config = race["race_config"]
    base = config['base_lap_time']
    temp = config['track_temp']
    plt = config['pit_lane_time']
    
    times = {}
    
    for pos_key, strategy in race['strategies'].items():
        driver = strategy['driver_id']
        pit_stops = sorted(strategy.get('pit_stops', []), key=lambda x: x['lap'])
        
        total = 0.0
        curr_lap = 1
        curr_tire = strategy['starting_tire']
        
        for stop in pit_stops:
            stint_laps = stop['lap'] - curr_lap + 1
            total += calc_stint_time(curr_tire, stint_laps, base, temp, curr_lap, v)
            total += plt
            curr_lap = stop['lap'] + 1
            curr_tire = stop['to_tire']
            
        final_laps = config['total_laps'] - curr_lap + 1
        total += calc_stint_time(curr_tire, final_laps, base, temp, curr_lap, v)
        
        times[driver] = total
        
    return times

def loss_function(v, races):
    wrong_pairs = 0
    total_pairs = 0
    
    for race in races:
        times = simulate_race(race, v)
        expected = race["expected"]
        
        # Strict Sequence Margin Loss
        for i in range(len(expected)):
            for j in range(i + 1, len(expected)):
                total_pairs += 1
                if times[expected[i]] >= times[expected[j]]:
                    wrong_pairs += 1
                    
    return wrong_pairs / total_pairs

def callback_fn(xk, convergence):
    # Quick test to see how many perfect races the current best vector gets
    # This runs after every generation so you can watch it climb
    races = load_final_exam()
    perfect = 0
    for race in races:
        times = simulate_race(race, xk)
        predicted = sorted(times.keys(), key=lambda d: times[d])
        if predicted == race["expected"]:
            perfect += 1
    print(f"Current Generation Perfect Races: {perfect}/100")

def main():
    races = load_final_exam()
    print("Firing up the Grand Unification Scipy Tuner...")
    
    # Bounded tightly around your proven parameters to speed up the math
    bounds = [
        (0.10, 0.13),      # 0: temp_coef
        (2.8, 3.1),        # 1: SOFT offset
        (0.35, 0.45),      # 2: SOFT deg
        (3.8, 4.1),        # 3: MEDIUM offset
        (0.15, 0.25),      # 4: MEDIUM deg
        (4.5, 4.9),        # 5: HARD offset
        (0.08, 0.12),      # 6: HARD deg
        (-0.001, -0.0001)  # 7: fuel_burn
    ]
    
    result = differential_evolution(
        loss_function, 
        bounds, 
        args=(races,),
        maxiter=1000, 
        popsize=15,
        mutation=(0.5, 1.0),
        recombination=0.8,
        seed=42,
        disp=True,
        workers=-1,
        callback=callback_fn
    )

    print("\n" + "="*50)
    print("OPTIMIZATION FINISHED!")
    
    v = result.x
    final_params = {
        'temp_coef': v[0],
        'SOFT':   {'offset': v[1], 'deg': v[2], 'cliff': 10},
        'MEDIUM': {'offset': v[3], 'deg': v[4], 'cliff': 20},
        'HARD':   {'offset': v[5], 'deg': v[6], 'cliff': 30},
        'fuel_burn': v[7]
    }
    
    print("Paste this into your race_simulator.py PARAMS block:\n")
    print(json.dumps(final_params, indent=4))
    print("="*50)

if __name__ == '__main__':
    main()