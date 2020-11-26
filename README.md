# A Python3 Script to Drain an EKS node

## Purpose

To upgrade the worker node AMI version, First you need to update the AMI ID in the auto scaling group / launch template, then you want to move your workload to new version of nodes.

Draining a node manually, then wait for all evicted pods are created, and check all affected deployments manually is tedious. You need to run a lots of kubectl command, get nodes, get pods, get deployments, etc, to check the result.

This script is automated to drain a node safely.

## How it Works

1. Get all running pods of the node to be drained;
2. Get all deployments those pods belong to (meaning those deployments will be affected during draining and need to be checked after drained);
3. Drain the node using `kubectl drain`;
4. Try 3 times with 10 seconds interval to make sure all those affected deployments have desired number of pods after node is drained.

## Prerequisites

EKS:
- PodDisruptionBudget is defined (otherwise one deployment might lose multiple pods during node draining process)
- Cluster autoscaler is enabled (otherwise if there are not enough resources, the drain will stuck forever)

Local:
- python3

## Dependencies

```shell script
pip install -r requirements.txt
```

## Usage

```shell script
(venv) tiexin@Tiexins-MacBook-Pro ~/eks-node-drain $ python main.py 
usage: main.py [-h] [--dry-run] node
main.py: error: the following arguments are required: node
```

### Example - Dry Run:
```shell script
python main.py ip-44-135-6-147.eu-central-1.compute.internal --dry-run 
```
This only shows you what pods will be evicted and which deployments are affected.

### Example - Drain Node:
```shell script
python main.py ip-44-135-6-147.eu-central-1.compute.internal 
```

## Todo

A wrapper shell script that loops over all nodes with this script.

After draining the node, you need to deleting the node from EKS and deleting the EC2 instance.
