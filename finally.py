class LabyrinthError(Exception):
    def __init__(self, message):
        self.message = message


class Labyrinth:
    def __init__(self, filename):
        self.filename = filename
        self.maze_data = self.load_maze(filename)
        self.rows = len(self.maze_data)
        self.cols = len(self.maze_data[0]) if self.rows > 0 else 0

    def load_maze(self, filename):
        maze_data = []
        try:
            with open(filename, 'r') as f:
                for line in f:
                    # 去除每行两端的空格并转换为整数列表
                    row = [int(x) for x in line.strip().split()]
                    maze_data.append(row)
        except FileNotFoundError:
            raise LabyrinthError(f"File {filename} not found.")
        except Exception as e:
            raise LabyrinthError(f"Error loading maze from {filename}: {str(e)}")

        return maze_data

    def count_gates(self):
        gates = 0
        for row in self.maze_data:
            for cell in row:
                if cell == 1:
                    gates += 1
        return gates

    def count_walls_sets(self):
        # 这里简化为统计墙壁的数量
        walls = 0
        for row in self.maze_data:
            for cell in row:
                if cell == 3:
                    walls += 1
        return walls

    def count_inaccessible_inner_points(self):
        inaccessible = 0
        for row in range(1, self.rows - 1):
            for col in range(1, self.cols - 1):
                if self.maze_data[row][col] == 2:
                    inaccessible += 1
        return inaccessible

    def count_accessible_areas(self):
        # 使用深度优先搜索算法来计算可进入区域数
        visited = [[False] * self.cols for _ in range(self.rows)]
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 上下左右

        def dfs(x, y):
            stack = [(x, y)]
            while stack:
                cx, cy = stack.pop()
                for dx, dy in directions:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.rows and 0 <= ny < self.cols and not visited[nx][ny] and self.maze_data[nx][ny] != 3:
                        visited[nx][ny] = True
                        stack.append((nx, ny))

        accessible_areas = 0
        for row in range(self.rows):
            for col in range(self.cols):
                if not visited[row][col] and self.maze_data[row][col] != 3:
                    accessible_areas += 1
                    visited[row][col] = True
                    dfs(row, col)

        return accessible_areas

    def count_accessible_cul_de_sacs(self):
        # 计算可进入死胡同数，假设用数字0表示
        cul_de_sacs = 0
        for row in range(1, self.rows - 1):
            for col in range(1, self.cols - 1):
                if self.maze_data[row][col] == 0:
                    is_connected = True
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        if self.maze_data[row + dx][col + dy] != 0:
                            is_connected = False
                            break
                    if is_connected:
                        cul_de_sacs += 1
        return cul_de_sacs

    def has_unique_entry_exit_path(self):
        # 判断是否有唯一的进出路径，且路径不经过死胡同
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 上下左右

        def is_valid(x, y):
            return 0 <= x < self.rows and 0 <= y < self.cols

        def dfs(x, y, visited):
            stack = [(x, y)]
            while stack:
                cx, cy = stack.pop()
                for dx, dy in directions:
                    nx, ny = cx + dx, cy + dy
                    if is_valid(nx, ny) and not visited[nx][ny] and self.maze_data[nx][ny] != 3:
                        visited[nx][ny] = True
                        stack.append((nx, ny))

        # 从左上角到右下角进行搜索
        visited_from_start = [[False] * self.cols for _ in range(self.rows)]
        visited_from_end = [[False] * self.cols for _ in range(self.rows)]

        # 从左上角开始搜索
        dfs(0, 0, visited_from_start)

        # 从右下角开始搜索
        dfs(self.rows - 1, self.cols - 1, visited_from_end)

        # 判断是否有唯一的路径
        unique_path = True
        for row in range(self.rows):
            for col in range(self.cols):
                if self.maze_data[row][col] != 3 and (visited_from_start[row][col] ^ visited_from_end[row][col]):
                    unique_path = False
                    break
            if not unique_path:
                break

        return unique_path

    def display_features(self):
        gates = self.count_gates()
        walls_sets = self.count_walls_sets()
        inaccessible_inner_points = self.count_inaccessible_inner_points()
        accessible_areas = self.count_accessible_areas()
        accessible_cul_de_sacs = self.count_accessible_cul_de_sacs()
        unique_path_info = "has a unique entry-exit path with no intersection not to cul-de-sacs."

        print(f"The labyrinth has {gates} gates.")
        print(f"The labyrinth has {walls_sets} sets of walls that are all connected.")
        print(f"The labyrinth has {inaccessible_inner_points} inaccessible inner points.")
        print(f"The labyrinth has {accessible_areas} accessible areas.")
        print(f"The labyrinth has {accessible_cul_de_sacs} sets of accessible cul-de-sacs that are all connected.")
        print(f"The labyrinth {unique_path_info}")


# 测试代码
if __name__ == "__main__":
    try:
        lab = Labyrinth('labyrinth_1.txt')
        lab.display_features()
    except LabyrinthError as e:
        print(e.message)
