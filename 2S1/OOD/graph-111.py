def create_adjacency_matrix(edges_input):
    edges = edges_input.split(',')
    nodes = set()
    for edge in edges:
        node1, node2 = edge.split()
        nodes.add(node1)
        nodes.add(node2)
    
    nodes = sorted(nodes)
    size = len(nodes)
    adjacency_matrix = [[0 for _ in range(size)] for _ in range(size)]
    node_to_index = {node: idx for idx, node in enumerate(nodes)}
    
    for edge in edges:
        node1, node2 = edge.split()
        adjacency_matrix[node_to_index[node1]][node_to_index[node2]] = 1
    
    print("   ", '  '.join(nodes))
    for i, node in enumerate(nodes):
        row = ', '.join(map(str, adjacency_matrix[i]))
        print(f"{node} : {row}")

edges_input1 = input("Enter : ")
create_adjacency_matrix(edges_input1)
