import fitz
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap
import re
import requests
from datetime import datetime, timedelta
import numpy as np

def extract_text_from_pdf(path):
    doc = fitz.open(path)
    return "\n".join([page.get_text() for page in doc])

def extract_tasks(text):
    pattern = r"([A-Za-z]{3} \d{1,2}, \d{4})\s+\s+(.*?)\n"
    matches = re.findall(pattern, text)

    tasks = []
    for date_str, task in matches:
        try:
            date = datetime.strptime(date_str.strip(), "%b %d, %Y").date()
            tasks.append((task.strip(), date))
        except:
            continue
    return tasks

def break_down_task(task, due, sub_steps=None):
    if sub_steps is None:
        sub_steps = ["Research", "Draft", "Revise", "Submit"]

    num_subtasks = len(sub_steps)
    start_date = due - timedelta(days=num_subtasks * 2)
    schedule_days = pd.date_range(start=start_date, end=due).to_list()

    if len(schedule_days) < num_subtasks:
        schedule_days = [due - timedelta(days=i) for i in range(num_subtasks)][::-1]

    step = max(1, len(schedule_days) // num_subtasks)
    chosen_days = schedule_days[::step][:num_subtasks]

    subtasks = []
    for step_name, date in zip(sub_steps, chosen_days):
        subtasks.append((f"{step_name}: {task}", date.strftime("%Y-%m-%d")))
    return subtasks

def send_to_todoist(subtasks, token):
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://api.todoist.com/rest/v2/tasks"
    for name, due in subtasks:
        data = {"content": name, "due_date": due}
        requests.post(url, json=data, headers=headers)

def generate_heatmap(subtasks):
    if not subtasks:
        print(" No tasks to plot.")
        return

    df = pd.DataFrame(subtasks, columns=["Task", "Date"])
    df["Date"] = pd.to_datetime(df["Date"])
    df["Count"] = 1

    full_range = pd.date_range(start=df["Date"].min(), end=df["Date"].max())
    full_df = pd.DataFrame({"Date": full_range})
    full_df = full_df.merge(df.groupby("Date")["Count"].sum().reset_index(), on="Date", how="left").fillna(0)

    cmap = LinearSegmentedColormap.from_list("task_load", ["#ffffcc", "#ffcc66", "#ff3300"], N=256)

    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(full_df["Date"], full_df["Count"], color=cmap(full_df["Count"] / full_df["Count"].max()))

    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    plt.xticks(rotation=45)

    plt.title(" ClassRadar - Workload Heatmap", fontsize=14)
    plt.ylabel("Tasks per Day")
    plt.xlabel("Date")
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig("static/heatmap.png")
    plt.close()

def process_pdf_and_generate_output(pdf_path, token):
    text = extract_text_from_pdf(pdf_path)
    tasks = extract_tasks(text)

    if not tasks:
        return []

    all_subtasks = []
    for task, due in tasks:
        all_subtasks += break_down_task(task, due)

    generate_heatmap(all_subtasks)
    send_to_todoist(all_subtasks, token)
    return all_subtasks
