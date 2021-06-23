from json import load
from pathlib import Path
from sys import argv
from typing import List, Tuple

from numpy import mean
from pandas import DataFrame, read_csv
from sklearn.metrics import average_precision_score


def calculate_average_precision(df: DataFrame, label_column: str,
                                top_percentile: float = 0.5):
    """
    Calculate average precision score for top-scores in the data frame
    with respect to relaxed or strict ground truth labels.
    """
    top = int(len(df) * top_percentile)
    df = df.sort_values("score", ascending=False).head(top)
    # If labels don't contain any match, define average precision as zero.
    # Otherwise, calculating precision would fail because of division by zero.
    if (df[label_column] == 0).all():
        return 0
    return average_precision_score(
        y_true=df[label_column],
        y_score=df["score"]
    )


def calculate_mean_average_precision(df: DataFrame, label_column: str):
    """
    Calculate mean average precision score for top-scores
    with respect to relaxed or strict ground truth labels
    across argument key point pairs of same topic and stance.
    """
    precisions = [
        calculate_average_precision(group, label_column)
        for _, group in df.groupby(["topic", "stance"])
    ]
    return mean(precisions)


def evaluate_predictions(merged_df: DataFrame):
    """
    Calculate mean average precision scores
    for relaxed and strict ground truth labels
    and print evaluation scores to console.
    """
    map_strict = calculate_mean_average_precision(merged_df, "label_strict")
    map_relaxed = calculate_mean_average_precision(merged_df, "label_relaxed")
    print(f"mAP strict= {map_strict} ; mAP relaxed = {map_relaxed}")


def load_kpm_data(
        gold_data_dir: Path,
        subset: str
) -> Tuple[DataFrame, DataFrame, DataFrame]:
    """
    Load arguments, key points, and ground truth labels from
    the data directory.
    """

    arguments_file = gold_data_dir / f"arguments_{subset}.csv"
    key_points_file = gold_data_dir / f"key_points_{subset}.csv"
    labels_file = gold_data_dir / f"labels_{subset}.csv"

    arguments_df = read_csv(arguments_file)
    key_points_df = read_csv(key_points_file)
    labels_file_df = read_csv(labels_file)

    return arguments_df, key_points_df, labels_file_df


def load_predictions(predictions_file: Path) -> DataFrame:
    """
    Load data frame with argument key point matches and scores.
    """
    args: List[str] = []
    kps: List[str] = []
    scores: List[float] = []
    with predictions_file.open("r") as file_in:
        predictions = load(file_in)
    for arg_id, kp_scores in predictions.items():
        for kp_id, score in kp_scores.items():
            args.append(arg_id)
            kps.append(kp_id)
            scores.append(score)
    print(f"Loaded {len(args)} predictions "
          f"for {len(predictions.items())} arguments.")
    return DataFrame({
        "arg_id": args,
        "key_point_id": kps,
        "score": scores
    })


def merge_labels_with_predictions(
        arg_df: DataFrame,
        kp_df: DataFrame,
        labels_df: DataFrame,
        predictions_df: DataFrame
) -> DataFrame:
    """
    Merge ground truth labels and predicted match scores
    for all argument key point pairs.
    Missing values are filled in as described in the task description.
    """

    # Remove text columns. These are not needed for evaluation.
    arg_df = arg_df.drop(columns=["argument"])
    kp_df = kp_df.drop(columns=["key_point"])

    # Create a data frame with all argument key point pairs
    # of same topic and stance.
    merged_df: DataFrame = arg_df.merge(kp_df, on=["topic", "stance"])

    # Add ground truth labels.
    # Note that we left-join here, because some pairs have undecided labels,
    # i.e., >15% annotators yet <60% of them marked the pair as a match
    # (as detailed in Bar-Haim et al., ACL-2020).
    merged_df = merged_df.merge(
        labels_df,
        how="left",
        on=["arg_id", "key_point_id"]
    )
    # Resolve undecided labels:
    # For strict labels, fill with no match (0).
    merged_df["label_strict"] = merged_df["label"].fillna(0)
    # For relaxed labels, fill with match (1).
    merged_df["label_relaxed"] = merged_df["label"].fillna(1)

    # Add participant predictions.
    # Note that we left-join here, because some pairs
    # might not have been predicted by the participant.
    merged_df = merged_df.merge(
        predictions_df,
        how="left",
        on=["arg_id", "key_point_id"]
    )
    # Warn if some pairs were not predicted.
    if (merged_df["score"].isna()).any():
        print(
            "Warning: Not all argument key point pairs were predicted. "
            "Missing predictions will be treated as no match."
        )
    # Fill unpredicted labels, treat them as no match (0).
    merged_df["score"] = merged_df["score"].fillna(0)
    # Select best-scored key point per argument.
    # Shuffle (with seed 42) before sorting to ensure
    # that a random key point is selected in case of a tie.
    merged_df = (merged_df.groupby(by="arg_id")
                 .apply(lambda df: df
                        .sample(frac=1, random_state=42)
                        .sort_values(by="score", ascending=False)
                        .head(1))
                 .reset_index(drop=True))
    return merged_df


def main():
    if len(argv) != 3:
        print("You must specify two parameters for this scripts: "
              "input data directory and the predictions file")
        exit(1)

    gold_data_dir = Path(argv[1])
    predictions_file = Path(argv[2])

    arg_df, kp_df, labels_df = load_kpm_data(gold_data_dir, subset="dev")
    predictions_df = load_predictions(predictions_file)
    merged_df = merge_labels_with_predictions(
        arg_df,
        kp_df,
        labels_df,
        predictions_df
    )

    evaluate_predictions(merged_df)


if __name__ == "__main__":
    main()
