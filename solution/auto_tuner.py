import json
import random
import copy

def load_data():
    with open("data/historical_races/races_00000-00999.json", "r") as f:
        return json.load(f)[:150] # Use 150 races to train quickly

def simulate(race, params):
    config = race["race_config"]
    strategies = race["strategies"]
    blt = float(config["base_lap_time"])
    plt = float(config["pit_lane_time"])
    laps = int(config["total_laps"])
    temp = float(config["track_temp"])
    
    times = {}
    for pos_key, driver_data in strategies.items():
        d_id = driver_data["driver_id"]
        c_tire = driver_data["starting_tire"]
        stops = {int(s["lap"]): s["to_tire"] for s in driver_data.get("pit_stops", [])}
        
        t_time = 0.0
        age = 0
        for lap in range(1, laps + 1):
            age += 1
            p = params[c_tire]
            deg = (p["deg_rate"] + (p["temp_multiplier"] * temp)) * age
            t_time += blt + p["offset"] + deg
            if lap in stops:
                t_time += plt
                c_tire = stops[lap]
                age = 0
        times[d_id] = t_time
    return times

def score_params(params, races):
    total_score = 0
    for race in races:
        times = simulate(race, params)
        expected = race["finishing_positions"]
        
        # Count how many pairwise driver finishes are predicted correctly
        correct = 0
        total = 0
        for i in range(len(expected)):
            for j in range(i + 1, len(expected)):
                total += 1
                if times[expected[i]] < times[expected[j]]:
                    correct += 1
        total_score += (correct / total)
    return total_score / len(races)

def main():
    print("Loading historical data... Please wait 1-2 minutes.")
    races = load_data()
    
    current_params = {
        "SOFT":   {"offset": -1.2, "deg_rate": 0.08, "temp_multiplier": 0.002},
        "MEDIUM": {"offset": 0.0,  "deg_rate": 0.05, "temp_multiplier": 0.001},
        "HARD":   {"offset": 1.0,  "deg_rate": 0.02, "temp_multiplier": 0.0005}
    }
    
    current_score = score_params(current_params, races)
    print(f"Initial Baseline Accuracy: {current_score * 100:.2f}%")
    
    # Hill Climbing Algorithm to find the exact numbers
    for i in range(1500):
        test_params = copy.deepcopy(current_params)
        
        # Pick a random tire and parameter to tweak
        tire = random.choice(["SOFT", "MEDIUM", "HARD"])
        key = random.choice(["offset", "deg_rate", "temp_multiplier"])
        
        # Make a tiny adjustment
        adjustment = random.uniform(-0.05, 0.05) if key == "offset" else random.uniform(-0.005, 0.005)
        test_params[tire][key] += adjustment
        
        test_score = score_params(test_params, races)
        
        if test_score > current_score:
            current_params = test_params
            current_score = test_score
            print(f"Iteration {i} | Improved Accuracy: {current_score * 100:.2f}%")
            
            if current_score >= 0.999:
                break

    print("\n" + "="*50)
    print("FINISHED! Replace the TIRE_PARAMS in race_simulator.py with this:\n")
    print(json.dumps(current_params, indent=4))
    print("="*50)

if __name__ == '__main__':
    main()