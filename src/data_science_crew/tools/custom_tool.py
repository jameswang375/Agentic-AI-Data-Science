import pandas as pd
from crewai.tools import BaseTool
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field
import json
import numpy as np
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import re
from pathlib import Path

class DatasetProfilingInput(BaseModel):
    dataset_path: str = Field(
        ..., description="Path to the CSV dataset to profile"
    )


class DatasetProfilingTool(BaseTool):
    name: str = "dataset_profiling"
    description: str = (
        "Profiles a CSV dataset and returns summary statistics "
        "useful for data cleaning and EDA planning."
    )
    args_schema: Type[BaseModel] = DatasetProfilingInput

    def _run(self, dataset_path: str) -> str:
        df = pd.read_csv(dataset_path)

        lines = []
        lines.append("DATASET OVERVIEW")
        lines.append(f"Rows: {df.shape[0]}")
        lines.append(f"Columns: {df.shape[1]}")
        lines.append(f"Duplicate rows: {df.duplicated().sum()}")
        lines.append("")

        lines.append("COLUMN PROFILES")

        for col in df.columns:
            lines.append(f"\nColumn: {col}")
            lines.append(f"Data type: {df[col].dtype}")
            lines.append(
                f"Missing values: {df[col].isna().sum()} "
                f"({df[col].isna().mean() * 100:.2f}%)"
            )
            lines.append(f"Unique values: {df[col].nunique()}")

            if pd.api.types.is_numeric_dtype(df[col]):
                lines.append("Numeric summary:")
                lines.append(df[col].describe().to_string())
            else:
                lines.append("Top categories:")
                lines.append(
                    df[col].value_counts(dropna=True).head(5).to_string()
                )

        return "\n".join(lines)
    




class MinimalWranglingExecutionInput(BaseModel):
    dataset_path: str = Field(
        ..., description="Path to the raw CSV dataset"
    )
    wrangling_plan: str = Field(
        ..., description="JSON string describing the minimal wrangling plan for EDA"
    )
    wrangled_dataset_path: str = Field(
        default="data/cleaned.csv",
        description="Where to save the minimally wrangled dataset"
    )





class MinimalWranglingExecutionTool(BaseTool):
    name: str = "minimal_wrangling_execution"
    description: str = "Executes ONLY the minimal, explicitly approved wrangling steps for EDA."
    args_schema: Type[BaseModel] = MinimalWranglingExecutionInput

    def _run(
        self,
        dataset_path: str,
        wrangling_plan: str,
        wrangled_dataset_path: str,
    ) -> str:

        # ----------------------------
        # LOAD DATA
        # ----------------------------
        try:
            df = pd.read_csv(dataset_path)
        except Exception as e:
            return f"Failed to load dataset at {dataset_path}: {e}"

        # ----------------------------
        # PARSE & VALIDATE PLAN
        # ----------------------------
        try:
            plan: Dict[str, Any] = json.loads(wrangling_plan)

        except Exception as e:
            return f"Invalid minimal wrangling plan: {e}"

        applied_steps: List[str] = []

        # ----------------------------
        # EXECUTE APPROVED STEPS ONLY
        # ----------------------------

        # Strip column names
        strip_column_names = plan.get("strip_column_names", False)
        if strip_column_names:
            original_columns = list(df.columns)
            df.columns = df.columns.astype(str).str.strip()

            if original_columns != list(df.columns):
                applied_steps.append("Stripped whitespace from column names.")

        # Strip string values
        strip_string_values = plan.get("strip_string_values", False)
        if strip_string_values:
            obj_cols = df.select_dtypes(include="object").columns
            for col in obj_cols:
                df[col] = df[col].where(
                    df[col].isna(),
                    df[col].astype(str).str.strip()
                )

            if len(obj_cols) > 0:
                applied_steps.append("Stripped whitespace from string values.")

        # Convert empty strings to NaN
        convert_empty_strings_to_null = plan.get("convert_empty_strings_to_null", False)
        if convert_empty_strings_to_null:
            df.replace(r"^\s*$", np.nan, regex=True, inplace=True)
            applied_steps.append("Converted empty strings to missing values.")

        # Safe numeric coercion
        safe_numeric_coercion = plan.get("safe_numeric_coercion", False)
        if safe_numeric_coercion:
            for col in df.columns:
                if df[col].dtype == object:
                    coerced = pd.to_numeric(df[col], errors="ignore")
                    if coerced.dtype != object:
                        df[col] = coerced
                        applied_steps.append(
                            f"Safely coerced column '{col}' to numeric."
                        )

       # Drop unusable columns (ONLY if explicitly specified)
        drop_columns = plan.get("drop_columns", [])
        if drop_columns:
            existing = [c for c in drop_columns if c in df.columns]
            if existing:
                df.drop(columns=existing, inplace=True)
                for col in existing:
                    applied_steps.append(f"Dropped unusable column '{col}'.")


        # ----------------------------
        # SAVE OUTPUT
        # ----------------------------
        output_dir = os.path.dirname(wrangled_dataset_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        df.to_csv(wrangled_dataset_path, index=False)

        # ----------------------------
        # RETURN EXECUTION REPORT
        # ----------------------------
        return json.dumps(
            {
                "wrangled_dataset_path": wrangled_dataset_path,
                "rows": df.shape[0],
                "columns": df.shape[1],
                "applied_wrangling_steps": applied_steps,
                "final_columns": list(df.columns),
            },
            indent=2,
        )



class EDAExecutionInput(BaseModel):
    dataset_path: str = Field(
        ...,
        description="Path to the minimally wrangled dataset CSV"
    )
    eda_plan: str = Field(
        ...,
        description="EDA plan JSON string generated by the EDA planning task"
    )
    output_dir: str = Field(
        default="reports/plots",
        description="Directory to save generated plot images"
    )
    base_url: str = Field(
        default="http://localhost:10000",
        description="Base URL used to construct image URLs embedded in the report"
    )




def safe_filename(name: str) -> str:
    """
    Sanitize strings so they are safe for filenames.
    """
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)




