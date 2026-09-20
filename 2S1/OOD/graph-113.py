class Graph:
    def __init__(self):
        self.graph = {}

    def add_edge(self, u, v, w):
        if u not in self.graph:
            self.graph[u] = []
        if v not in self.graph:
            self.graph[v] = []
        self.graph[u].append((v, w))

    def dijkstra(self, start, target):
        shortest_paths = {vertex: (float('inf'), []) for vertex in self.graph}
        shortest_paths[start] = (0, [start])

        visited = set()

        while len(visited) < len(self.graph):
            current_vertex = None
            current_shortest = float('inf')

            for vertex, (dist, path) in shortest_paths.items():
                if vertex not in visited and dist < current_shortest:
                    current_vertex = vertex
                    current_shortest = dist

            if current_vertex is None:
                break

            visited.add(current_vertex)

            for neighbor, weight in self.graph.get(current_vertex, []):
                distance = current_shortest + weight
                if distance < shortest_paths[neighbor][0]:
                    shortest_paths[neighbor] = (distance, shortest_paths[current_vertex][1] + [neighbor])

        if target not in shortest_paths or shortest_paths[target][0] == float('inf'):
            return None
        return shortest_paths[target][1]

def build_graph_and_find_shortest_path(input_string):
    g = Graph()
    graph_input, paths_input = input_string.split('/')

    edges = graph_input.split(',')
    for edge in edges:
        u, w, v = edge.split()
        g.add_edge(u, v, int(w))

    paths = paths_input.split(',')
    for path in paths:
        start, target = path.split()
        if start not in g.graph:
            g.graph[start] = []
        if target not in g.graph:
            g.graph[target] = []

    for path in paths:
        start, target = path.split()
        shortest_path = g.dijkstra(start, target)
        if shortest_path:
            print(f"{start} to {target} : {'->'.join(shortest_path)}")
        else:
            print(f"Not have path : {start} to {target}")

input_string = input("Enter : ")
build_graph_and_find_shortest_path(input_string)
