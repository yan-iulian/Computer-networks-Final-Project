import socket
import threading

HOST = 'localhost'
PORT = 5050


def receive_messages(sock):
    """Thread separat care primește mesaje de la server non-stop."""
    while True:
        try:
            data = sock.recv(1024).decode('utf-8')
            if not data:
                print("[CLIENT] Server deconectat.")
                break
            print(f"[SERVER] {data.strip()}")
        except:
            break


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    print(f"[CLIENT] Conectat la {HOST}:{PORT}")
    print(
        "[CLIENT] Comenzi: LIST, ATTACH <prog>, ADD_BREAKPOINT <prog> <linie>, EVAL <var>, SET <var> <val>, CONTINUE, DETACH")

    # Thread separat pentru mesaje primite de la server
    t = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    t.start()

    # Loop principal - citești comenzi de la tastatură
    while True:
        try:
            command = input()
            if not command.strip():
                continue
            sock.send(f"{command}\n".encode())
        except KeyboardInterrupt:
            print("\n[CLIENT] Deconectare...")
            break

    sock.close()


if __name__ == '__main__':
    main()