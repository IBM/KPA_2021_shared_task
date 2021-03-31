NAME: IBM Debater(R) - ArgKP

VERSION: v1

RELEASE DATE: May 10, 2020

DATASET OVERVIEW

24,093 (argument, key point) pairs labeled as matching/non-matching, for 28 controversial topics. 
For each pair, the topic and stance are also indicated.

The dataset is released under the following licensing and copyright terms:
• (c) Copyright IBM 2020. Released under Community Data License Agreement – Sharing, Version 1.0 (https://cdla.io/sharing-1-0/).

The dataset is described in the following publication: 

• From Arguments to Key Points: Towards Automatic Argument Summarization. Roy Bar-Haim, Lilach Eden, Roni Friedman, 
Yoav Kantor, Dan Lahav and Noam Slonim. ACL 2020.

Please cite this paper if you use the dataset.

CONTENTS

The data is split into train and dev datasets. Train consists of 24 motions and dev consists of 4 motions.
Each dataset is represented with 3 csv files:

1. arguments_DATASET.csv - contains the following columns: arg_id,argument,topic,stance (1 for pro, -1 for con)
2. key_points_DATASET.csv - contains the following columns: key_point_id,key_point,topic,stance (1 for pro, -1 for con)
3. labels_DATASET.csv - contains the following columns: arg_id,key_point_id,label (1 for matching, 0 for non-matching)