class EDAExecutionTool(BaseTool):
    name: str = "eda_execution"
    description: str = "Executes an EDA plan and saves visualization images to disk."
    args_schema: Type[BaseModel] = EDAExecutionInput

    def _run(
        self,
        dataset_path: str,
        eda_plan: str,
        output_dir: str = "reports/plots",
        base_url: str = "http://localhost:10000",
    ) -> str:

        # ----------------------------
        # LOAD DATA
        # ----------------------------
        try:
            df = pd.read_csv(dataset_path)
        except Exception as e:
            return f"Failed to load dataset at {dataset_path}: {e}"

        # ----------------------------
        # PARSE & VALIDATE PLAN
        # ----------------------------
        try:
            plan = json.loads(eda_plan)
        except json.JSONDecodeError as e:
            return f"Invalid EDA plan JSON: {e}"

        if not isinstance(plan, dict):
            return "EDA plan must be a JSON object."

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_images: List[str] = []
        warnings: List[str] = []

        # ----------------------------
        # STYLE SETTINGS
        # ----------------------------
        plt.style.use("seaborn-v0_8-whitegrid")
        PRIMARY_COLOR = "#4C72B0"
        SECONDARY_COLOR = "#55A868"

        # ----------------------------
        # UNIVARIATE PLOTS
        # ----------------------------
        for item in plan.get("univariate", []):
            col = item.get("column")
            plot_type = item.get("plot")

            if col not in df.columns:
                warnings.append(f"Column '{col}' not found. Skipped.")
                continue

            plt.figure(figsize=(7, 4.5))

            try:
                if plot_type == "histogram":
                    df[col].dropna().plot(
                        kind="hist",
                        bins=30,
                        color=PRIMARY_COLOR,
                        edgecolor="black",
                        alpha=0.85,
                    )
                    plt.xlabel(col)
                    plt.ylabel("Frequency")


                elif plot_type == "bar":
                    if df[col].nunique() > 20:
                        warnings.append(
                            f"Column '{col}' has high cardinality. Bar plot skipped."
                        )
                        plt.close()
                        continue

                    counts = df[col].value_counts()
                    counts.plot(
                        kind="bar",
                        color=PRIMARY_COLOR,
                        edgecolor="black",
                    )
                    plt.ylabel("Count")
                    plt.xticks(rotation=45, ha="right")

                else:
                    warnings.append(f"Unknown plot type '{plot_type}' for '{col}'.")
                    plt.close()
                    continue

                safe_col = safe_filename(col)
                filename = f"{safe_col}_{plot_type}.png"
                filepath = output_dir / filename

                plt.title(f"{plot_type.title()} of {col}", fontsize=12)
                plt.tight_layout()
                plt.savefig(filepath, dpi=120)
                plt.close()

                # Save Markdown-relative path for the reporting agent
                saved_images.append(f"{base_url.rstrip('/')}/{output_dir}/{filename}")


            except Exception as e:
                plt.close()
                return f"EDA execution failed on column '{col}': {e}"

        # ----------------------------
        # BIVARIATE PLOTS
        # ----------------------------
        for item in plan.get("bivariate", []):
            x = item.get("x")
            y = item.get("y")
            plot_type = item.get("plot")

            if x not in df.columns or y not in df.columns:
                warnings.append(f"Columns '{x}', '{y}' not found. Skipped.")
                continue

            plt.figure(figsize=(7, 4.5))

            try:
                if plot_type == "scatter":
                    plt.scatter(
                        df[x],
                        df[y],
                        alpha=0.6,
                        color=PRIMARY_COLOR,
                        edgecolors="none",
                    )
                    plt.xlabel(x)
                    plt.ylabel(y)


                else:
                    warnings.append(
                        f"Unknown plot type '{plot_type}' for '{x}' vs '{y}'."
                    )
                    plt.close()
                    continue

                safe_x = safe_filename(x)
                safe_y = safe_filename(y)
                filename = f"{safe_x}_{safe_y}_{plot_type}.png"
                filepath = output_dir / filename

                plt.title(f"{plot_type.title()} of {y} by {x}", fontsize=12)
                plt.tight_layout()
                plt.savefig(filepath, dpi=120)
                plt.close()

                # Save Markdown-relative path for reporting
                saved_images.append(f"{base_url.rstrip('/')}/{output_dir}/{filename}")


            except Exception as e:
                plt.close()
                return f"EDA execution failed on '{x}' vs '{y}': {e}"

        # ----------------------------
        # RETURN EXECUTION REPORT
        # ----------------------------
        return json.dumps(
            {
                "eda_output_dir": str(output_dir),
                "images_saved": saved_images,
                "warnings": warnings,
            },
            indent=2,
        )
