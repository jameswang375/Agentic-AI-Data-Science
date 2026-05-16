#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from data_science_crew.crew import DataScienceCrew, STEPS
from data_science_crew import progress

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information



def run(*, dataset_path: str, base_url: str, run_dir: str = ".", emit=None):
    """
    Run the full CrewAI data science pipeline for a dataset.
    All outputs are scoped to run_dir for per-run isolation.
    If emit is provided, progress events are pushed to it as the pipeline runs.
    """
    from pathlib import Path

    run_path = Path(run_dir)
    cleaned_dataset_path = str(run_path / "data" / "cleaned.csv")
    plots_dir = str(run_path / "reports" / "plots")
    report_path = run_path / "reports" / "insights_report.md"

    (run_path / "data").mkdir(parents=True, exist_ok=True)
    (run_path / "reports").mkdir(parents=True, exist_ok=True)

    if emit:
        progress.setup(emit)
        progress.emit({"type": "task_started", "task": STEPS[0], "index": 0})

    try:
        result = DataScienceCrew().crew().kickoff(
            inputs={
                "dataset_path": dataset_path,
                "cleaned_dataset_path": cleaned_dataset_path,
                "plots_dir": plots_dir,
                "base_url": base_url,
            }
        )
        report_path.write_text(result.raw)
    finally:
        progress.teardown()

def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        DataScienceCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        DataScienceCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        DataScienceCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = DataScienceCrew().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
    

if __name__ == "__main__":
    run()

