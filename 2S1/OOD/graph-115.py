class Graph:
    def __init__(self):
        self.graph = {}

    def add_edge(self, u, v):
        if u not in self.graph:
            self.graph[u] = []
        self.graph[u].append(v)

    def has_cycle_util(self, vertex, visited, recursion_stack):
        visited.add(vertex)
        recursion_stack.add(vertex)

        for neighbor in self.graph.get(vertex, []):
            if neighbor not in visited:
                if self.has_cycle_util(neighbor, visited, recursion_stack):
                    return True
            elif neighbor in recursion_stack:
                return True

        recursion_stack.remove(vertex)
        return False

    def has_cycle(self):
        visited = set()
        recursion_stack = set()

        for vertex in self.graph:
            if vertex not in visited:
                if self.has_cycle_util(vertex, visited, recursion_stack):
                    return True
        return False

def build_graph_and_check_cycle(input_string):
    g = Graph()
    
    edges = input_string.split(',')
    for edge in edges:
        u, v = edge.split()
        g.add_edge(u, v)

    if g.has_cycle():
        print("Graph has a cycle")
    else:
        print("Graph has no cycle")

input_string = input("Enter : ")
build_graph_and_check_cycle(input_string)
