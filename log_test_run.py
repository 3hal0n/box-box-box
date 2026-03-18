import os
import subprocess
import json
from pathlib import Path

# --- Configuration ---
TEST_CASES_DIR = Path("data/test_cases/inputs")
EXPECTED_OUTPUTS_DIR = Path("data/test_cases/expected_outputs")
RUN_COMMAND_FILE = Path("solution/run_command.txt")
LOG_DIR = Path("logs/failed_tests")

# Colors
RED, GREEN, YELLOW, BLUE, NC = '\033[0;31m', '\033[0;32m', '\033[1;33m', '\033[0;34m', '\033[0m'

def print_header(text):
    print(f"{BLUE}╔" + "═" * 56 + "╗")
    print(f"║ {text:^54} ║")
    print(f"╚" + "═" * 56 + "╝{NC}")

def main():
    if not RUN_COMMAND_FILE.exists():
        print(f"{RED}Error: Run command file not found: {RUN_COMMAND_FILE}{NC}")
        return

    with open(RUN_COMMAND_FILE, 'r') as f:
        solution_cmd = f.read().strip()

    if not TEST_CASES_DIR.exists():
        print(f"{RED}Error: Test cases directory not found: {TEST_CASES_DIR}{NC}")
        return

    test_files = sorted(list(TEST_CASES_DIR.glob("test_*.json")))
    total_tests = len(test_files)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    print_header("Box Box Box - Test Runner")
    print(f"Solution Command: {YELLOW}{solution_cmd}{NC}")
    print(f"Test Cases Found: {YELLOW}{total_tests}{NC}\n")

    passed, failed, errors = 0, 0, 0
    has_answers = EXPECTED_OUTPUTS_DIR.exists()

    for test_path in test_files:
        test_name = test_path.stem
        test_id = test_name.replace("test_", "TEST_")

        try:
            with open(test_path, 'r') as f_in:
                input_data = f_in.read()

            process = subprocess.Popen(
                solution_cmd, shell=True, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            stdout, stderr = process.communicate(input=input_data)

            if process.returncode != 0:
                print(f"{RED}✗{NC} {test_id} - Execution error")
                errors += 1
                continue

            try:
                actual_json = json.loads(stdout)
                predicted = actual_json.get("finishing_positions", [])
                
                answer_file = EXPECTED_OUTPUTS_DIR / f"{test_name}.json"
                if has_answers and answer_file.exists():
                    with open(answer_file, 'r') as f_ans:
                        expected_json = json.load(f_ans)
                        expected = expected_json.get("finishing_positions", [])

                    if predicted == expected:
                        print(f"{GREEN}✓{NC} {test_id}")
                        passed += 1
                    else:
                        print(f"{RED}✗{NC} {test_id} - Incorrect prediction")
                        # --- DIFF SECTION ---
                        print(f"    {BLUE}Expected:{NC} {expected}")
                        print(f"    {RED}Actual:  {NC} {predicted}")
                        
                        # Save log for deep dive
                        log_path = LOG_DIR / f"{test_name}_fail.json"
                        with open(log_path, 'w') as f_log:
                            json.dump({"expected": expected, "actual": predicted}, f_log, indent=4)
                        failed += 1
                else:
                    print(f"{YELLOW}?{NC} {test_id} - Output generated (no answer key)")
                    passed += 1

            except json.JSONDecodeError:
                print(f"{RED}✗{NC} {test_id} - Invalid JSON output")
                failed += 1

        except Exception as e:
            print(f"{RED}✗{NC} {test_id} - System error: {e}")
            errors += 1

    # Results Summary
    print_header("Results")
    pass_rate = (passed * 100 / total_tests) if total_tests > 0 else 0
    print(f"Total: {total_tests} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
    print(f"Pass Rate: {pass_rate:.1f}%")

if __name__ == "__main__":
    main()