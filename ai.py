"""
Hnefatafl AI - Alpha-Beta Pruning
"""
import math, random, time
from game_state import *
from game_logic import get_all_moves, get_piece_moves, make_move, is_valid_pos, DIRECTIONS

DIFFICULTY_DEPTH = {'Easy': 1, 'Medium': 3, 'Hard': 5}
INF = math.inf
TIME_LIMIT = 20  # Time limit in seconds for iterative deepening

def _evaluate_material(state, computer_player):
    """Evaluates the difference in piece counts."""
    num_attackers, num_defenders = 0, 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = state.board[r][c]
            if piece == ATTACKER:
                num_attackers += 1
            elif piece == DEFENDER:
                num_defenders += 1

    if computer_player == ATTACKER_PLAYER:
        return num_attackers * 8 - num_defenders * 14
    else:
        return num_defenders * 14 - num_attackers * 8

def _evaluate_king_safety(state, computer_player, king_row, king_col):
    """Evaluates how many attackers surround the king."""
    blocked = 0
    for dr, dc in DIRECTIONS:
        nr, nc = king_row + dr, king_col + dc
        if not is_valid_pos(nr, nc) or state.board[nr][nc] == ATTACKER:
            blocked += 1
            
    if computer_player == ATTACKER_PLAYER:
        return blocked * 18
    else:
        return -blocked * 18

def _evaluate_king_distance(state, computer_player, king_row, king_col):
    """Evaluates the king's Manhattan distance to the nearest corner."""
    min_dist = min(abs(king_row - cr) + abs(king_col - cc) for cr, cc in CORNERS)
    if computer_player == DEFENDER_PLAYER:
        return -min_dist * 6
    else:
        return min_dist * 6

def _evaluate_corner_paths(state, computer_player, king_row, king_col):
    """Checks for clear, unobstructed paths from the king to any corner."""
    score = 0
    for cr, cc in CORNERS:
        clear = False
        if king_row == cr:
            step = 1 if cc > king_col else -1
            clear = all(state.board[king_row][c] == EMPTY for c in range(king_col + step, cc, step))
        elif king_col == cc:
            step = 1 if cr > king_row else -1
            clear = all(state.board[r][king_col] == EMPTY for r in range(king_row + step, cr, step))
            
        if clear:
            score += 25 if computer_player == DEFENDER_PLAYER else -25
    return score

def evaluate(state, computer_player):
    """Main evaluation function combining all heuristics."""
    king_pos = state.find_king()
    if king_pos is None:
        return 100000 if computer_player == ATTACKER_PLAYER else -100000
    if king_pos in CORNERS:
        return 100000 if computer_player == DEFENDER_PLAYER else -100000
    if state.game_over:
        return 100000 if state.winner == computer_player else -100000

    king_row, king_col = king_pos
    score = 0
    
    score += _evaluate_material(state, computer_player)
    score += _evaluate_king_distance(state, computer_player, king_row, king_col)
    
    king_moves = len(get_piece_moves(state, king_row, king_col))
    score += (king_moves * 4) if computer_player == DEFENDER_PLAYER else -(king_moves * 4)
    
    score += _evaluate_king_safety(state, computer_player, king_row, king_col)
    score += _evaluate_corner_paths(state, computer_player, king_row, king_col)

    return score

def _order_moves(state, moves, computer_player, maximizing):
    """Orders moves to improve alpha-beta pruning efficiency."""
    scored = []
    for src, dst in moves:
        score = 0
        piece = state.get_piece(src[0], src[1])
        
        # Prioritize king reaching a corner
        if piece == KING and dst in CORNERS:
            score += 1000
            
        # Prioritize moves that bring the king closer to a corner
        if piece == KING:
            old_dist = min(abs(src[0] - cr) + abs(src[1] - cc) for cr, cc in CORNERS)
            new_dist = min(abs(dst[0] - cr) + abs(dst[1] - cc) for cr, cc in CORNERS)
            diff = (old_dist - new_dist) * 10
            score += diff if computer_player == DEFENDER_PLAYER else -diff
            
        # Prioritize attackers moving closer to the king
        if piece == ATTACKER:
            kp = state.find_king()
            if kp:
                old_dist = abs(src[0] - kp[0]) + abs(src[1] - kp[1])
                new_dist = abs(dst[0] - kp[0]) + abs(dst[1] - kp[1])
                score += (old_dist - new_dist) * 3
                
        scored.append((score, src, dst))
    
    # Sort descending if maximizing, ascending if minimizing (opponent's turn)
    scored.sort(key=lambda x: x[0], reverse=maximizing)
    return [(src, dst) for _, src, dst in scored]

class TimeoutException(Exception):
    pass

def alpha_beta(state, depth, alpha, beta, maximizing, computer_player, end_time):
    """Minimax search with alpha-beta pruning and time limit."""
    if time.time() > end_time:
        raise TimeoutException()
        
    if depth == 0 or state.game_over:
        return evaluate(state, computer_player), None
        
    moves = get_all_moves(state)
    if not moves:
        return evaluate(state, computer_player), None
        
    moves = _order_moves(state, moves, computer_player, maximizing)
    best_move = moves[0]
    
    if maximizing:
        max_eval = -INF
        for src, dst in moves:
            ns, _ = make_move(state, src, dst)
            ev, _ = alpha_beta(ns, depth - 1, alpha, beta, False, computer_player, end_time)
            if ev > max_eval:
                max_eval = ev
                best_move = (src, dst)
            alpha = max(alpha, ev)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = INF
        for src, dst in moves:
            ns, _ = make_move(state, src, dst)
            ev, _ = alpha_beta(ns, depth - 1, alpha, beta, True, computer_player, end_time)
            if ev < min_eval:
                min_eval = ev
                best_move = (src, dst)
            beta = min(beta, ev)
            if beta <= alpha:
                break
        return min_eval, best_move

def get_computer_move(state, difficulty, computer_player):
    """Gets the best move for the AI using iterative deepening and alpha-beta pruning."""
    max_depth = DIFFICULTY_DEPTH.get(difficulty, 3)
    
    moves = get_all_moves(state)
    if not moves:
        return None
        
    best_overall_move = random.choice(moves)
    end_time = time.time() + TIME_LIMIT

    # Iterative deepening
    for depth in range(1, max_depth + 1):
        try:
            _, best_move_at_depth = alpha_beta(state, depth, -INF, INF, True, computer_player, end_time)
            if best_move_at_depth is not None:
                best_overall_move = best_move_at_depth
        except TimeoutException:
            # Time's up, use the best move found in the previous fully completed depth
            break

    return best_overall_move
