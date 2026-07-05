import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
import ast
from collections import defaultdict
import copy

class KNNSeasonSimulator:

    def __init__(self):
        self.nn = None
        self.future_results = None

        self.feature_cols = [
            "prev5_avg",
            "points_behind_leader",
            "percent_of_max",
            "position",
            "race_number"
        ]

        self.prev5_idx = self.feature_cols.index("prev5_avg")
        self.race_idx = self.feature_cols.index("race_number")

        self.rng = np.random.default_rng()
    
    def set_neighbors(self, year):

        df_neighbors = pd.read_csv(
            f"training_data/neighbors_excluding_{year}.csv"
        )

        df_neighbors["prev5_points"] = (
            df_neighbors["prev5_points"].apply(ast.literal_eval)
        )

        self.future_results = df_neighbors["future_results"].to_numpy()

        X_hist = df_neighbors[self.feature_cols].to_numpy()

        self.nn = NearestNeighbors(
            n_neighbors=30,
            metric="euclidean"
        )

        self.nn.fit(X_hist)

    def get_weights(self, distances):
        d = np.array(distances, dtype=float)

        # replace zeros with a tiny epsilon BEFORE inversion
        d = np.where(d <= 0, 1e-8, d)

        # optional: scale (keeps stability)
        d = d / (np.max(d) + 1e-8)

        w = 1.0 / (d ** 2)

        # remove any leftover inf/nan
        w = np.nan_to_num(w, nan=0.0, posinf=0.0, neginf=0.0)

        total = w.sum()

        if total <= 0 or not np.isfinite(total):
            return np.ones(len(w)) / len(w)

        return w / total

    def get_neighbors(self, train_dict, num_races):
        
        # ---------------------------------------
        # Historical matrix
        # ---------------------------------------
        
        # ---------------------------------------
        # Query matrix from dictionary
        # ---------------------------------------
        drivers = list(train_dict.keys())

        # X_query = np.array([
        #     [train_dict[d][col] for col in feature_cols]
        #     for d in drivers
        # ], dtype=float)

        X_query = np.array(
        [[stats["prev5_avg"],
        stats["points_behind_leader"],
        stats["percent_of_max"],
        stats["position"],
        stats["race_number"]]
        for stats in train_dict.values()],
        dtype=float)
        
        # ---------------------------------------
        # Normalize exactly like the dataframe version
        # ---------------------------------------
        mins = X_query.min(axis=0)
        ranges = X_query.max(axis=0) - mins
        ranges[ranges == 0] = 1  # avoid divide-by-zero

        X_query = (X_query - mins) / ranges

        # Fill prev5_avg NaNs with -1
        
        X_query[np.isnan(X_query[:, self.prev5_idx]), self.prev5_idx] = -1

        # (Only needed if race_number is ever added back into feature_cols)
        if "race_number" in self.feature_cols:
            X_query[:, self.race_idx] /= num_races

        # ---------------------------------------
        # Nearest neighbors
        # ---------------------------------------
        

        distances, indices = self.nn.kneighbors(X_query)

        # ---------------------------------------
        # Build output
        # ---------------------------------------
        result = {}

        for driver, idxs, dists in zip(drivers, indices, distances):
            neighbor_results = [
                self.future_results[idx] if self.future_results[idx] else 0
                for idx in idxs
            ]

            result[driver] = {
                "neighbor_next_result": neighbor_results,
                "neighbor_distances": dists.tolist(),
            }

        return result

    

    def simulate_next_race(self, neighbor_future_df, df_train_updated, num_races):
        # simulating the number of points each driver gets based off neighboring distributions
        # updating their current points
        # c = 1
        # df_train_updated = df_train_updated.set_index("driver").to_dict(orient='index')
        for driver, v in neighbor_future_df.items():
            nn_result = v["neighbor_next_result"]
            weights = self.get_weights(v["neighbor_distances"])
            # can make this sim based as well, create a distribution and sample
            idx = self.rng.choice(len(nn_result), p=weights)
            race_points = nn_result[idx]

            # if race_points == 0:
            #     print(c)
            #     c += 1
            
            df_train_updated[driver]["current_points"] += race_points

            # if "prev5_points" not in v:
            #     stats["prev5_points"] = []

            df_train_updated[driver]["prev5_points"].append(race_points)
            df_train_updated[driver]["prev5_points"] = df_train_updated[driver]["prev5_points"][-5:]

        
        # now, need to recalcuate df_train_updated to reflect updated features:
        # prev5_avg	points_behind_leader	points_behind_second	race_number	position	percent_of_max

        for driver in df_train_updated:
            df_train_updated[driver]["race_number"] *= num_races
            df_train_updated[driver]["race_number"] += 1

        leaderboard = sorted(
            df_train_updated.items(),
            key=lambda x: x[1]["current_points"],
            reverse=True
        )

        leader_points = leaderboard[0][1]["current_points"]

        for pos, (driver, stats) in enumerate(leaderboard, start=1):
            stats["position"] = pos

        for driver, stats in df_train_updated.items():
            stats["points_behind_leader"] = (
                leader_points - stats["current_points"]
            )

        current_race = leaderboard[0][1]["race_number"]

        for driver, stats in df_train_updated.items():
            stats["percent_of_max"] = (
                stats["current_points"] / leader_points
            )

        for driver, stats in df_train_updated.items():

            # if "prev5_points" not in stats:
            #     stats["prev5_points"] = []

            # stats["prev5_points"].append(race_results[driver])

            # stats["prev5_points"] = stats["prev5_points"][-5:]

            stats["prev5_avg"] = np.mean(stats["prev5_points"])

        # df_train_updated = pd.DataFrame.from_dict(df_train_updated, orient="index")
        # df_train_updated = df_train_updated.reset_index().rename(columns={"index": "driver"})
        return df_train_updated

    def simulate_season(self, df_sim, num_races):
        #df_sim = copy.deepcopy(df_train)
        # print(df_sim)
        curr_race = -1
        for k in df_sim.keys():
            curr_race = df_sim[k]["race_number"]
            break
        
        if curr_race < 0 or curr_race > 30:
            # print(curr_race)
            raise Exception("curr race invalid")

        for i in range(int(num_races - curr_race)):
            n = self.get_neighbors(df_sim, num_races)
            df_sim = self.simulate_next_race(n, df_sim, num_races)

        return df_sim