import time
import curses
import threading
import random

#Constants
SHAPES = {
    'I' :[(3,0), (4,0), (5,0), (6,0)],  # I shape (x,y) coordinates
    'O' :[(4,0), (5,0), (4,1), (5,1)],  # O shape
    'T' :[(4,0), (3,1), (4,1), (5,1)],  # T shape
    'J' :[(3,0), (3,1), (4,1), (5,1)],  # J shape
    'L' :[(5,0), (3,1), (4,1), (5,1)],  # L shape
    'S' :[(4,0), (5,0), (3,1), (4,1)],  # S shape
    'Z' :[(3,0), (4,0), (4,1), (5,1)],  # Z shape
}

TETROMINOES = [
    # 0: I-Piece (Cyan)
    [
        [[-1, 0], [0, 0], [1, 0], [2, 0]],   # flat →
        [[0, -1], [0, 0], [0, 1], [0, 2]],   # upright
        [[-1, 1], [0, 1], [1, 1], [2, 1]],   # flat (180°)
        [[1, -1], [1, 0], [1, 1], [1, 2]]    # upright (270°)
    ],
    # 1: O-Piece (Yellow) - square, no rotation needed
    [
        [[0, 0], [1, 0], [0, 1], [1, 1]],
        [[0, 0], [1, 0], [0, 1], [1, 1]],
        [[0, 0], [1, 0], [0, 1], [1, 1]],
        [[0, 0], [1, 0], [0, 1], [1, 1]]
    ],
    # 2: T-Piece (Purple)
    [
        [[-1, 0], [0, 0], [1, 0], [0, 1]],   # T up
        [[0, -1], [0, 0], [0, 1], [1, 0]],   # T right
        [[-1, 0], [0, 0], [1, 0], [0, -1]],  # T down
        [[0, -1], [0, 0], [0, 1], [-1, 0]]   # T left
    ],
    # 3: S-Piece (Green)
    [
        [[0, 0], [1, 0], [-1, 1], [0, 1]],
        [[0, -1], [0, 0], [1, 0], [1, 1]],
        [[0, 0], [1, 0], [-1, 1], [0, 1]],
        [[0, -1], [0, 0], [1, 0], [1, 1]]
    ],
    # 4: Z-Piece (Red)
    [
        [[-1, 0], [0, 0], [0, 1], [1, 1]],
        [[1, -1], [0, 0], [1, 0], [0, 1]],
        [[-1, 0], [0, 0], [0, 1], [1, 1]],
        [[1, -1], [0, 0], [1, 0], [0, 1]]
    ],
    # 5: J-Piece (Blue)
    [
        [[-1, -1], [-1, 0], [0, 0], [1, 0]],
        [[1, -1], [0, -1], [0, 0], [0, 1]],
        [[-1, 0], [0, 0], [1, 0], [1, 1]],
        [[0, -1], [0, 0], [0, 1], [-1, 1]]
    ],
    # 6: L-Piece (Orange)
    [
        [[-1, 0], [0, 0], [1, 0], [1, -1]],
        [[0, -1], [0, 0], [0, 1], [1, 1]],
        [[-1, 1], [-1, 0], [0, 0], [1, 0]],
        [[-1, -1], [0, -1], [0, 0], [0, 1]]
    ]
]

# functions
def make_grid_dict(rows=20, cols=10, fill_value=0):
    return  [ [fill_value for _ in range(cols)] for _ in range(rows)]

grid = make_grid_dict()

