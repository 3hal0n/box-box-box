import json

def main():
    with open('data/test_cases/inputs/test_001.json', 'r') as f:
        data = json.load(f)
        
    print("=== RACE CONFIG ===")
    print(json.dumps(data['race_config'], indent=2))
    
    print("\n=== THE TIED DRIVERS ===")
    targets = ['pos6', 'pos18', 'pos3', 'pos9'] # D006, D018, D003, D009
    
    for pos in targets:
        if pos in data['strategies']:
            print(f"\n{pos.upper()}:")
            print(json.dumps(data['strategies'][pos], indent=2))

if __name__ == '__main__':
    main()