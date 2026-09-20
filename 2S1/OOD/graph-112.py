class Graph:
    def __init__(self):
        self.graph = {}

    def add_edge(self, u, v):
        if u not in self.graph:
            self.graph[u] = []
        if v not in self.graph:
            self.graph[v] = []
        self.graph[u].append(v)
        self.graph[v].append(u)

    def dfs(self):
        visited = set()
        traversal = []

        def dfs_util(v):
            visited.add(v)
            traversal.append(v)
            for neighbor in sorted(self.graph[v]):
                if neighbor not in visited:
                    dfs_util(neighbor)

        for node in sorted(self.graph.keys()):
            if node not in visited:
                dfs_util(node)

        return traversal

    def bfs(self):
        visited = set()
        traversal = []

        for node in sorted(self.graph.keys()):
            if node not in visited:
                queue = [node]
                visited.add(node)
                
                while queue:
                    v = queue.pop(0) 
                    traversal.append(v)
                    for neighbor in sorted(self.graph[v]):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)

        return traversal

def build_graph_and_traverse(edges_input):
    g = Graph()
    
    edges = edges_input.split(',')
    for edge in edges:
        u, v = edge.split()
        g.add_edge(u, v)
    
    dfs_traversal = g.dfs()
    bfs_traversal = g.bfs()
    
    print("Depth First Traversals :", ' '.join(dfs_traversal))
    print("Bredth First Traversals :", ' '.join(bfs_traversal))


edges_input = input("Enter : ")
build_graph_and_traverse(edges_input)
