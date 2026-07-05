import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
import ast
from collections import defaultdict
from sklearn.metrics import r2_score
from scipy.stats import spearmanr
import copy

import scripts.knn_class as knn_class
import importlib

importlib.reload(knn_class)
knn_sim = knn_class.KNNSeasonSimulator()


def metrics(year, all_sims, sims):
    df_actual = pd.read_csv(f"cleaned_data/actual_results_{year}.csv")
    df_actual["Points"] = df_actual["Points"].fillna(0)
    df_actual = df_actual.set_index("Driver").to_dict(orient='index')

    mae = {}
    rmse = {}
    r2 = {}

    mare = {}
    rho = {}

    champion = {}
    champion_in_t3 = {}
    champion_in_t2 = {}

    t3_order = {}
    t3 = {}

    t5_order = {}
    t5 = {}

    t10_order = {}
    t10 = {}

    y_actual = np.array([v["Points"] for v in df_actual.values()])

    actual_ranks = np.array([i for i in range(1, len(y_actual) + 1)])

    for i in range(0, len(all_sims)):
        # for driver in all_sims[i].keys():
        # print(all_sims[i])
        mae_sum = 0
        rmse_sum = 0
        r2_sum = 0

        mare_sum = 0
        rho_sum = 0

        champion_sum = 0
        t3_sum = 0
        t5_sum = 0
        t10_sum = 0
        t3_order_sum = 0
        t5_order_sum = 0
        t10_order_sum = 0

        champion_in_t3_sum = 0
        champion_in_t2_sum = 0

        for j in range(sims):

            y_pred = np.array(list(all_sims[i][j].values()))

            mae_sum += np.mean(np.abs(y_actual - y_pred))
            rmse_sum += np.sqrt(np.mean((y_actual - y_pred)**2))
            r2_sum += r2_score(y_actual, y_pred)

            sorted_drivers = sorted(all_sims[i][j].items(), key=lambda x: x[1], reverse=True)
            ranks = {driver: rank for rank, (driver, _) in enumerate(sorted_drivers, start=1)}

            predicted_rank = np.array([ranks[driver] for driver in all_sims[i][j]])

            # print(actual_ranks, predicted_rank)

            mare_sum += np.mean(np.abs(actual_ranks - predicted_rank))
            rho_cor, _ = spearmanr(actual_ranks, predicted_rank)
            rho_sum += rho_cor

            if np.argmin(actual_ranks) == np.argmin(predicted_rank):
                champion_sum += 1
            
            if np.argmin(actual_ranks) in set(np.argsort(predicted_rank)[:3]):
                champion_in_t3_sum += 1

            if np.argmin(actual_ranks) in set(np.argsort(predicted_rank)[:2]):
                champion_in_t2_sum += 1
            
            if set(np.argsort(actual_ranks)[:3]) == set(np.argsort(predicted_rank)[:3]):
                t3_sum += 1

                if np.array_equal(np.argsort(actual_ranks)[:3], np.argsort(predicted_rank)[:3]):
                    t3_order_sum += 1
            
            if set(np.argsort(actual_ranks)[:5]) == set(np.argsort(predicted_rank)[:5]):
                t5_sum += 1

                if np.array_equal(np.argsort(actual_ranks)[:5], np.argsort(predicted_rank)[:5]):
                    t5_order_sum += 1
            
            if set(np.argsort(actual_ranks)[:10]) == set(np.argsort(predicted_rank)[:10]):
                t10_sum += 1

                if np.array_equal(np.argsort(actual_ranks)[:10], np.argsort(predicted_rank)[:10]):
                    t10_order_sum += 1
                
        mae["Races Left: " + str(len(all_sims) - i)] = mae_sum/sims
        rmse["Races Left: " + str(len(all_sims) - i)] = rmse_sum/sims
        r2["Races Left: " + str(len(all_sims) - i)] = r2_sum/sims

        mare["Races Left: " + str(len(all_sims) - i)] = mare_sum/sims
        rho["Races Left: " + str(len(all_sims) - i)] = rho_sum/sims

        champion["Races Left: " + str(len(all_sims) - i)] = champion_sum/sims
        champion_in_t3["Races Left: " + str(len(all_sims) - i)] = champion_in_t3_sum/sims
        champion_in_t2["Races Left: " + str(len(all_sims) - i)] = champion_in_t2_sum/sims
        t3["Races Left: " + str(len(all_sims) - i)] = t3_sum/sims
        t5["Races Left: " + str(len(all_sims) - i)] = t5_sum/sims
        t10["Races Left: " + str(len(all_sims) - i)] = t10_sum/sims

        t3_order["Races Left: " + str(len(all_sims) - i)] = t3_order_sum/sims
        t5_order["Races Left: " + str(len(all_sims) - i)] = t5_order_sum/sims
        t10_order["Races Left: " + str(len(all_sims) - i)] = t10_order_sum/sims


    data = [mae, rmse, r2, mare, rho, champion, champion_in_t3, champion_in_t2, t3, t3_order, t5, t5_order, t10, t10_order]

    df = pd.DataFrame(data)
    df.insert(loc=0, column='metric', value=["Mean Absolute Error", "RMSE", "R2", "MARE", 
                                            "Spearman Rho", "Champion Correct", "Champion in T3", "Champion in T2", "T3 Correct", 
                                            "T3 Order Correct", "T5 Correct", "T5 Order Correct", 
                                            "T10 Correct", "T10 Order Correct"])
    df.to_csv(f"results/metrics_{year}.csv", index = False)

def evaluate(year, year_races, sims):
    knn_sim.set_neighbors(year)

    df_eval = pd.read_csv(f"cleaned_data/testing{str(year)}.csv")
    df_eval['prev5_points'] = df_eval['prev5_points'].apply(ast.literal_eval)
    # df_eval['future_results'] = df_eval['future_results'].apply(ast.literal_eval)

    # df_eval_small = (df_eval[df_eval.race_number == 10]).set_index("driver").to_dict(orient='index')

    all_sims = []
    num_races = year_races

    for i in range(6, num_races):
        df_eval_small = (df_eval[df_eval.race_number == i]).set_index("driver").to_dict(orient='index')
        # df_sim = df_eval_small
        res = []
        for j in range(sims):
            df_sim = copy.deepcopy(df_eval_small)
            # changed from 24
            df_sim = knn_sim.simulate_season(df_sim, num_races)


            # res[d] += df_sim[d]["current_points"]/sims
            res.append({
                d: df_sim[d]["current_points"]
                for d in df_sim
            })

        all_sims.append(res)
    # print(all_sims[len(all_sims)-1])
    metrics(year, all_sims, sims)

def avg_metrics(years):
    dfs = []

    for y in years:
        # if y == 2020 or y == 2015:
        #     continue
        df = pd.read_csv(f"results/metrics_{y}.csv")
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)

    avg_df = (
        combined
        .groupby("metric", as_index=False)
        .mean(numeric_only=True)
    )

    race_cols = sorted(
        [c for c in avg_df.columns if c.startswith("Races Left:")],
        key=lambda c: int(c.split(": ")[1]), reverse = True
    )

    avg_df = avg_df[["metric"] + race_cols]
    return avg_df