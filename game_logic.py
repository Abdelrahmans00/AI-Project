"""
Hnefatafl (Viking Chess) - Game Logic
=======================================
Movement rules, capture mechanics, and win condition checking.
"""

from game_state import (
    EMPTY, ATTACKER, DEFENDER, KING,
    ATTACKER_PLAYER, DEFENDER_PLAYER,
    BOARD_SIZE, THRONE, CORNERS, GameState,
)

DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def is_valid_pos(row, col):
    """Check if a position is within the board bounds."""
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def is_corner(row, col):
    """Check if a position is a corner square."""
    return (row, col) in CORNERS


def is_throne(row, col):
    """Check if a position is the throne (center) square."""
    return (row, col) == THRONE


def is_restricted(row, col):
    """Corners and throne are restricted — only the king may stop on them."""
    return is_corner(row, col) or is_throne(row, col)


# ─── Move Generation ────────────────────────────────────────────────

def get_piece_moves(state, row, col):
    """
    Return a list of valid destination (r, c) for the piece at (row, col).
    Pieces move like rooks: any number of empty squares in a straight line.
    Only the king may land on the throne or corners.
    """
    piece = state.get_piece(row, col)
    if piece == EMPTY:
        return []

    moves = []
    for dr, dc in DIRECTIONS:
        nr, nc = row + dr, col + dc
        while is_valid_pos(nr, nc) and state.get_piece(nr, nc) == EMPTY:
            # Restricted squares: only king may land
            if is_restricted(nr, nc) and piece != KING:
                # Can pass through the throne but not land on it
                if is_throne(nr, nc):
                    nr += dr
                    nc += dc
                    continue
                else:
                    # Cannot pass through or land on corners
                    break
            moves.append((nr, nc))
            nr += dr
            nc += dc
    return moves


def get_all_moves(state):
    """
    Return all legal moves [(src, dst), ...] for the current player.
    """
    moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = state.get_piece(r, c)
            if state.current_player == ATTACKER_PLAYER and piece == ATTACKER:
                for dst in get_piece_moves(state, r, c):
                    moves.append(((r, c), dst))
            elif state.current_player == DEFENDER_PLAYER and piece in (DEFENDER, KING):
                for dst in get_piece_moves(state, r, c):
                    moves.append(((r, c), dst))
    return moves


# ─── Capture Logic ──────────────────────────────────────────────────

def _is_hostile_to(state, row, col, captured_player):
    """
    Determine if the square at (row, col) is hostile to the captured_player.
    Hostile means: it contains an enemy piece, or it is a corner/empty throne.
    The king is unarmed — he does NOT count as hostile for capture purposes.
    """
    if not is_valid_pos(row, col):
        return False

    # Corners are hostile to everyone
    if is_corner(row, col):
        return True

    # Empty throne is hostile to everyone
    if is_throne(row, col) and state.get_piece(row, col) == EMPTY:
        return True

    piece = state.get_piece(row, col)

    if captured_player == ATTACKER_PLAYER:
        # Defenders (not king) are hostile to attackers
        return piece == DEFENDER
    else:
        # Attackers are hostile to defenders
        return piece == ATTACKER


def check_captures(state, row, col):
    """
    After a piece moves to (row, col), check and perform custodial captures.
    Returns a list of captured positions.
    The king is NOT captured by normal custodial capture — see check_king_capture.
    """
    mover = state.get_piece(row, col)
    if mover == EMPTY:
        return []

    # Determine which player is being captured
    if mover in (ATTACKER,):
        captured_player = DEFENDER_PLAYER
    else:
        captured_player = ATTACKER_PLAYER

    captured = []
    for dr, dc in DIRECTIONS:
        ar, ac = row + dr, col + dc
        if not is_valid_pos(ar, ac):
            continue

        adj_piece = state.get_piece(ar, ac)

        # Skip empty, friendly, and king (king has special capture rules)
        if adj_piece == EMPTY or adj_piece == KING:
            continue

        # Check if the adjacent piece belongs to the enemy
        is_enemy = False
        if mover in (ATTACKER,) and adj_piece == DEFENDER:
            is_enemy = True
        elif mover in (DEFENDER, KING) and adj_piece == ATTACKER:
            # King is unarmed — cannot assist in capture
            if mover == KING:
                continue
            is_enemy = True

        if not is_enemy:
            continue

        # Check if there's a hostile square on the other side
        br, bc = ar + dr, ac + dc
        if _is_hostile_to(state, br, bc, captured_player):
            captured.append((ar, ac))

    # Remove captured pieces
    for r, c in captured:
        state.set_piece(r, c, EMPTY)

    return captured


def check_king_capture(state):
    """
    Check if the king is captured (surrounded on all open sides by attackers).
    - On open board: all 4 sides must be attackers
    - Against a wall: the 3 non-wall sides must be attackers
    - Against a corner: the 2 non-corner sides must be attackers
    Returns True if king is captured.
    """
    king_pos = state.find_king()
    if king_pos is None:
        return True  # King already removed

    kr, kc = king_pos

    for dr, dc in DIRECTIONS:
        nr, nc = kr + dr, kc + dc
        if not is_valid_pos(nr, nc):
            # Wall counts as blocking
            continue
        piece = state.get_piece(nr, nc)
        if piece != ATTACKER:
            # The empty throne also counts as hostile for king capture
            if is_throne(nr, nc) and piece == EMPTY:
                continue
            return False  # At least one side is not blocked

    return True  # All sides blocked


def check_king_escape(state):
    """Check if the king has reached any corner square."""
    king_pos = state.find_king()
    if king_pos is None:
        return False
    return king_pos in CORNERS


# ─── Game Controller ────────────────────────────────────────────────

def make_move(state, src, dst):
    """
    Execute a move on a COPY of the state.
    Returns the new state and list of captured positions.
    """
    new_state = state.copy()
    sr, sc = src
    dr, dc = dst

    piece = new_state.get_piece(sr, sc)
    new_state.set_piece(sr, sc, EMPTY)
    new_state.set_piece(dr, dc, piece)

    # Check for custodial captures
    captured = check_captures(new_state, dr, dc)

    # Check win conditions
    if check_king_escape(new_state):
        new_state.game_over = True
        new_state.winner = DEFENDER_PLAYER
    elif check_king_capture(new_state):
        new_state.game_over = True
        new_state.winner = ATTACKER_PLAYER
    else:
        # Check if the king was removed (shouldn't happen with custodial, but safety)
        if new_state.find_king() is None:
            new_state.game_over = True
            new_state.winner = ATTACKER_PLAYER

    # Switch turns
    new_state.switch_player()

    # Check if next player has any moves — if not, they lose
    if not new_state.game_over:
        if len(get_all_moves(new_state)) == 0:
            new_state.game_over = True
            # Player with no moves loses
            if new_state.current_player == ATTACKER_PLAYER:
                new_state.winner = DEFENDER_PLAYER
            else:
                new_state.winner = ATTACKER_PLAYER

    return new_state, captured


def is_valid_move(state, src, dst):
    """Check if a specific move is valid for the current player."""
    sr, sc = src
    piece = state.get_piece(sr, sc)

    # Check piece belongs to current player
    if state.current_player == ATTACKER_PLAYER and piece != ATTACKER:
        return False
    if state.current_player == DEFENDER_PLAYER and piece not in (DEFENDER, KING):
        return False

    valid_dsts = get_piece_moves(state, sr, sc)
    return dst in valid_dsts
