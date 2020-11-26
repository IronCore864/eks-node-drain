from time import sleep
import os
import argparse

from kubernetes import client, config

config.load_kube_config()
core_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()


def get_all_pods_on_node(node_name):
    field_selector = 'spec.nodeName={}'.format(node_name)
    pods = core_v1.list_namespaced_pod(namespace, field_selector=field_selector)
    return pods.items


def get_all_deployments_on_node(node_name):
    result = set()
    pods = get_all_pods_on_node(node_name)
    for p in pods:
        if p.metadata.owner_references[0].kind == 'ReplicaSet':
            rs = apps_v1.read_namespaced_replica_set(p.metadata.owner_references[0].name, namespace)
            if rs.metadata.owner_references[0].kind == 'Deployment':
                d = rs.metadata.owner_references[0].name
                result.add(d)
    return result


def check_all_deployments_have_new_pods(deployments):
    attempts = 0
    ready = False

    while attempts < 3:
        ready = True
        for deployment in deployments:
            res = apps_v1.read_namespaced_deployment(deployment, namespace)
            desired = res.spec.replicas
            available = res.status.available_replicas

            print('Deployment {} desired: {}, available: {}'.format(deployment, desired, available))
            if desired != available:
                ready = False

        if ready:
            return True
        else:
            attempts += 1
            sleep(10)

    return ready


def dry_run(node):
    print("Pods that will be evicted:")
    for p in get_all_pods_on_node(node):
        print(p.metadata.name)

    print()

    print("Deployments that will be affected:")
    for d in get_all_deployments_on_node(args.node):
        print(d)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("node", help="node name")
    parser.add_argument('--dry-run', action='store_true',
                        help="only list pods that will be evicted and deployments that are affected")

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    namespace = "default"
    deployments = get_all_deployments_on_node(args.node)

    if args.dry_run:
        dry_run(args.node)
    else:
        # drain
        os.system('kubectl drain {} --ignore-daemonsets --delete-local-data'.format(args.node))
        # check
        if check_all_deployments_have_new_pods(deployments):
            print('All deployments have desired number of pods after draining node {}, '
                  'please continue.'.format(args.node))
        else:
            print("Some deployments still don't have desired number of pods after 3 retry, "
                  "please check before draining next node.")
