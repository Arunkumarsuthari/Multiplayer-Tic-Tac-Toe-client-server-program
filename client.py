import socket
import threading
import struct
import tkinter as tk
from tkinter import messagebox, simpledialog

class TicTacToeClient:
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.player_id = None
        self.game_number = 1  # Initialize game number
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.sock = None
        self.my_turn = False  # Track if it's this player's turn
        self.create_gui()

    def create_gui(self):
        # Initialize main window
        self.root = tk.Tk()
        self.root.title("Tic-Tac-Toe: ARUN KUMAR")
        self.root.geometry("400x500")
        self.root.configure(bg="lightblue")

        # Title label with your name and game information
        self.title_label = tk.Label(
            self.root, text="Tic-Tac-Toe Game - ARUN KUMAR (21MEB0B62)",
            font=("Arial", 16, "bold"), bg="lightblue"
        )
        self.title_label.pack(pady=10)

        # Player and game info labels
        self.info_frame = tk.Frame(self.root, bg="lightblue")
        self.info_frame.pack(pady=5)

        self.player_label = tk.Label(self.info_frame, text="Player: Waiting...", font=("Arial", 12), bg="lightblue")
        self.player_label.grid(row=0, column=0, padx=20)

        self.game_label = tk.Label(self.info_frame, text=f"Game No: {self.game_number}", font=("Arial", 12), bg="lightblue")
        self.game_label.grid(row=0, column=1, padx=20)

        # Game board buttons
        self.buttons = [[None for _ in range(3)] for _ in range(3)]
        self.board_frame = tk.Frame(self.root, bg="lightblue")
        self.board_frame.pack(pady=10)

        for i in range(3):
            for j in range(3):
                btn = tk.Button(self.board_frame, text="", font=("Arial", 24), width=5, height=2,
                                command=lambda i=i, j=j: self.send_move(i, j), state="disabled")
                btn.grid(row=i, column=j, padx=5, pady=5)
                self.buttons[i][j] = btn

        # Status label
        self.status_label = tk.Label(self.root, text="Connecting to server...", font=("Arial", 12), bg="lightblue")
        self.status_label.pack(pady=10)

        # Connect to the server and start the game loop
        threading.Thread(target=self.connect_to_server).start()

    def connect_to_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print(f"Attempting to connect to {self.hostname}:{self.port}")
            self.sock.connect((self.hostname, self.port))
            print("Connection established!")
            self.player_id = self.recv_int()
            self.update_player_info()
            threading.Thread(target=self.listen_for_messages).start()
        except socket.error as e:
            error_message = f"Unable to connect to server at {self.hostname}:{self.port}\nError: {e}"
            print(error_message)
            messagebox.showerror("Connection Error", error_message)
            self.root.destroy()

    def update_player_info(self):
        # Update player info once connected
        self.player_label.config(text=f"Player: {'X' if self.player_id == 1 else 'O'}")
        self.status_label.config(text="Waiting for the game to start...")

    def listen_for_messages(self):
        while True:
            msg = self.recv_msg()
            if msg == "SRT":
                self.status_label.config(text="Game started! Your turn..." if self.player_id == 1 else "Waiting for opponent...")
                self.clear_board()
                self.my_turn = (self.player_id == 1)
                self.update_buttons()
            elif msg == "TRN":
                self.my_turn = True
                self.status_label.config(text="Your turn!")
                self.update_buttons()
            elif msg == "WAT":
                self.my_turn = False
                self.status_label.config(text="Waiting for opponent's move...")
                self.update_buttons()
            elif msg == "UPD":
                player_id = self.recv_int()
                move = self.recv_int()
                self.update_board(player_id, move)
            elif msg == "WIN":
                self.show_game_result("Congratulations! You win!")
            elif msg == "LSE":
                self.show_game_result("You lost. Better luck next time!")
            elif msg == "DRW":
                self.show_game_result("It's a draw!")
            elif msg == "INV":
                messagebox.showwarning("Invalid Move", "This position is already taken. Try another one.")
            elif msg == "CNT":
                num_players = self.recv_int()
                messagebox.showinfo("Active Players", f"There are currently {num_players} active players.")

    def show_game_result(self, message):
        self.status_label.config(text=message)
        for row in self.buttons:
            for btn in row:
                btn.config(state="disabled")
        self.game_number += 1
        self.update_game_info()

    def send_move(self, row, col):
        if self.my_turn:
            move = row * 3 + col
            self.write_server_int(move)
            self.my_turn = False
            self.update_buttons()
        else:
            messagebox.showwarning("Not Your Turn", "Please wait for your turn.")

    def update_board(self, player_id, move):
        symbol = 'X' if player_id == 1 else 'O'
        row, col = divmod(move, 3)
        self.board[row][col] = symbol
        self.buttons[row][col].config(text=symbol, state="disabled")

    def clear_board(self):
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        for i in range(3):
            for j in range(3):
                self.buttons[i][j].config(text="", state="normal")

    def update_buttons(self):
        for row in self.buttons:
            for btn in row:
                btn.config(state="normal" if self.my_turn else "disabled")

    def update_game_info(self):
        self.game_label.config(text=f"Game No: {self.game_number}")

    def recv_msg(self):
        try:
            msg = self.sock.recv(3).decode('utf-8')
            return msg
        except socket.error:
            self.sock.close()
            self.root.quit()
            return None

    def recv_int(self):
        try:
            data = self.sock.recv(4)
            return struct.unpack("!I", data)[0]
        except socket.error:
            self.sock.close()
            self.root.quit()
            return None

    def write_server_int(self, msg):
        try:
            data = struct.pack("!I", msg)
            self.sock.sendall(data)
        except socket.error:
            self.sock.close()
            self.root.quit()

def main():
    hostname = simpledialog.askstring("Hostname", "Enter server hostname or IP:")
    port = simpledialog.askinteger("Port", "Enter server port number:")
    if hostname and port:
        client = TicTacToeClient(hostname, port)
        client.root.mainloop()

if __name__ == "__main__":
    main()
