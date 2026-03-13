import json
import random

def load_data():
    with open("data/historical_races/races_00000-00999.json", "r") as f:
        return json.load(f)[:200] # 200 races for absolute precision

def simulate(race, p):
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
            if c_tire == "SOFT":
                off, cliff, deg, tfac, dcurve = p[0], int(p[1]), p[2], p[3], p[4]
            elif c_tire == "MEDIUM":
                off, cliff, deg, tfac, dcurve = p[5], int(p[6]), p[7], p[8], p[9]
            else:
                off, cliff, deg, tfac, dcurve = p[10], int(p[11]), p[12], p[13], p[14]
            
            # The Universal Exponential Physics Model
            deg_laps = max(0, age - cliff)
            degradation = (deg + (temp * tfac)) * (deg_laps ** dcurve)
            
            t_time += blt + off + degradation
            if lap in stops:
                t_time += plt
                c_tire = stops[lap]
                age = 0
        times[d_id] = t_time
    return times

def score_params(p, races):
    correct_pairs = 0
    total_pairs = 0
    perfect_races = 0
    
    for race in races:
        times = simulate(race, p)
        expected = race["finishing_positions"]
        
        race_correct = 0
        race_total = 0
        for i in range(len(expected)):
            for j in range(i + 1, len(expected)):
                race_total += 1
                if times[expected[i]] < times[expected[j]]:
                    race_correct += 1
                    
        correct_pairs += race_correct
        total_pairs += race_total
        if race_correct == race_total:
            perfect_races += 1
            
    # Maximize pairwise accuracy, but give a massive bonus for perfect sequences
    return (correct_pairs / total_pairs) + (perfect_races * 2.0), perfect_races

def main():
    print("Unleashing the Particle Swarm Optimizer...")
    races = load_data()
    
    # 15-Dimensional Search Space: (offset, cliff, deg_rate, temp_factor, deg_curve)
    bounds = [
        (-2.5, 0.0), (1, 15), (0.01, 0.2), (0.0, 0.02), (0.8, 2.5), # SOFT
        (-1.0, 1.0), (5, 25), (0.01, 0.1), (0.0, 0.02), (0.8, 2.5), # MEDIUM
        (0.0, 2.5), (10, 35), (0.001, 0.05), (0.0, 0.02), (0.8, 2.5) # HARD
    ]
    
    num_particles = 40
    num_iterations = 250
    
    particles = []
    velocities = []
    pbest = []
    pbest_scores = []
    
    gbest = None
    gbest_score = -1.0
    gbest_perfects = 0
    
    for _ in range(num_particles):
        pos = [random.uniform(b[0], b[1]) for b in bounds]
        particles.append(pos)
        velocities.append([0.0] * 15)
        pbest.append(list(pos))
        
        score, perfects = score_params(pos, races)
        pbest_scores.append(score)
        
        if score > gbest_score:
            gbest_score = score
            gbest = list(pos)
            gbest_perfects = perfects
            
    w = 0.7   # Inertia (maintains momentum over cliffs)
    c1 = 1.5  # Cognitive (remembers personal bests)
    c2 = 1.5  # Social (swarms toward the global best)
    
    for i in range(num_iterations):
        for j in range(num_particles):
            for k in range(15):
                r1, r2 = random.random(), random.random()
                velocities[j][k] = (w * velocities[j][k] + 
                                    c1 * r1 * (pbest[j][k] - particles[j][k]) + 
                                    c2 * r2 * (gbest[k] - particles[j][k]))
                particles[j][k] += velocities[j][k]
                particles[j][k] = max(bounds[k][0], min(bounds[k][1], particles[j][k]))
                
            score, perfects = score_params(particles[j], races)
            if score > pbest_scores[j]:
                pbest[j] = list(particles[j])
                pbest_scores[j] = score
                if score > gbest_score:
                    gbest = list(particles[j])
                    gbest_score = score
                    gbest_perfects = perfects
                    print(f"Iteration {i} | Swarm Metric: {gbest_score:.4f} | Perfect Races: {gbest_perfects}/200")
                    
                    if gbest_perfects == 200:
                        break
        if gbest_perfects == 200:
            break

    print("\n" + "="*50)
    print("FINISHED! Paste this into race_simulator.py:\n")
    out_json = {
        "SOFT":   {"offset": gbest[0], "cliff": int(gbest[1]), "deg_rate": gbest[2], "temp_factor": gbest[3], "deg_curve": gbest[4]},
        "MEDIUM": {"offset": gbest[5], "cliff": int(gbest[6]), "deg_rate": gbest[7], "temp_factor": gbest[8], "deg_curve": gbest[9]},
        "HARD":   {"offset": gbest[10], "cliff": int(gbest[11]), "deg_rate": gbest[12], "temp_factor": gbest[13], "deg_curve": gbest[14]}
    }
    print(json.dumps(out_json, indent=4))
    print("="*50)

if __name__ == '__main__':
    main()