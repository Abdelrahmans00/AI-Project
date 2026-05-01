"""
Hnefatafl (Viking Chess) - Game State Representation
=====================================================
11x11 board with pieces, special squares, and initial setup.
"""

# Piece types
EMPTY = 0
ATTACKER = 1
DEFENDER = 2
KING = 3

# Players
ATTACKER_PLAYER = 'attacker'
DEFENDER_PLAYER = 'defender'

# Board configuration
BOARD_SIZE = 11
THRONE = (5, 5)
CORNERS = [(0, 0), (0, 10), (10, 0), (10, 10)]

# Initial piece positions for 11x11 Hnefatafl
INITIAL_ATTACKERS = [
    # Top group (6)
    (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (1, 5),
    # Bottom group (6)
    (10, 3), (10, 4), (10, 5), (10, 6), (10, 7), (9, 5),
    # Left group (6)
    (3, 0), (4, 0), (5, 0), (6, 0), (7, 0), (5, 1),
    # Right group (6)
    (3, 10), (4, 10), (5, 10), (6, 10), (7, 10), (5, 9),
]

INITIAL_DEFENDERS = [
    (3, 5), (4, 4), (4, 5), (4, 6),
    (5, 3), (5, 4),         (5, 6), (5, 7),
    (6, 4), (6, 5), (6, 6), (7, 5),
]

INITIAL_KING = (5, 5)


class GameState:
    """Represents the complete state of a Hnefatafl game."""

    def __init__(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = ATTACKER_PLAYER  # Attackers always move first
        self.game_over = False
        self.winner = None
        self._setup_initial_position()

    def _setup_initial_position(self):
        """Place all pieces in their starting positions."""
        self.board[INITIAL_KING[0]][INITIAL_KING[1]] = KING
        for r, c in INITIAL_DEFENDERS:
            self.board[r][c] = DEFENDER
        for r, c in INITIAL_ATTACKERS:
            self.board[r][c] = ATTACKER

    def copy(self):
        """Create a deep copy of the game state."""
        new_state = GameState.__new__(GameState)
        new_state.board = [row[:] for row in self.board]
        new_state.current_player = self.current_player
        new_state.game_over = self.game_over
        new_state.winner = self.winner
        return new_state

    def get_piece(self, row, col):
        """Get the piece at the given position."""
        return self.board[row][col]

    def set_piece(self, row, col, piece):
        """Set the piece at the given position."""
        self.board[row][col] = piece

    def find_king(self):
        """Find the king's position on the board."""
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == KING:
                    return (r, c)
        return None

    def switch_player(self):
        """Switch the current player."""
        if self.current_player == ATTACKER_PLAYER:
            self.current_player = DEFENDER_PLAYER
        else:
            self.current_player = ATTACKER_PLAYER

    def count_pieces(self):
        """Count attackers and defenders (including king)."""
        attackers = 0
        defenders = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = self.board[r][c]
                if p == ATTACKER:
                    attackers += 1
                elif p in (DEFENDER, KING):
                    defenders += 1
        return attackers, defenders

    def __str__(self):
        """String representation of the board for debugging."""
        symbols = {EMPTY: '.', ATTACKER: 'A', DEFENDER: 'D', KING: 'K'}
        lines = []
        lines.append('   ' + ' '.join(f'{c:2d}' for c in range(BOARD_SIZE)))
        for r in range(BOARD_SIZE):
            row_str = ' '.join(f' {symbols[self.board[r][c]]}' for c in range(BOARD_SIZE))
            lines.append(f'{r:2d} {row_str}')
        return '\n'.join(lines)
