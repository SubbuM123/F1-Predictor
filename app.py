import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
import ast
from collections import defaultdict
from sklearn.metrics import r2_score
from scipy.stats import spearmanr
import copy
import importlib
import time
import json
import requests
import unicodedata

import scripts.cleaning as cleaning
import scripts.knn_class as knn_class
import scripts.eval as eval

# completed_race = -1
# point_total = -1

with open('json/predictions.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    completed_race = data["completed race"]
    point_total = data["point total"]

def total_points(data):
    s = 0
    for driver in data:
        s += int(driver["points"])
    return s

def check_new_race(completed_race, point_total):
    url = "https://api.jolpi.ca/ergast/f1/2026/driverStandings.json"

    response = requests.get(url)
    
    data = response.json()["MRData"]["StandingsTable"]

    if int(data["round"]) > completed_race:
        if total_points(data["StandingsLists"][0]["DriverStandings"]) - point_total > 36:
            # completed_race = int(data["round"])
            # print(f"New race detected: {completed_race}")
            return True

    return False

def normalize_name(name):
    return "".join(
        c for c in unicodedata.normalize("NFD", name)
        if unicodedata.category(c) != "Mn"
    )

def update_data():
    url = "https://api.jolpi.ca/ergast/f1/2026/driverStandings.json"

    response = requests.get(url)
    response.raise_for_status()  # Raises an exception if the request failed

    data = response.json()["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"]

    points = {}

    for driver in data:
        points[normalize_name(driver["Driver"]["givenName"][0] + ". " + driver["Driver"]["familyName"])] = int(driver["points"])

    with open('training_data/current_standings.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    for driver, new_total in points.items():
        row = data[driver]

        earned_points = new_total - row["current_points"]

        # p5p
        prev5 = ast.literal_eval(row["prev5_points"])
        prev5 = prev5[1:] + [earned_points]
        row["prev5_points"] = str(prev5)

        # p5a
        row["prev5_points_avg"] = round(sum(ast.literal_eval(row["prev5_points"])) / 5, 2)

        # current points
        row["current_points"] = new_total

        # race number
        row["race_number"] += 1

    leader_points = max(row["current_points"] for row in data.values())

    sorted_drivers = sorted(
        data.items(),
        key=lambda x: x[1]["current_points"],
        reverse=True
    )

    for position, (driver, row) in enumerate(sorted_drivers, start=1):
        row["position"] = position
        row["points_behind_leader"] = leader_points - row["current_points"]
        row["percent_of_max"] = row["current_points"] / leader_points

    json.dump(data, open("training_data/current_standings.json", "w"), indent=4)

def update_predictions(completed_race, year = 2026, year_races = 22, sims = 10000):
    knn_sim = knn_class.KNNSeasonSimulator()
    knn_sim.set_neighbors(year)

    # change this to read json and covert to pandas
    with open('training_data/current_standings.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    df_eval = pd.DataFrame.from_dict(data, orient='index').reset_index().rename(columns={'index': 'driver'})
    df_eval['prev5_points'] = df_eval['prev5_points'].apply(ast.literal_eval)

    all_sims = []
    num_races = year_races
    # print(df_eval)
    df_eval_small = (df_eval[df_eval.race_number == completed_race + 1]).set_index("driver").to_dict(orient='index')
    res = []
    for j in range(sims):
        df_sim = copy.deepcopy(df_eval_small)
        # print(df_sim)
        # print(completed_race)
        df_sim = knn_sim.simulate_season(df_sim, num_races)

        res.append({
            d: df_sim[d]["current_points"]
            for d in df_sim  
        })

    all_sims.append(res)

    data = defaultdict(lambda: defaultdict(int))
    for i in range(sims):
        d = all_sims[0][i]

        sort = dict(sorted(d.items(), key=lambda item: item[1], reverse=True))
        c = 1
        for k,v in sort.items():
            if c == 1:
                data[k]["1st"] += 100 * 1/sims
            if c <= 3:
                data[k]["Podium"] += 100 * 1/sims
            if c <= 5:
                data[k]["Top 5"] += 100 * 1/sims
            if c <= 10:
                data[k]["Top 10"] += 100 * 1/sims
            
            data[k]["points"] += v/sims
            
            c += 1

    url = "https://api.jolpi.ca/ergast/f1/2026/driverStandings.json"

    response = requests.get(url)
    
    data2 = response.json()["MRData"]["StandingsTable"]
    
    data["completed race"] = completed_race + 1
    data["point total"] = total_points(data2["StandingsLists"][0]["DriverStandings"])

    json_string = json.dumps(data, indent=4)
    with open("json/predictions.json", "w") as file:
        file.write(json_string)

if __name__ == "__main__":
    completed_race = -1
    point_total = -1

    with open('json/predictions.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        completed_race = data["completed race"]
        point_total = data["point total"]
    # print(completed_race)

    if check_new_race(completed_race, point_total):
        # print(completed_race)
        update_data()
        update_predictions(completed_race)