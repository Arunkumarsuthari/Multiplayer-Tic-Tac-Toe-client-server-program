import socket
import threading
import struct
import tkinter as tk
from tkinter import messagebox

player_count = 0
mutex = threading.Lock()

class TicTacToeServer:
    def __init__(self, port):
        self.port = port
        self.server_socket = None
        self.setup_gui()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Tic-Tac-Toe Server")
        self.root.geometry("400x300")
        self.root.configure(bg="lightgray")

        # Server title label
        self.title_label = tk.Label(
            self.root, text="Tic-Tac-Toe Server - ARUN KUMAR", font=("Arial", 16, "bold"), bg="lightgray"
        )
        self.title_label.pack(pady=10)

        # Player count and server status labels
        self.info_frame = tk.Frame(self.root, bg="lightgray")
        self.info_frame.pack(pady=10)

        self.player_count_label = tk.Label(self.info_frame, text="Active Players: 0", font=("Arial", 12), bg="lightgray")
        self.player_count_label.grid(row=0, column=0, padx=10, pady=5)

        self.game_count_label = tk.Label(self.info_frame, text="Ongoing Games: 0", font=("Arial", 12), bg="lightgray")
        self.game_count_label.grid(row=1, column=0, padx=10, pady=5)

        # Status message box
        self.status_box = tk.Text(self.root, height=10, width=40, state="disabled", bg="white")
        self.status_box.pack(pady=10)

        # Start server in a separate thread
        threading.Thread(target=self.run_server).start()

        # Run the GUI
        self.root.mainloop()

    def log_message(self, message):
        self.status_box.config(state="normal")
        self.status_box.insert("end", f"{message}\n")
        self.status_box.config(state="disabled")
        self.status_box.see("end")

    def update_active_players(self, count):
        self.player_count_label.config(text=f"Active Players: {count}")

    def update_ongoing_games(self, count):
        self.game_count_label.config(text=f"Ongoing Games: {count}")

    def run_server(self):
        global player_count
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', self.port))
        self.server_socket.listen(5)
        self.log_message(f"Server listening on port {self.port}.")

        game_count = 0
        while True:
            # Accept new connections and handle players
            clients = self.get_clients()
            game_count += 1
            self.update_ongoing_games(game_count // 2)
            game_thread = threading.Thread(target=self.run_game, args=(clients,))
            game_thread.start()

    def get_clients(self):
        clients = []
        global player_count
        while len(clients) < 2:
            conn, addr = self.server_socket.accept()
            with mutex:
                player_count += 1
                self.update_active_players(player_count)
                self.log_message(f"Player {player_count} connected from {addr}.")
            clients.append(conn)
            self.write_client_int(conn, len(clients) - 1)  # Send client ID (0 or 1)
        return clients

    def run_game(self, clients):
        board = [[' ' for _ in range(3)] for _ in range(3)]
        self.log_message("Game started between two players.")
        player_turn = 0
        game_over = False
        turn_count = 0

        while not game_over:
            self.write_client_msg(clients[(player_turn + 1) % 2], "WAT")
            valid_move = False
            move = -1

            while not valid_move:
                move = self.get_player_move(clients[player_turn])
                if move == -1:
                    self.log_message("Player disconnected.")
                    return
                if self.check_move(board, move):
                    valid_move = True
                else:
                    self.write_client_msg(clients[player_turn], "INV")

            self.update_board(board, move, player_turn)
            self.send_update(clients, move, player_turn)

            if turn_count >= 4 and self.check_board(board, move):
                game_over = True
                self.write_client_msg(clients[player_turn], "WIN")
                self.write_client_msg(clients[(player_turn + 1) % 2], "LSE")
                self.log_message(f"Player {player_turn} won.")
            elif turn_count == 8:
                game_over = True
                self.write_clients_msg(clients, "DRW")
                self.log_message("Game ended in a draw.")

            player_turn = (player_turn + 1) % 2
            turn_count += 1

        for conn in clients:
            conn.close()
        global player_count
        with mutex:
            player_count -= 2
            self.update_active_players(player_count)

    def check_move(self, board, move):
        return 0 <= move <= 8 and board[move // 3][move % 3] == ' '

    def update_board(self, board, move, player_id):
        board[move // 3][move % 3] = 'X' if player_id == 1 else 'O'

    def send_update(self, clients, move, player_id):
        self.write_clients_msg(clients, "UPD")
        self.write_clients_int(clients, player_id)
        self.write_clients_int(clients, move)

    def check_board(self, board, last_move):
        row = last_move // 3
        col = last_move % 3
        player_mark = board[row][col]

        if all(board[row][i] == player_mark for i in range(3)) or all(board[i][col] == player_mark for i in range(3)):
            return True
        if last_move % 2 == 0:
            return all(board[i][i] == player_mark for i in range(3)) or all(board[i][2 - i] == player_mark for i in range(3))
        return False

    def write_client_int(self, conn, msg):
        try:
            conn.sendall(struct.pack("!I", msg))
        except Exception as e:
            self.log_message(f"Error writing int to client socket: {e}")

    def write_client_msg(self, conn, msg):
        try:
            conn.sendall(msg.encode())
        except Exception as e:
            self.log_message(f"Error writing msg to client socket: {e}")

    def write_clients_msg(self, clients, msg):
        for client in clients:
            self.write_client_msg(client, msg)

    def write_clients_int(self, clients, msg):
        for client in clients:
            self.write_client_int(client, msg)

    def get_player_move(self, conn):
        self.write_client_msg(conn, "TRN")
        return self.recv_int(conn)

    def recv_int(self, conn):
        try:
            data = conn.recv(4)
            if not data:
                return -1
            return struct.unpack("!I", data)[0]
        except:
            return -1

def main(port):
    server = TicTacToeServer(port)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Error: No port provided.")
        sys.exit(1)
    main(int(sys.argv[1]))
