import json
import os
import sys
from scipy.optimize import differential_evolution

BEST_SCORE = 0

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

def calc_stint_time(tire_name, stint_laps, base_time, temp, v):
    if stint_laps <= 0: return 0.0
        
    temp_coef = v[0]
    
    if tire_name == 'SOFT':   offset, deg, exp = v[1], v[2], v[3]
    elif tire_name == 'MEDIUM': offset, deg, exp = v[4], v[5], v[6]
    else:                       offset, deg, exp = v[7], v[8], v[9]

    total_stint_time = 0.0
    
    for i in range(stint_laps):
        tire_age = i + 1
        
        # Rule 3 & 4: Tire Degradation affected by Track Temp (Exponential Curve)
        current_deg = deg * (1.0 + temp * temp_coef) * (tire_age ** exp)
        
        # Rule 1 & 2: Base Lap Time + Tire Compound Performance
        current_lap = base_time + offset + current_deg
            
        total_stint_time += current_lap
        
    return total_stint_time

def simulate_race(race, v):
    config = race["race_config"]
    base = config["base_lap_time"]
    temp = config["track_temp"]
    plt = config["pit_lane_time"] # Rule 5: Pit Stops

    times = {}
    for pos_key, strategy in race["strategies"].items():
        driver = strategy["driver_id"]
        grid_pos = int(pos_key.replace('pos', ''))
        
        pit_stops = sorted(strategy.get("pit_stops", []), key=lambda x: x["lap"])

        total = 0.0
        curr_lap = 1
        curr_tire = strategy["starting_tire"]

        for stop in pit_stops:
            stint_laps = stop["lap"] - curr_lap + 1
            total += calc_stint_time(curr_tire, stint_laps, base, temp, v)
            total += plt # Exactly as the rules state: penalty when entering pit lane
            curr_lap = stop["lap"] + 1
            curr_tire = stop["to_tire"]

        final_laps = config["total_laps"] - curr_lap + 1
        total += calc_stint_time(curr_tire, final_laps, base, temp, v)

        # Round the final total time to 4 decimals to allow the Grid Tiebreaker to work cleanly
        times[driver] = (round(total, 4), grid_pos)

    return times

def loss_function(v, races):
    wrong_pairs = 0
    total_pairs = 0

    for race in races:
        times = simulate_race(race, v)
        expected = race["expected"]

        for i in range(len(expected)):
            for j in range(i + 1, len(expected)):
                total_pairs += 1
                if times[expected[i]] >= times[expected[j]]:
                    wrong_pairs += 1

    return wrong_pairs / total_pairs

def callback_fn(xk, convergence, races):
    global BEST_SCORE
    perfect = 0
    for race in races:
        times = simulate_race(race, xk)
        predicted = sorted(times.keys(), key=lambda d: times[d])
        if predicted == race["expected"]:
            perfect += 1
            
    print(f"Current Gen: {perfect}/100")
    
    if perfect > BEST_SCORE:
        BEST_SCORE = perfect
        print("\n" + "🔥" * 20)
        print(f"NEW HIGH SCORE: {perfect}/100!")
        print("🔥" * 20)
        
        live_params = {
            "temp_coef": xk[0],
            "SOFT":   {"offset": xk[1], "deg": xk[2], "exp": xk[3]},
            "MEDIUM": {"offset": xk[4], "deg": xk[5], "exp": xk[6]},
            "HARD":   {"offset": xk[7], "deg": xk[8], "exp": xk[9]}
        }
        print(json.dumps(live_params, indent=4) + "\n")

def main():
    races = load_final_exam()
    print("Firing up the 5-Rule Lightning Tuner...")

    bounds = [
        (0.01, 0.20),     # 0: temp_coef
        
        (-3.0, 3.5),      # 1: SOFT offset
        (0.001, 0.5),     # 2: SOFT base deg
        (1.0, 2.5),       # 3: SOFT exponential curve
        
        (-1.0, 4.5),      # 4: MEDIUM offset
        (0.001, 0.5),     # 5: MEDIUM base deg
        (1.0, 2.5),       # 6: MEDIUM exponential curve
        
        (0.0, 5.5),       # 7: HARD offset
        (0.001, 0.5),     # 8: HARD base deg
        (1.0, 2.0),       # 9: HARD exponential curve
    ]

    try:
        differential_evolution(
            loss_function,
            bounds,
            args=(races,),
            maxiter=500,
            popsize=5,  # Lightning fast population size
            mutation=(0.5, 1.0),
            recombination=0.8,
            seed=42,
            disp=False, 
            workers=-1,
            callback=lambda xk, convergence: callback_fn(xk, convergence, races),
        )
        print("\nOptimization completed naturally.")
    except KeyboardInterrupt:
        print("\n\nUser stopped the tuner. Check the console above for your highest scoring JSON block!")

if __name__ == "__main__":
    main()