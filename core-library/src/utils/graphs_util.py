import networkx as nx


def normalize_weights(graph: dict) -> dict:
    sum = 0
    for start, edges in graph.items():
        for end, weight in edges.items():
            sum += weight

    for start, edges in graph.items():
        for end, weight in edges.items():
            graph[start][end] /= sum

    return graph


def create_graph_as_dict(event_ids: list, include_last: bool) -> dict:
    """
    Method that creates a graph represented as a dictionary based on the occurrences of event ids in a window/session
    :param include_last: A bool value that represents whether the last event ID should be included in the graph generation
    :param event_ids: List of the event ids extracted from the logs that occurred in a given window/session
    :return: A dictionary for representation of the graph (nodes and edges),
    where the key is a source node in the graph, and the value is another dictionary where the key
    is the destination node, and the value is the weight of the edge.
    Example: {"A": {"B": 5}} means that the graph has two nodes A,B and there is a directed edge from A to B with weight 5.
    """
    graph_dict = {}
    end = len(event_ids) - 1 if include_last else len(event_ids) - 2
    for i in range(end):
        node1 = event_ids[i]
        node2 = event_ids[i + 1]
        if node1 in graph_dict:
            edge_dict = graph_dict[node1]
            if node2 in edge_dict:
                edge_dict[node2] = edge_dict[node2] + 1
            else:
                edge_dict[node2] = 1
        else:
            graph_dict[node1] = dict()
            graph_dict[node1][node2] = 1
    return normalize_weights(graph_dict)


def create_position_embeddings(event_ids: list, include_last: bool) -> dict:
    """
    Method that creates the position embeddings for the event_ids. The position embeddings represent numerical information
    for the order of occurrence of the event IDs in a log sequence (session). The last event_id detected in the session
    has embedding of 1 and the first event_id in the sequence has the embedding N where N is the count of unique event
    IDs in the sequence
    :param event_ids: List of the event ids extracted from the logs that occurred in a given window/session
    :param include_last: A bool value that represents whether the last event ID should be included in the graph generation
    :return: dictionary where the keys are the event IDs and the values are the corresponding position embeddings for
    the key
    """
    end = len(event_ids) if include_last else len(event_ids) - 1
    embeddings = {event_id: 0 for event_id in event_ids[:end]}
    counter = 1
    for event_id in reversed(event_ids[:end]):
        if embeddings[event_id] == 0:
            embeddings[event_id] = counter
        counter += 1
    return embeddings


def create_networkx_graph(event_ids: list, include_last: bool):
    graph_dict = create_graph_as_dict(event_ids, include_last)
    nodes = set()
    edges_list = []
    graph = nx.DiGraph()
    for start, edges in graph_dict.items():
        nodes.add(start)
        for end, weight in edges.items():
            nodes.add(end)
            edges_list.append((start, end, {"weight": weight}))
    graph.add_nodes_from(list(nodes))
    graph.add_edges_from(edges_list)
    return graph


if __name__ == '__main__':
    print(create_graph_as_dict("A,B,C,B,C,A,D".split(","), False))
    print(create_position_embeddings("A,B,C,B,C,A,D".split(","), False))

