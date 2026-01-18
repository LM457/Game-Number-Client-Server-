import socket
import random
import threading
import time

MAX_CLIENTS = 4
clients = []   # (conn, addr, name, ready)
lock = threading.Lock()
secret = []
MAX_TURNS = 12
ready_event = threading.Event()


def generate_secret():
    digits = list(range(10))
    random.shuffle(digits)
    return digits[:6]


def check_guess(secret, guess):
    correct_position = sum(s == g for s, g in zip(secret, guess))
    correct_number = sum(min(secret.count(x), guess.count(x)) for x in set(guess)) - correct_position
    return correct_position, correct_number


def is_ready_word(word: str) -> bool:
    target = "ready"
    if word == target:
        return True

    # กรณีสะกดผิดที่พบบ่อย
    common_typos = {"redy", "raedy", "readdy", "rady"}
    if word in common_typos:
        return True

    # Levenshtein distance แบบง่าย
    def levenshtein(a, b):
        dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
        for i in range(len(a) + 1):
            dp[i][0] = i
        for j in range(len(b) + 1):
            dp[0][j] = j
        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                cost = 0 if a[i - 1] == b[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + cost
                )
        return dp[len(a)][len(b)]

    # ถือว่าใช่ถ้าห่างกันไม่เกิน 1 ตัวอักษร
    return levenshtein(word, target) <= 1


def broadcast(message):
    with lock:
        for conn, _, _, _ in clients:
            try:
                conn.send(message.encode())
            except:
                pass


def handle_game():
    global secret
    secret = generate_secret()
    print(f"(เฉลย: {secret})")

    turn = 0
    winner = None

    while turn < MAX_TURNS and not winner and clients:
        with lock:
            current_client = clients[turn % len(clients)]
        conn, addr, name, _ = current_client

        broadcast(f"🎲 ตานี้เป็นของ {name}")

        try:
            conn.send("YOUR_TURN".encode())
            data = conn.recv(1024).decode()
        except:
            print(f"❌ {name} หลุด")
            with lock:
                clients.remove(current_client)
            turn += 1
            continue

        if not data:
            turn += 1
            continue

        guess = [int(x) for x in data]
        correct_pos, correct_num = check_guess(secret, guess)

        log = f"👤 {name} เดา: {guess} -> {correct_pos} ถูกตำแหน่ง, {correct_num} ถูกแต่ไม่ตรงตำแหน่ง"
        print(log)
        broadcast(log)

        if correct_pos == 6:
            winner = name
            break

        turn += 1
        time.sleep(0.5)

    if winner:
        broadcast(f"🎉 {winner} ชนะแล้ว! ตัวเลขคือ {secret}")
    else:
        broadcast(f"😢 ไม่มีใครชนะ ตัวเลขที่ถูกต้องคือ {secret}")


def readiness_checker():
    """รอจนกว่าทุกคน ready ถึงจะเริ่มเกม"""
    while True:
        ready_event.wait()   # จะ unblock เมื่อทุกคน ready
        broadcast("🚀 ทุกคนพร้อมแล้ว เริ่มเกม!")
        handle_game()
        ready_event.clear()  # reset เผื่อรอบใหม่


def handle_client(conn, addr):
    conn.send("กรุณาใส่ชื่อตัวเอง: ".encode())
    name = conn.recv(1024).decode().strip()

    with lock:
        clients.append((conn, addr, name, False))
        print(f"✅ {name} เชื่อมต่อจาก {addr} (รวม {len(clients)} คน)")

    broadcast(f"📢 {name} เข้าร่วมเกมแล้ว!")
    conn.send("Are you ready? (พิมพ์ ready)".encode())

    while True:
        try:
            data = conn.recv(1024).decode().strip().lower()
        except:
            print(f"❌ {name} หลุด")
            with lock:
                for c in clients:
                    if c[0] == conn:
                        clients.remove(c)
                        break
            return

        if is_ready_word(data):
            with lock:
                for i, (c, a, n, r) in enumerate(clients):
                    if n == name:
                        clients[i] = (c, a, n, True)
                        break
            broadcast(f"✅ {name} พร้อมแล้ว!")

            with lock:
                if len(clients) >= 2 and all(r for _, _, _, r in clients):
                    ready_event.set()
            break
        else:
            conn.send("❌ กรุณาพิมพ์ 'ready' ให้ถูกต้อง".encode())


def run_server():
    host = "127.0.0.1"
    port = 65432

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(MAX_CLIENTS)

    print("🎮 รอการเชื่อมต่อจาก Client...")

    threading.Thread(target=readiness_checker, daemon=True).start()

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    run_server()