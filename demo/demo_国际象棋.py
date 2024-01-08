import chess
def save_board(board, filename):
    with open(filename, 'a') as file:
        file.write(board.fen() + '\n')

def print_board(board):
    print(board)

def get_move():
    uci_move = input("Enter your move: ")
    return 
    
def minimax(board, depth):
    if board.is_checkmate():
        return float('-inf') if board.turn else float('inf')
    if board.is_stalemate() or depth == 0:
        return 0

    if board.turn:
        max_eval = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1)
            board.pop()
            max_eval = max(max_eval, eval)
        return max_eval
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1)
            board.pop()
            min_eval = min(min_eval, eval)
        return min_eval

def get_ai_move(board):
    best_move = None
    best_value = float('-inf')

    for move in board.legal_moves:
        board.push(move)
        move_value = minimax(board, 2)  # 你可以调整深度来改变AI的强度
        board.pop()
        if move_value > best_value:
            best_value = move_value
            best_move = move

    return best_move

def main():
    board = chess.Board()

    while not board.is_checkmate() and not board.is_stalemate():
        print_board(board)
        if board.turn:  # 如果是白方（用户）的回合
            #打印可用步骤列表
            print(list(board.legal_moves))
            move = get_move()
        else:  # 如果是黑方（AI）的回合
            move = get_ai_move(board)
        if move in board.legal_moves:
            board.push(move)
            #save_board(board, 'chess_game.txt')
        else:
            print("Illegal move. Try again.")

    print_board(board)
    if board.is_checkmate():
        print("Checkmate!") 
    else:
        print("Stalemate.")

if __name__ == "__main__":
    main()