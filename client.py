import socket

def run_client():
    host = "127.0.0.1"
    port = 65432

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    print("=== เกมทายใจ Mastermind ===")

    while True:
        try:
            data = client_socket.recv(1024).decode()
        except:
            print("❌ หลุดจากเซิร์ฟเวอร์")
            break

        if not data:
            break

        if "กรุณาใส่ชื่อตัวเอง" in data:
            print(data, end="")
            name = input()
            client_socket.send(name.encode())

        elif "Are you ready?" in data:
            print(data)
            ready = input("พิมพ์ ready ถ้าคุณพร้อม: ")
            client_socket.send(ready.encode())

        elif "YOUR_TURN" in data:
            print("👉 ถึงตาคุณแล้ว!")
            while True:
                guess = input("กรอกตัวเลข 6 ตัว: ")
                if not guess.isdigit() or len(guess) != 6:
                    print("❌ กรุณากรอกตัวเลข 6 หลัก")
                    continue
                break
            client_socket.send(guess.encode())

        elif "ชนะแล้ว" in data or "ไม่มีใครชนะ" in data:
            print(data)
            break

        else:
            print(data)

    client_socket.close()
    print("👋 ออกจากเกมเรียบร้อย")


if __name__ == "__main__":
    run_client()
