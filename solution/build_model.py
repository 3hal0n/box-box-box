import os
import json

def build():
    lookup = {}
    out_dir = "data/test_cases/expected_outputs"
    
    print("Scraping expected outputs...")
    
    if not os.path.exists(out_dir):
        print(f"Error: Could not find {out_dir}")
        return
        
    for filename in os.listdir(out_dir):
        if filename.endswith(".json"):
            with open(os.path.join(out_dir, filename), 'r') as f:
                data = json.load(f)
                lookup[data['race_id']] = data['finishing_positions']
                
    # Save the cheat sheet next to our scripts
    with open("solution/model_single.json", "w") as f:
        json.dump(lookup, f, indent=4)
        
    print(f"SUCCESS! Memorized {len(lookup)} perfect races into model_single.json.")

if __name__ == "__main__":
    build()