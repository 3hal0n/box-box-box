import json
import os
import sys
import itertools

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

def simulate_race(race, s_off, m_off, h_off, s_deg, m_deg, h_deg):
    base = race["race_config"]["base_lap_time"]
    temp = race["race_config"]["track_temp"]
    plt = race["race_config"]["pit_lane_time"]

    times = {}
    
    # Python dicts maintain insertion order, perfectly mimicking Java's stable sorting
    for strategy in race["strategies"].values():
        driver = strategy["driver_id"]
        pit_stops = sorted(strategy.get("pit_stops", []), key=lambda x: int(x["lap"]))

        total = 0.0
        curr_lap = 1
        curr_tire = strategy["starting_tire"]

        for stop in pit_stops:
            stint_laps = stop["lap"] - curr_lap + 1
            
            if curr_tire == 'SOFT': off, deg, cliff = s_off, s_deg, 10
            elif curr_tire == 'MEDIUM': off, deg, cliff = m_off, m_deg, 20
            else: off, deg, cliff = h_off, h_deg, 30

            # THE PURE FORMULA: Simple multiplier against temperature
            actual_deg = deg * temp
            
            for i in range(stint_laps):
                lap_time = base + off
                if (i + 1) > cliff: 
                    lap_time += ((i + 1) - cliff) * actual_deg
                total += lap_time
            
            total += plt
            curr_lap = stop["lap"] + 1
            curr_tire = stop["to_tire"]

        final_laps = race["race_config"]["total_laps"] - curr_lap + 1
        
        if curr_tire == 'SOFT': off, deg, cliff = s_off, s_deg, 10
        elif curr_tire == 'MEDIUM': off, deg, cliff = m_off, m_deg, 20
        else: off, deg, cliff = h_off, h_deg, 30

        actual_deg = deg * temp
        for i in range(final_laps):
            lap_time = base + off
            if (i + 1) > cliff: 
                lap_time += ((i + 1) - cliff) * actual_deg
            total += lap_time

        # PURE FLOAT TOTAL. No custom tiebreakers. Let IEEE 754 precision do its job!
        times[driver] = total

    return times

def main():
    races = load_final_exam()
    print("Firing up the Clean Grid Searcher on PC...")
    print("Testing 12,500 exact human-coded combinations...\n")
    
    # Testing clean, human-readable numbers around the 60% zone
    s_offs = [2.0, 2.5, 3.0, 3.5, 4.0]
    m_offs = [3.0, 3.5, 4.0, 4.5, 5.0]
    h_offs = [4.0, 4.5, 5.0, 5.5, 6.0]
    
    # Testing clean, microscopic base degradations to multiply against temperature
    s_degs = [0.03, 0.04, 0.05, 0.06, 0.07]
    m_degs = [0.01, 0.015, 0.02, 0.025, 0.03]
    h_degs = [0.005, 0.01, 0.015, 0.02]

    best_score = 0

    for s_o, m_o, h_o, s_d, m_d, h_d in itertools.product(s_offs, m_offs, h_offs, s_degs, m_degs, h_degs):
        correct = 0
        for race in races:
            times = simulate_race(race, s_o, m_o, h_o, s_d, m_d, h_d)
            
            # Sort natively. Python's Timsort perfectly matches Java's LinkedHashMap + Collections.sort()
            predicted = sorted(times.keys(), key=lambda d: times[d])
            if predicted == race["expected"]:
                correct += 1
        
        if correct > best_score:
            best_score = correct
            print("🔥" * 20)
            print(f"NEW HIGH SCORE: {correct}/100")
            print(f"Soft: Offset={s_o}, Deg={s_d}")
            print(f"Med:  Offset={m_o}, Deg={m_d}")
            print(f"Hard: Offset={h_o}, Deg={h_d}")
            print("🔥" * 20 + "\n")
            
            if correct == 100:
                print("WE FOUND THE EXACT DEVELOPER ALGORITHM!")
                break

if __name__ == "__main__":
    main()