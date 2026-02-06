from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from data_science_crew.tools.custom_tool import (
    DatasetProfilingTool,
    MinimalWranglingExecutionTool,
    EDAExecutionTool
)

from typing import List
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class DataScienceCrew():
    """DataScienceCrew crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools


    @agent
    def data_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["data_engineer"],  # type: ignore[index]
            verbose=False,
            memory=False
        )


    @agent
    def eda_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["eda_analyst"],  # type: ignore[index]
            verbose=False,
            memory=False
        )
    
    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["reporting_analyst"],  # type: ignore[index]
            verbose=False,
            memory=False
        )
    


    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task

# ---------------- TASKS ----------------

    @task
    def wrangling_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config["minimal_wrangling_plan_task"],  # type: ignore[index]
            agent=self.data_engineer(),
            
        )

    
    @task
    def wrangling_execution_task(self) -> Task:
        return Task(
            config=self.tasks_config["minimal_wrangling_execution_task"],  # type: ignore[index]
            agent=self.data_engineer(),
            tools=[MinimalWranglingExecutionTool()],
        )
    

    @task
    def data_profiling_task(self) -> Task:
        return Task(
            config=self.tasks_config["dataset_profiling_task"],  # type: ignore[index]
            agent=self.data_engineer(),
            tools=[DatasetProfilingTool()]
        )


    @task
    def eda_planning(self) -> Task:
        return Task(
            config=self.tasks_config["eda_planning_task"],  # type: ignore[index]
            agent=self.eda_analyst(),
        )
    
    @task
    def eda_execution(self) -> Task:
        return Task(
            config=self.tasks_config["eda_execution_task"],  # type: ignore[index]
            agent=self.eda_analyst(),
            tools=[EDAExecutionTool()],
        )

    @task
    def insight_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config["insights_report_task"],  # type: ignore[index]
            agent=self.reporting_analyst(),
        )




    @crew
    def crew(self) -> Crew:
        """Creates the DataScienceCrew crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
