#!/usr/bin/env python3
"""
Box Box Box - F1 Race Simulator (Optimized 63% Version)
"""

import json
import sys

# ==============================================================================
# CONFIGURATION 
# ==============================================================================

# High-Precision Optimized Parameters
TIRE_OFFSET = {
    'SOFT': -1.0164688925415162,
    'MEDIUM': 0.0,
    'HARD': 0.8083559033446268
}

DEGRADATION_RATE = {
    'SOFT': 1.7721437781975329,
    'MEDIUM': 0.9020411535879727,
    'HARD': 0.45965552833668016
}

FLAT_PERIOD = {
    'SOFT': 10.129535541186053,
    'MEDIUM': 20.077035296627418,
    'HARD': 30.07214783623455
}

# Thermal Sensitivity
TEMP_ORIGIN = 25.32291967111835
TEMP_MULT = 0.015758278987604856

# Power-Law Wear Exponent
WEAR_POWER = 0.9535525170945268

def get_temp_multiplier(temp):
    return 1.0 + (temp - TEMP_ORIGIN) * TEMP_MULT

# ==============================================================================
# LAP TIME PREDICTION
# ==============================================================================

def calculate_lap_time(base_lap_time, tire_compound, tire_age, temperature):
    """
    Calculate lap time using power-law degradation
    """
    effective_age = max(0.0, tire_age - FLAT_PERIOD[tire_compound])
    wear_effect = (effective_age ** WEAR_POWER)

    base_speed = base_lap_time + TIRE_OFFSET[tire_compound]
    temp_effect = get_temp_multiplier(temperature)

    degradation = DEGRADATION_RATE[tire_compound] * wear_effect * temp_effect
    lap_time = base_speed + degradation
    return lap_time

# ==============================================================================
# RACE SIMULATION
# ==============================================================================

def simulate_driver(driver_id, strategy, race_config):
    total_laps = race_config['total_laps']
    base_lap_time = race_config['base_lap_time']
    pit_lane_time = race_config['pit_lane_time']
    temperature = race_config['track_temp']

    total_time = 0.0
    current_tire = strategy['starting_tire']
    tire_age = 0
    pit_stops = {ps['lap']: ps['to_tire'] for ps in strategy['pit_stops']}

    for lap in range(1, total_laps + 1):
        tire_age += 1

        lap_time = calculate_lap_time(base_lap_time, current_tire, tire_age, temperature)
        total_time += lap_time

        if lap in pit_stops:
            total_time += pit_lane_time
            current_tire = pit_stops[lap]
            tire_age = 0

    return total_time

def simulate_race(race_config, strategies):
    results = []

    for position_key, strategy in strategies.items():
        driver_id = strategy['driver_id']
        grid_pos = int(position_key.replace('pos', ''))
        total_time = simulate_driver(driver_id, strategy, race_config)
        results.append((driver_id, total_time, grid_pos))

    # Sort by total time (primary) and grid position (tie-breaker Regulation 2.08)
    results.sort(key=lambda x: (x[1], x[2]))
    return [driver_id for driver_id, _, _ in results][:20]

# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data:
            return
        data = json.loads(input_data)
    except (json.JSONDecodeError, EOFError):
        return

    races = data if isinstance(data, list) else [data]

    outputs = []
    for race in races:
        race_id = race['race_id']
        positions = simulate_race(race['race_config'], race['strategies'])
        outputs.append({
            'race_id': race_id,
            'finishing_positions': positions
        })

    if isinstance(data, dict):
        print(json.dumps(outputs[0]))
    else:
        print(json.dumps(outputs))

if __name__ == '__main__':
    main()