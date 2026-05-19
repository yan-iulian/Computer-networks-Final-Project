import threading
import time


class ProgramExecutor:
    def __init__(self, code_lines):
        # Initializam memoria si curatam liniile goale
        self.code_lines = [line.strip() for line in code_lines if line.strip()]
        self.variables = {} # memoria programului
        self.breakpoints = set() # set cu nr. liniilor unde treb. sa se opreasca

        self.current_line = 0  # intern folosim 0-index, vizual vom folosi 1-index
        self.state = "not_started"  # running, paused, finished

        # Semaforul
        self._pause_event = threading.Event()
        self._pause_event.set()  # semaforul e "verde"(True) cand programul porneste

        # Callback-uri optionale pentru a trimite informatii inapoi Serverului (Colegul 2)
        self.on_pause_callback = None
        self.on_finish_callback = None

    def set_breakpoint(self, line_number):
        """Adauga un breakpoint. Atentie: userii folosesc 1-index (incep cu linia 1)."""
        self.breakpoints.add(line_number)

    def remove_breakpoint(self, line_number):
        if line_number in self.breakpoints:
            self.breakpoints.remove(line_number)

    def get_variable(self, name):
        # returnam valoarea unei variabile din memoria programului
        """Metoda promisa Colegului 3 pentru interogare."""
        if name in self.variables:
            return self.variables[name]
        return f"EROARE: Variabila '{name}' nu exista in memorie."

    def set_variable(self, name, value):
        # modifica sau creeaza o variab. in memoria programului
        """Metoda promisa Colegului 3 pentru manipulare/trisare in timpul executiei."""
        try:
            self.variables[name] = float(value)
            return True
        except ValueError:
            return False

    def continue_execution(self):
        # reia executia programului dupa pauza
        """Reda semaforul pe culoarea verde pentru a porni iar Thread-ul principal."""
        if self.state == "paused":
            self.state = "running"
            self._pause_event.set()

    def _execute_line(self, line):
        # parseaza si executa o singura linie de cod
        # e meth. privata in python (pt ca are _ in fata)
        """Motorul intern de procesare a matematicii"""
        if '=' not in line:
            return  # Sarim daca nu e instructiune de atribuire

        var_name, expression = line.split('=', 1)
        var_name = var_name.strip()
        expression = expression.strip()

        try:
            # Functia eval este inima calculelor: parcurge expresia (ex "a + 3 * 2")
            # Inlocuieste automat "a"-ul din dictionarul self.variables !
            result = eval(expression, {"__builtins__": {}}, self.variables)
            # Salvam noua valoare in memorie:
            self.variables[var_name] = result
        except Exception as e:
            print(f"Eroare severa la engine in timpul evaluarii '{expression}': {e}")

    def run(self):
        # ruleaza toate liniile in ordine
        """Functia uriasa care trebuie pusa de Colegul 2 pe un Thread separat."""
        while self.current_line < len(self.code_lines):
            line_to_execute = self.code_lines[self.current_line]
            display_line_num = self.current_line + 1  # convertim la numerotatia pe care o vede clientul( 0 -> 1)

            # Verificam Breakpointu INAINTE de a rula logica:
            if display_line_num in self.breakpoints:
                self.state = "paused"
                self._pause_event.clear()  # semaforul trece pe rosu!!

                # Anuntam pe celula de control ca ne-am blocat
                if self.on_pause_callback:
                    self.on_pause_callback(display_line_num)

                # THE THREAD STOPS HERE AND CONSUMES 0% CPU !
                # It will wait endlessly until somebody calls motor.continue_execution()
                self._pause_event.wait()

            # firul ajunge aici abia dupa ce Thread-ul a fost reluat
            # (Sau din prima daca nu exista Breakpoint):
            self._execute_line(line_to_execute)
            time.sleep(0.5)  # Simulam o secunda de gandire, ca instructiunile "sa nu se termine instant"

            self.current_line += 1

        # Odata scapat de While, anuntam ca script-ul e gata
        self.state = "finished"
        if self.on_finish_callback:
            self.on_finish_callback()