# display the grid with a simple animation
def display_grid_with_animation(stdscr,grid, message=None):
        height, width = stdscr.getmaxyx()
        stdscr.clear()
        lines = []
        for row in grid:
            text = ''
            for cell in row:
                if cell == 1:
                    text += '[]'  # Current moving block
                elif cell == 2:
                    text += '[]'  # Fixed block
                elif cell == 3:
                    text += '##'  # Ghost block
                else:
                    text += '  '  # Empty space
            lines.append('|' + text + '|')
        lines.append('+' + '__' * len(grid[0]) + '+')
        board_lines = lines
        board_width = len(board_lines[0]) if board_lines else 0
        board_height = len(board_lines)
        left_pad = max(0, (width - board_width) // 2)
        top_pad = max(0, (height - board_height) // 2)
        for i, line in enumerate(board_lines):
            stdscr.addstr(top_pad + i, left_pad, line)
        if message:
            stdscr.addstr(max(0, top_pad + 3), left_pad -1 - len(message), message)  # Display message above board
        stdscr.refresh()

def show_message(message, duration=2):
    global current_message
    current_message = message
    timer = threading.Timer(duration, clear_message)
    timer.start()

def clear_message():
    global current_message
    current_message = None

def new_bag_gen():
    global SHAPES
    bag = list(SHAPES.keys())
    random.shuffle(bag)
    return bag

def block_spawner():
    global current_bag, control_block, grid
    if not current_bag:
        current_bag = new_bag_gen()
    shape_key = current_bag.pop()
    control_block = block(shape_key)
    
    #check for spawn collision
    for (x, y) in control_block.get_current_shape():
        if 0 <= y < 20 and 0 <= x < 10 and grid[y][x] == 2:
            show_message("Game Over! Ctrl + C to exit", duration=5)
            control_block = None
            return
    
    # Add new block to grid
    for (x, y) in control_block.get_current_shape():
        if 0 <= y < 20 and 0 <= x < 10:
            grid[y][x] = 1

def remove_old_position(block, grid):
    for (x, y) in block.get_current_shape():
        if 0 <= y < 20 and 0 <= x < 10:
            grid[y][x] = 0

def draw_new_position(block, grid):
    for (x, y) in block.get_current_shape():
        if 0 <= y < 20 and 0 <= x < 10:
            grid[y][x] = 1


# classes
class block:
    def __init__(self, shape_key):
        self.x = 4  # Center position
        self.y = 0  # Center position
        self.shape_key = shape_key
        # Map shape keys to tetromino indices
        shape_to_index = {'I': 0, 'O': 1, 'T': 2, 'S': 3, 'Z': 4, 'J': 5, 'L': 6}
        self.tetromino_index = shape_to_index[shape_key]
        self.rotation_state = 0  # 0, 1, 2, 3
    
    def get_current_shape(self):
        """Returns list of (x, y) coordinates for current rotation state"""
        relative_coords = TETROMINOES[self.tetromino_index][self.rotation_state]
        return [(self.x + dx, self.y + dy) for dx, dy in relative_coords]
    
    def can_move(self, grid, dx, dy):
        """Check if block can move to new position"""
        new_coords = [(self.x + dx + dx2, self.y + dy + dy2) 
                      for dx2, dy2 in TETROMINOES[self.tetromino_index][self.rotation_state]]
        
        for x, y in new_coords:
            # Check boundaries
            if x < 0 or x >= 10 or y >= 20:
                return False
            # Check collision with placed blocks (only check if y >= 0)
            if y >= 0 and grid[y][x] == 2:
                return False
        return True
    
    def can_rotate(self, grid, direction):
        """Check if block can rotate (direction: 1 for right, -1 for left)"""
        new_rotation = (self.rotation_state + direction) % 4
        relative_coords = TETROMINOES[self.tetromino_index][new_rotation]
        new_coords = [(self.x + dx, self.y + dy) for dx, dy in relative_coords]
        
        for x, y in new_coords:
            # Check boundaries
            if x < 0 or x >= 10 or y >= 20:
                return False
            # Check collision
            if y >= 0 and grid[y][x] == 2:
                return False
        return True
    
    def move(self, grid, dx, dy):
        """Move block if possible"""
        if self.can_move(grid, dx, dy):
            self.x += dx
            self.y += dy
            return True
        return False
    
    def rotate(self, grid, direction):
        """Rotate block if possible (direction: 1 for right, -1 for left)"""
        if self.can_rotate(grid, direction):
            self.rotation_state = (self.rotation_state + direction) % 4
            return True
        return False


# init values
current_bag = new_bag_gen()
control_block = None
current_message = None

# main loop for tetis game would go here
def main(stdscr):
    global grid
    #intiialize for every loop
    curses.curs_set(0)
    stdscr.nodelay(True)
    running = True
    drop_speed = 10
    drop_counter = 0
    block_spawner()

    #main loop
    while running:
        #key capture
        key = stdscr.getch()
        if key != -1 and control_block:
            if key == ord('q'):
                running = False
                break
            elif key == ord('a'):  # Move left
                # Clear old position
                remove_old_position(control_block, grid)
                control_block.move(grid, -1, 0)
                # Redraw at new position
                draw_new_position(control_block, grid)
                        
            elif key == ord('d'):  # Move right
                # Clear old position
                remove_old_position(control_block, grid)
                control_block.move(grid, 1, 0)
                # Redraw at new position
                draw_new_position(control_block, grid)
                        
            elif key == ord('s'):  # Soft drop (move down)
                # Clear old position
                remove_old_position(control_block, grid)
                    
                control_block.move(grid, 0, 1)
                # Redraw at new position
                draw_new_position(control_block, grid)
                        
            elif key == ord('w'):  # Hard drop
                # Clear old position
                remove_old_position(control_block, grid)
                # Drop until collision
                while control_block.move(grid, 0, 1):
                    pass
                # Redraw at new position
                draw_new_position(control_block, grid)
                        
            elif key == ord('j'):  # Rotate left
                # Clear old position
                remove_old_position(control_block, grid)
                control_block.rotate(grid, -1)
                # Redraw at new rotation
                draw_new_position(control_block, grid)
                        
            elif key == ord('k'):  # Rotate right
                # Clear old position
                remove_old_position(control_block, grid)
                control_block.rotate(grid, 1)
                # Redraw at new rotation
                draw_new_position(control_block, grid)
        

        drop_counter += 1
        if drop_counter >= drop_speed:
            drop_counter = 0
            # Auto-drop block
            if control_block:
                # Clear old position
                for (x, y) in control_block.get_current_shape():
                    if 0 <= y < 20 and 0 <= x < 10:
                        grid[y][x] = 0
                if not control_block.move(grid, 0, 1):
                    # Block hit bottom, spawn new one
                    for (x, y) in control_block.get_current_shape():
                        if 0 <= y < 20 and 0 <= x < 10:
                            grid[y][x] = 2  # Set block as fixed
                    #clear full lines
                    new_grid = [row for row in grid if any(cell != 2 for cell in row)]
                    lines_cleared = len(grid) - len(new_grid)
                    for _ in range(lines_cleared):
                        new_grid.insert(0, [0 for _ in range(10)])
                    grid = new_grid
                    block_spawner()
                else:
                    # Redraw at new position
                    for (x, y) in control_block.get_current_shape():
                        if 0 <= y < 20 and 0 <= x < 10:
                            grid[y][x] = 1

        #show ghost block
        if control_block:
            # First, remove any existing ghost blocks (value 3)
            for y in range(20):
                for x in range(10):
                    if grid[y][x] == 3:
                        grid[y][x] = 0
            # Create a copy of the control block to simulate dropping
            ghost_block = block(control_block.shape_key)
            ghost_block.x = control_block.x
            ghost_block.y = control_block.y
            ghost_block.rotation_state = control_block.rotation_state
            # Drop the ghost block until it can't move
            while ghost_block.can_move(grid, 0, 1):
                ghost_block.y += 1
            # Draw the ghost block (value 3)
            for (x, y) in ghost_block.get_current_shape():
                if 0 <= y < 20 and 0 <= x < 10 and grid[y][x] == 0:
                    grid[y][x] = 3

        #display
        display_grid_with_animation(stdscr, grid, current_message)
        time.sleep(1/60)

if __name__ == "__main__":
    curses.wrapper(main)
