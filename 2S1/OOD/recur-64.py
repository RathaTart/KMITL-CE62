def CreateMaze2D(maze):
    maze2D = [list(row) for row in maze]
    return maze2D

def FindMaze(maze):
    start = (0,0)

    def solve_maze(maze, row, col):
        if maze[row][col] == 'E':
            return True
        
        # Mark cell
        if maze[row][col] != 'S':
            maze[row][col] = '*'
        
        #moves: up, down, left, right
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for move in moves:
            next_row, next_col = row + move[0], col + move[1]
            if 0 <= next_row < len(maze) and 0 <= next_col < len(maze[0]):
                if maze[next_row][next_col] in ('.', 'E'):
                    if solve_maze(maze, next_row, next_col):
                        return True
        
        #unmark the cell (backtrack)
        if maze[row][col] != 'S':
            maze[row][col] = '.'
        
        return False

    if solve_maze(maze, start[0], start[1]):
        return maze
    else:
        print("No solution found")
        return False

print("Enter the entire maze in one line. Use '.' for open cells, '#' for walls, 'S' for start, and 'E' for end.")
print("Separate each row with a comma (,).")
maze_input = input("Enter the maze: ").split(',')
# print("1 = ", maze_input)
maze_input = [list(row) for row in maze_input]
# print("2 = ", maze_input)
maze = CreateMaze2D(maze_input)
# print("3 = ", maze)
print("Your maze:")
for row in maze:
    for col in row:
        print(col, end="")
    print("")
solution = FindMaze(maze)
if solution:
    print("Solution found:")
    for row in solution:
        for col in row:
            print(col, end="")
        print("")
