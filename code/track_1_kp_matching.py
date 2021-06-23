import sys
import pandas as pd
from sklearn.metrics import precision_recall_curve, average_precision_score, precision_score
import numpy as np
import os
import json



def get_ap(df, label_column, top_percentile=0.5):
    top = int(len(df)*top_percentile)
    df = df.sort_values('score', ascending=False).head(top)
    # after selecting top percentile candidates, we set the score for the dummy kp to 1, to prevent it from increasing the precision.
    df.loc[df['key_point_id'] == "dummy_id", 'score'] = 0.99
    return average_precision_score(y_true=df[label_column], y_score=df["score"])

def calc_mean_average_precision(df, label_column):
    precisions = [get_ap(group, label_column) for _, group in df.groupby(["topic", "stance"])]
    return np.mean(precisions)

def evaluate_predictions(merged_df):
    print("\n** running evalution:")
    mAP_strict = calc_mean_average_precision(merged_df, "label_strict")
    mAP_relaxed = calc_mean_average_precision(merged_df, "label_relaxed")
    print(f"mAP strict= {mAP_strict} ; mAP relaxed = {mAP_relaxed}")

def load_kpm_data(gold_data_dir, subset, submitted_kp_file=None):
    print("\nֿ** loading task data:")
    arguments_file = os.path.join(gold_data_dir, f"arguments_{subset}.csv")
    if not submitted_kp_file:
        key_points_file = os.path.join(gold_data_dir, f"key_points_{subset}.csv")
    else:
        key_points_file=submitted_kp_file
    labels_file = os.path.join(gold_data_dir, f"labels_{subset}.csv")


    arguments_df = pd.read_csv(arguments_file)
    key_points_df = pd.read_csv(key_points_file)
    labels_file_df = pd.read_csv(labels_file)


    for desc, group in arguments_df.groupby(["stance", "topic"]):
        stance = desc[0]
        topic = desc[1]
        key_points = key_points_df[(key_points_df["stance"] == stance) & (key_points_df["topic"] == topic)]
        print(f"\t{desc}: loaded {len(group)} arguments and {len(key_points)} key points")
    return arguments_df, key_points_df, labels_file_df


def get_predictions(predictions_file, labels_df, arg_df, kp_df):
    print("\nֿ** loading predictions:")
    arg_df = arg_df[["arg_id", "topic", "stance"]]
    predictions_df = load_predictions(predictions_file, kp_df["key_point_id"].unique())

    #make sure each arg_id has a prediction
    predictions_df = pd.merge(arg_df, predictions_df, how="left", on="arg_id")

    #handle arguements with no matching key point
    predictions_df["key_point_id"] = predictions_df["key_point_id"].fillna("dummy_id")
    predictions_df["score"] = predictions_df["score"].fillna(0)

    #merge each argument with the gold labels
    merged_df = pd.merge(predictions_df, labels_df, how="left", on=["arg_id", "key_point_id"])

    merged_df.loc[merged_df['key_point_id'] == "dummy_id", 'label'] = 0
    merged_df["label_strict"] = merged_df["label"].fillna(0)
    merged_df["label_relaxed"] = merged_df["label"].fillna(1)


    print("\n** predictions analysis:")
    for desc, group in merged_df.groupby(["stance", "topic"]):
        not_dummies = group[group["key_point_id"] != "dummy_id"]
        print(f"\t{desc}:")
        print(f"\t\tsubmitted matched for {len(not_dummies)/len(group):.2} of the arguments ({len(not_dummies)}/{len(group)})")


    return merged_df


"""
this method chooses the best key point for each argument
and generates a dataframe with the matches and scores
"""
def load_predictions(predictions_dir, correct_kp_list):
    arg =[]
    kp = []
    scores = []
    invalid_keypoints = set()
    with open(predictions_dir, "r") as f_in:
        res = json.load(f_in)
        for arg_id, kps in res.items():
            valid_kps = {key: value for key, value in kps.items() if key in correct_kp_list}
            invalid = {key: value for key, value in kps.items() if key not in correct_kp_list}
            for invalid_kp, _ in invalid.items():
                if invalid_kp not in invalid_keypoints:
                    print(f"key point {invalid_kp} doesn't appear in the key points file and will be ignored")
                    invalid_keypoints.add(invalid_kp)
            if valid_kps:
                best_kp = max(valid_kps.items(), key=lambda x: x[1])
                arg.append(arg_id)
                kp.append(best_kp[0])
                scores.append(best_kp[1])
        print(f"\tloaded predictions for {len(arg)} arguments")
        return pd.DataFrame({"arg_id" : arg, "key_point_id": kp, "score": scores})

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("You must specify two parameters for this scripts: input data directory and the predictions file")
    else:
        gold_data_dir = sys.argv[1]
        predictions_file = sys.argv[2]

        arg_df, kp_df, labels_df = load_kpm_data(gold_data_dir, subset="dev")

        merged_df = get_predictions(predictions_file, labels_df, arg_df, kp_df)
        evaluate_predictions(merged_df)
