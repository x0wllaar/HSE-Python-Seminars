import networkx as nx
from transliterate import slugify
from networkx.algorithms import bipartite
import logging
from tqdm import tqdm
import argparse

logging.basicConfig(level=logging.DEBUG)

parser = argparse.ArgumentParser(
    description="Takes lemmatized texts from MongoDB and builds a dictionary mapping for use with LDA"
)
parser.add_argument(
    "--output", "-o", type=str, required=True, help="Where to save the one-mode network"
)
parser.add_argument(
    "--input", "-i", type=str, required=True, help="Input gpickle network"
)
parser.add_argument(
    "--twomode",
    type=bool,
    default=False,
    help="Treat the network as 2-mode (bipartite attribute)",
)
parser.add_argument("--removenone", type=bool, default=False, help="Remove None node")
parser.add_argument(
    "--translit", type=bool, default=False, help="Transliterate node names"
)
args = parser.parse_args()

graph = nx.read_gpickle(args.input)

if args.removenone:
    try:
        graph.remove_node(None)
    except:
        pass
    try:
        graph.remove_node("None")
    except:
        pass

if args.twomode:
    bottom_nodes = set(n for n, d in graph.nodes(data=True) if d["bipartite"] == 1)
    top_nodes = set(graph) - bottom_nodes
else:
    top_nodes = set()
    bottom_nodes = set(n for n, d in graph.nodes(data=True))


logging.debug(f"{len(bottom_nodes)} bottom nodes")
logging.debug(f"{len(top_nodes)} top nodes")

with open(args.output, "w+") as of:
    if args.twomode:
        print(f"*vertices {graph.order()} {len(bottom_nodes)}", file=of)
    else:
        print(f"*vertices {graph.order()}", file=of)

    all_nodes_ordered = list(bottom_nodes) + list(top_nodes)
    nodens = dict(zip(all_nodes_ordered, range(1, len(all_nodes_ordered) + 1)))

    logging.debug("Writing nodes")
    for name, num in tqdm(nodens.items()):
        sanName = str(name).replace(" ", "_")
        if args.translit:
            sanName = slugify(sanName)
        # sanName = str(num)
        print(f"{num} {sanName}", file=of)
    logging.debug("Nodes written!")

    logging.debug("Writing edges")
    print("*edges", file=of)
    for u, v, data in tqdm(graph.edges(data=True)):
        weight = data["weight"]
        nu = nodens[u]
        nv = nodens[v]
        print(f"{nu} {nv} {weight}", file=of)
