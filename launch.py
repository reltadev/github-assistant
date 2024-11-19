import subprocess
import sys
import os
import argparse
from concurrent.futures import ThreadPoolExecutor
import inquirer

def prompt_for_refresh():
    questions = [
        inquirer.Confirm('refresh',
                        message="Existing GitHub data found. Do you want to refresh it?",
                        default=False),
    ]
    answers = inquirer.prompt(questions)
    return answers['refresh'] if answers else False

def run_command(command, cwd=None, env=None):
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=cwd,
        env=env,
    )
    for line in process.stdout:
        print(line, end="")
    process.wait()

def main():
    parser = argparse.ArgumentParser(
        description="Launch client and server with optional RELTA_SOURCE."
    )
    parser.add_argument(
        "--relta-source", help="Set the RELTA_SOURCE environment variable"
    )
    parser.add_argument(
        "--force-refresh", 
        action="store_true",
        help="Force refresh of GitHub data"
    )
    args = parser.parse_args()

    env = os.environ.copy()
    if args.relta_source:
        env["RELTA_SOURCE"] = args.relta_source

    # Check if data exists and prompt for refresh
    if os.path.exists('server-poc/data/github_issues.duckdb') and not args.force_refresh:
        should_refresh = prompt_for_refresh()
        if should_refresh:
            env["FORCE_REFRESH"] = "1"

    commands = [
        ("npm install && npm run dev", "client-poc"),
        ("uvicorn server_poc.server:app --reload", "server-poc"),
    ]

    with ThreadPoolExecutor(max_workers=len(commands)) as executor:
        futures = [executor.submit(run_command, cmd, cwd, env) for cmd, cwd in commands]

        for future in futures:
            try:
                future.result()
            except KeyboardInterrupt:
                print("\nStopping all processes...")
                sys.exit(0)

if __name__ == "__main__":
    main()
