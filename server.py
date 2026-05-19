import socket
import threading
import os

from engine import ProgramExecutor

# configurarea server-ului
HOST = '0.0.0.0'
PORT = 5050
PROGRAMS_DIR = "programs" # folder-ul cu fisierele .txt

programs = {}
programs_lock = threading.Lock()

def load_programs():
    for filename in os.listdir(PROGRAMS_DIR):
        if filename.endswith('.txt'):
            name = filename.replace('.txt', '')
            filepath = os.path.join(PROGRAMS_DIR, filename)

            with open(filepath, 'r') as f:
                lines = f.readlines()

            executor = ProgramExecutor(lines)

            programs[name] = {
                "executor": executor,
                "client": None,
                "lock": threading.Lock(),
                "started": False  # flag ca sa stim daca programul a fost pornit
            }

            print(f"[SERVER] Program incarcat: {name}")

def start_programs():
    for name, program in programs.items():
        executor = program["executor"]

        # injectam callback-urile
        def make_pause_callback(prog_name):
            def on_pause(line):
                send_to_client(prog_name, f"BREAKPOINT HIT on line {line}")
            return on_pause

        def make_finish_callback(prog_name):
            def on_finish():
                send_to_client(prog_name, "PROGRAM FINISHED!!")
            return on_finish

        executor.on_pause_callback = make_pause_callback(name)
        executor.on_finish_callback = make_finish_callback(name)

        # daemon pe True inseamna ca thread-ul se opreste odata cu oprirea server-ului
        t = threading.Thread(target=executor.run, daemon=True)
        t.start()
        program["started"] = True
        print(f"[SERVER] Program pornit: {name}")

def start_single_program(prog_name):
    """Porneste un singur program - apelat la comanda START din client."""
    program = programs[prog_name]
    executor = program["executor"]

    def on_pause(line):
        send_to_client(prog_name, f"BREAKPOINT HIT on line {line}")

    def on_finish():
        send_to_client(prog_name, "PROGRAM FINISHED!!")

    executor.on_pause_callback = on_pause
    executor.on_finish_callback = on_finish

    t = threading.Thread(target=executor.run, daemon=True)
    t.start()
    program["started"] = True
    print(f"[SERVER] Program pornit: {prog_name}")

def send_to_client(prog_name, message):
    program = programs.get(prog_name)
    if program is None:
        return

    with program["lock"]:
        client = program["client"]
        if client is not None:
            try:
                client.send(f"{message}\n".encode())
            except:
                program["client"] = None
                print(f"[SERVER] Client deconectat de la {prog_name}")

def handle_client(conn, addr):
    print(f"[SERVER] Client conectat: {addr}")
    attached_program = None

    try:
        while True:
            data = conn.recv(1024).decode('utf-8').strip()
            if not data:
                break

            print(f"[SERVER] Primit de la {addr}: '{data}'")

            parts = data.split(' ', 2)
            command = parts[0].upper()


            # ATTACH
            if command == 'ATTACH':
                if len(parts) < 2:
                    conn.send("ERROR missing program name\n".encode())
                    continue

                prog_name = parts[1]

                if prog_name not in programs:
                    conn.send(f"ERROR program {prog_name} not found\n".encode())
                    continue

                program = programs[prog_name]

                with program["lock"]:
                    if program["client"] is not None:
                        conn.send("DENIED program already has a debugger\n".encode())
                    else:
                        program["client"] = conn
                        attached_program = prog_name
                        conn.send(f"OK attached to {prog_name}\n".encode())

            # START - porneste programul atasat (dupa ce ai setat breakpoints)
            elif command == "START":
                conn.send("ERROR command not implemented yet\n".encode())

            # adding a breakpoint
            elif command == "ADD_BREAKPOINT":
                # cerinta: nu poti adauga breakpoints in timpul executiei
                # doar daca e paused sau inca nestartat
                conn.send("ERROR command not implemented yet\n".encode())


            # removing a breakpoint
            elif command == "REMOVE_BREAKPOINT":
                # cerinta: nu poti elimina breakpoints in timpul executiei
                conn.send("ERROR command not implemented yet\n".encode())


            # evaluation of a variab.
            elif command == "EVAL":
                conn.send("ERROR command not implemented yet\n".encode())

            # set variable
            elif command == "SET":
                conn.send("ERROR command not implemented yet\n".encode())

            # continue
            elif command == "CONTINUE":
                conn.send("ERROR command not implemented yet\n".encode())

            # detach from a program
            elif command == "DETACH":
                if attached_program is None:
                    conn.send("ERROR not attached to any programs\n".encode())
                    continue

                program = programs[attached_program]
                with program["lock"]:
                    program["client"] = None

                conn.send(f"OK detached from {attached_program}\n".encode())
                attached_program = None

            # list
            elif command == "LIST":
                conn.send("ERROR command not implemented yet\n".encode())

            else:
                conn.send(f"ERROR unknown command {command}\n".encode())

    # tratare eroare clienti
    except Exception as e:
        print(f"[SERVER] Eroare cu clientul {addr}: {e}")
    finally:
        # TODO: de implementat - curatare resurse la deconectarea clientului:
        # 1. daca clientul era atasat la un program, detaseaza-l (seteaza program["client"] = None)
        # 2. daca programul era in starea "paused", apeleaza continue_execution() ca sa nu ramana blocat
        # 3. de inchis conexiunea
        conn.close()
        print(f"[SERVER] Client deconectat: {addr}")

def main():
    load_programs()
    # programele nu pornesc automat - clientul trimite START dupa ce seteaza breakpoints

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[SERVER] Pornit pe {HOST}:{PORT}")
    print(f"[SERVER] Astept clienti...")


    while True:
        try:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
        except KeyboardInterrupt:
            print("\n[SERVER] Oprire...")
            break
        except Exception as e:
            print(f"Exception {e}")

if __name__ == '__main__':
    main()