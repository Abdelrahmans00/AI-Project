"""
Hnefatafl AI - Alpha-Beta Pruning
"""
import math, random
from game_state import *
from game_logic import get_all_moves, get_piece_moves, make_move, is_valid_pos, DIRECTIONS

DIFFICULTY_DEPTH = {'Easy': 1, 'Medium': 3, 'Hard': 5}
INF = math.inf

def evaluate(state, computer_player):
    king_pos = state.find_king()
    if king_pos is None:
        return 100000 if computer_player == ATTACKER_PLAYER else -100000
    if king_pos in CORNERS:
        return 100000 if computer_player == DEFENDER_PLAYER else -100000
    if state.game_over:
        return 100000 if state.winner == computer_player else -100000

    score = 0
    kr, kc = king_pos
    na, nd = 0, 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = state.board[r][c]
            if p == ATTACKER: na += 1
            elif p == DEFENDER: nd += 1

    if computer_player == ATTACKER_PLAYER:
        score += na * 8 - nd * 14
    else:
        score += nd * 14 - na * 8

    min_dist = min(abs(kr-cr)+abs(kc-cc) for cr, cc in CORNERS)
    if computer_player == DEFENDER_PLAYER:
        score -= min_dist * 6
    else:
        score += min_dist * 6

    king_moves = len(get_piece_moves(state, kr, kc))
    if computer_player == DEFENDER_PLAYER:
        score += king_moves * 4
    else:
        score -= king_moves * 4

    blocked = 0
    for dr, dc in DIRECTIONS:
        nr, nc = kr+dr, kc+dc
        if not is_valid_pos(nr, nc) or state.board[nr][nc] == ATTACKER:
            blocked += 1
    if computer_player == ATTACKER_PLAYER:
        score += blocked * 18
    else:
        score -= blocked * 18

    for cr, cc in CORNERS:
        clear = False
        if kr == cr:
            step = 1 if cc > kc else -1
            clear = all(state.board[kr][c] == EMPTY for c in range(kc+step, cc, step))
        elif kc == cc:
            step = 1 if cr > kr else -1
            clear = all(state.board[r][kc] == EMPTY for r in range(kr+step, cr, step))
        if clear:
            score += 25 if computer_player == DEFENDER_PLAYER else -25

    return score

def _order_moves(state, moves, computer_player):
    scored = []
    for src, dst in moves:
        p = 0
        piece = state.get_piece(src[0], src[1])
        if piece == KING and dst in CORNERS:
            p += 1000
        if piece == KING:
            od = min(abs(src[0]-cr)+abs(src[1]-cc) for cr,cc in CORNERS)
            nd = min(abs(dst[0]-cr)+abs(dst[1]-cc) for cr,cc in CORNERS)
            p += (od - nd) * 10 if computer_player == DEFENDER_PLAYER else (nd - od) * 10
        if piece == ATTACKER:
            kp = state.find_king()
            if kp:
                od = abs(src[0]-kp[0])+abs(src[1]-kp[1])
                nd = abs(dst[0]-kp[0])+abs(dst[1]-kp[1])
                p += (od - nd) * 3
        scored.append((p, src, dst))
    scored.sort(key=lambda x: -x[0])
    return [(s, d) for _, s, d in scored]

def alpha_beta(state, depth, alpha, beta, maximizing, computer_player):
    if depth == 0 or state.game_over:
        return evaluate(state, computer_player), None
    moves = get_all_moves(state)
    if not moves:
        return evaluate(state, computer_player), None
    moves = _order_moves(state, moves, computer_player)
    best_move = moves[0]
    if maximizing:
        max_eval = -INF
        for src, dst in moves:
            ns, _ = make_move(state, src, dst)
            ev, _ = alpha_beta(ns, depth-1, alpha, beta, False, computer_player)
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
            ev, _ = alpha_beta(ns, depth-1, alpha, beta, True, computer_player)
            if ev < min_eval:
                min_eval = ev
                best_move = (src, dst)
            beta = min(beta, ev)
            if beta <= alpha:
                break
        return min_eval, best_move

def get_computer_move(state, difficulty, computer_player):
    depth = DIFFICULTY_DEPTH.get(difficulty, 3)
    _, best = alpha_beta(state, depth, -INF, INF, True, computer_player)
    if best is None:
        moves = get_all_moves(state)
        if moves:
            best = random.choice(moves)
    return best
