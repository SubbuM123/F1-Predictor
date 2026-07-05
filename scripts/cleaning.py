import pandas as pd
import numpy as np

def import_and_clean(filename):
    df = pd.read_csv(filename)

    race_cols = df.columns[2:]
    df[race_cols] = (
        df[race_cols]
        .replace('-', "0")           
        .apply(lambda col: col.str.split('/').str[0])  
        .astype("Float64")                
    )
    df = df.drop(columns=["Pos"])
    df_dict = df.set_index('Driver').to_dict(orient='index')
    return df_dict

def import_and_clean_and_sum(filename):
    df = pd.read_csv(filename)

    race_cols = df.columns[2:]
    df[race_cols] = (
        df[race_cols]
        .replace('-', "0")           
        .apply(lambda col: col.str.split('/').str[0])  
        .astype("Float64")                
    )
    df = df.drop(columns=["Pos"])

    df["Points"] = df.sum(axis = 1, numeric_only=True)
    return df[["Driver", "Points"]]

def format_neighbors(df_dict):
    rows = []

    # Get all race numbers that exist
    all_races = sorted(
        {int(r) for races in df_dict.values() for r in races.keys()}
    )

    # Running championship totals
    cumulative = {driver: 0 for driver in df_dict}

    for race in all_races:
        race_str = str(race)

        # Update cumulative totals after this race
        for driver, races in df_dict.items():
            cumulative[driver] += races.get(race_str, 0)

        leader_points = max(cumulative.values())
        # print(leader_points)

        # Championship positions
        standings = sorted(
            cumulative.items(),
            key=lambda x: x[1],
            reverse=True
        )
        positions = {
            driver: pos + 1
            for pos, (driver, _) in enumerate(standings)
        }

        # Create one row per driver
        for driver, races in df_dict.items():
            prev5 = [
                races.get(str(r), 0)
                for r in range(max(1, race - 5), race)
            ]

            future_results = races.get(str(race + 1), 0)
                # for r in range(race + 1, max(all_races) + 1)
                # for r in range(race + 1, race + 2)
            

            total_points = cumulative[driver]

            rows.append({
                "driver": driver,
                "prev5_avg": sum(prev5) / len(prev5) if prev5 else 0,
                "prev5_points": prev5,
                "points_behind_leader": leader_points - total_points,
                "percent_of_max": total_points / leader_points,
                "position": positions[driver],
                "race_number": race,
                "future_results" : future_results
            })

    df = pd.DataFrame(rows)

    feature_cols = ["prev5_avg", "points_behind_leader", "percent_of_max", "position", "race_number"]

    for col in feature_cols:
        df[col] = (df[col] - df[col].min())/(df[col].max() - df[col].min())

    return df

def format_testing(df_dict):
    rows = []

    # Get all race numbers that exist
    all_races = sorted(
        {int(r) for races in df_dict.values() for r in races.keys()}
    )

    # Running championship totals
    cumulative = {driver: 0 for driver in df_dict}

    for race in all_races:
        race_str = str(race)

        # Update cumulative totals after this race
        for driver, races in df_dict.items():
            cumulative[driver] += races.get(race_str, 0)

        leader_points = max(cumulative.values())

        # Championship positions
        standings = sorted(
            cumulative.items(),
            key=lambda x: x[1],
            reverse=True
        )
        positions = {
            driver: pos + 1
            for pos, (driver, _) in enumerate(standings)
        }

        # Create one row per driver
        for driver, races in df_dict.items():
            prev5 = [
                races.get(str(r), 0)
                for r in range(max(1, race - 5), race)
            ]

            # future_results = [
            #     races.get(str(r), 0)
            #     for r in range(race + 1, max(all_races) + 1)
            # ]

            total_points = cumulative[driver]

            rows.append({
                "driver": driver,
                "prev5_avg": sum(prev5) / len(prev5) if prev5 else 0,
                "prev5_points": prev5,
                "points_behind_leader": leader_points - total_points,
                "current_points": total_points,
                "percent_of_max": total_points / leader_points,
                "position": positions[driver],
                "race_number": race
                # "future_results" : future_results
            })

    df = pd.DataFrame(rows)

    # feature_cols = ["prev5_avg", "points_behind_leader", "percent_of_max", "position", "race_number"]

    # for col in feature_cols:
    #     df[col] = (df[col] - df[col].min())/(df[col].max() - df[col].min())

    return df