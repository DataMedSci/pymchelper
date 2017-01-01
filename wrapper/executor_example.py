"""
To run example, you have to be in main directory of project (if-shieldide).
Then:
python3.4 -m modules.runner.executor_example input_files_path shield_hit_path
"""

import modules.runner.executor as executor
import sys

def run_example():
    default_input_files = "examples/simple"
    default_shield_hit = "shieldhit"

    if len(sys.argv) == 3:
        input_files = sys.argv[1]
        shield_hit = sys.argv[2]
    else:
        print("You can give in input_files and shield-hit paths like that: ")
        print("python3.4 -m modules.runner.executor_example input_files_path shield_hit_path")
        input_files = default_input_files
        shield_hit = default_shield_hit


    s = executor.Shield(input_files, shield_hit)
    s.run()

    print("Communicates:")
    last_communicate = ""
    while s.status != executor.Shield.FAILED_STATUS and s.status != executor.Shield.FINISHED_STATUS:
        if s.communicate != last_communicate:
            last_communicate = s.communicate
            print(last_communicate)


    print("Output: " + s.output)
    print("Status:  " + s.status)

    print("Stderr")
    print(s.stderr)

    print("Special lines")
    print(s.special_lines)


if __name__ == '__main__':
    run_example()

