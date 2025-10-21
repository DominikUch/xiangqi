# game_logic.py
# Reguły ruchów, pozycje startowe, funkcje pomocnicze.

CELL = 60
COLS = 9
ROWS = 10
MARGIN = 40

INITIAL_POSITIONS = {
    (0, 0): ('b', 'R'), (1, 0): ('b', 'Kn'), (2, 0): ('b', 'E'),
    (3, 0): ('b', 'A'), (4, 0): ('b', 'K'), (5, 0): ('b', 'A'),
    (6, 0): ('b', 'E'), (7, 0): ('b', 'Kn'), (8, 0): ('b', 'R'),
    (1, 2): ('b', 'C'), (7, 2): ('b', 'C'),
    (0, 3): ('b', 'P'), (2, 3): ('b', 'P'), (4, 3): ('b', 'P'),
    (6, 3): ('b', 'P'), (8, 3): ('b', 'P'),
    
    (0, 9): ('r', 'R'), (1, 9): ('r', 'Kn'), (2, 9): ('r', 'E'),
    (3, 9): ('r', 'A'), (4, 9): ('r', 'K'), (5, 9): ('r', 'A'),
    (6, 9): ('r', 'E'), (7, 9): ('r', 'Kn'), (8, 9): ('r', 'R'),
    (1, 7): ('r', 'C'), (7, 7): ('r', 'C'),
    (0, 6): ('r', 'P'), (2, 6): ('r', 'P'), (4, 6): ('r', 'P'),
    (6, 6): ('r', 'P'), (8, 6): ('r', 'P'),
}


def in_board(pos):
    x, y = pos
    return 0 <= x < COLS and 0 <= y < ROWS


def is_clear_path(pieces, src, dst):
    x1, y1 = src
    x2, y2 = dst
    if x1 == x2:
        step = 1 if y2 > y1 else -1
        for y in range(y1 + step, y2, step):
            if (x1, y) in pieces:
                return False
    elif y1 == y2:
        step = 1 if x2 > x1 else -1
        for x in range(x1 + step, x2, step):
            if (x, y1) in pieces:
                return False
    return True


def count_between(pieces, src, dst):
    x1, y1 = src
    x2, y2 = dst
    count = 0
    if x1 == x2:
        step = 1 if y2 > y1 else -1
        for y in range(y1 + step, y2, step):
            if (x1, y) in pieces:
                count += 1
    elif y1 == y2:
        step = 1 if x2 > x1 else -1
        for x in range(x1 + step, x2, step):
            if (x, y1) in pieces:
                count += 1
    return count


def is_legal_move(pieces, src, dst):
    """Sprawdza, czy ruch src->dst jest legalny w obecnym układzie 'pieces'.
    pieces: dict[(x,y)] -> (color, label)
    """
    if src not in pieces:
        return False
    if dst in pieces and pieces[dst][0] == pieces[src][0]:
        return False

    color, label = pieces[src]
    dx = dst[0] - src[0]
    dy = dst[1] - src[1]

    # K - Król
    if label == 'K':
        palace_x = range(3, 6)
        palace_y = range(7, 10) if color == 'r' else range(0, 3)
        if dst[0] not in palace_x or dst[1] not in palace_y:
            return False
        return abs(dx) + abs(dy) == 1

    # A - Doradca (Advisor)
    if label == 'A':
        palace_x = range(3, 6)
        palace_y = range(7, 10) if color == 'r' else range(0, 3)
        if dst[0] not in palace_x or dst[1] not in palace_y:
            return False
        return abs(dx) == 1 and abs(dy) == 1

    # E - Słoń (elephant) - 2 po przekątnej, nie może przeskoczyć i nie może przekroczyć rzeki
    if label == 'E':
        if abs(dx) != 2 or abs(dy) != 2:
            return False
        mid = (src[0] + dx // 2, src[1] + dy // 2)
        if mid in pieces:
            return False
        # nie może przekroczyć rzeki
        if color == 'r' and dst[1] < 5:
            return False
        if color == 'b' and dst[1] > 4:
            return False
        return True

    # Kn - koń
    if label == 'Kn':
        if (abs(dx), abs(dy)) not in [(1, 2), (2, 1)]:
            return False
        # blokada konia
        if abs(dx) == 2:
            block = (src[0] + dx // 2, src[1])
        else:
            block = (src[0], src[1] + dy // 2)
        return block not in pieces

    # R - wieża
    if label == 'R':
        if dx != 0 and dy != 0:
            return False
        return is_clear_path(pieces, src, dst)

    # C - armatka (cannon)
    if label == 'C':
        if dx != 0 and dy != 0:
            return False
        between = count_between(pieces, src, dst)
        if dst in pieces:
            return between == 1  # do bicia musi być dokładnie 1 między
        else:
            return between == 0  # do ruchu nie może być żadnej między

    # P - pion
    if label == 'P':
        forward = -1 if color == 'r' else 1
        if dy == forward and dx == 0:
            return True
        crossed = (color == 'r' and src[1] <= 4) or (color == 'b' and src[1] >= 5)
        if crossed and abs(dx) == 1 and dy == 0:
            return True
        return False

    return False


def get_legal_moves(pieces, src):
    moves = []
    for x in range(COLS):
        for y in range(ROWS):
            dst = (x, y)
            if src != dst and is_legal_move(pieces, src, dst):
                moves.append(dst)
    return moves


def move_piece(pieces, src, dst):
    """Wykonaj ruch (przemieszczamy obiekt z src do dst) — zwraca ewentualnie zbita figura."""
    captured = None
    if dst in pieces:
        captured = pieces.pop(dst)
    piece = pieces.pop(src)
    pieces[dst] = piece
    return captured
