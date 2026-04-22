import threading
import time

class ProgramExecutor:
    def __init__(self, code_lines):
        # Initializam memoria si curatam liniile goale
        self.code_lines = [line.strip() for line in code_lines if line.strip()]
        self.variables = {}
        self.breakpoints = set()
        
        self.current_line = 0 # Intern folosim 0-index, vizual vom folosi 1-index
        self.state = "running" # Poate fi: running, paused, finished
        
        # Obiectul magic care ne permite blocarea threadului (Semaforul)
        self._pause_event = threading.Event()
        self._pause_event.set() # La pornire semaforul e Verde
        
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
        """Metoda promisa Colegului 3 pentru interogare."""
        if name in self.variables:
            return self.variables[name]
        return f"EROARE: Variabila '{name}' nu exista in memorie."
        
    def set_variable(self, name, value):
        """Metoda promisa Colegului 3 pentru manipulare/trisare in timpul executiei."""
        try:
            self.variables[name] = float(value)
            return True
        except ValueError:
            return False
            
    def continue_execution(self):
        """Reda semaforul pe culoarea verde pentru a porni iar Thead-ul principal."""
        if self.state == "paused":
            self.state = "running"
            self._pause_event.set() 
            
    def _execute_line(self, line):
        """Motorul intern de procesare a matematicii"""
        if '=' not in line:
            return # Sarim daca nu e instructiune de atribuire
            
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
        """Functia uriasa care trebuie pusa de Colegul 2 pe un Thread separat."""
        while self.current_line < len(self.code_lines):
            line_to_execute = self.code_lines[self.current_line]
            display_line_num = self.current_line + 1 # Convertim la numerotatie umana
            
            # Verificam Breakpointu INAINTE de a rula logica:
            if display_line_num in self.breakpoints:
                self.state = "paused"
                self._pause_event.clear() # Culoarea Roșie!
                
                # Anuntam pe celula de control ca ne-am blocat
                if self.on_pause_callback:
                    self.on_pause_callback(display_line_num)
                
                # THE THEAD STOPS HERE AND CONSUMES 0% CPU !
                # It will wait endlessly until somebody calls motor.continue_execution()
                self._pause_event.wait()
                
            # Firul ajunge abia aici dupa ce Thead-ul a fost reluat 
            # (Sau din prima daca nu exista Breakpoint):
            self._execute_line(line_to_execute)
            time.sleep(0.5) # Simulam o secunda de gandire, ca instructiunile "sa nu se termine instant"
            
            self.current_line += 1
            
        # Odata scapat de While, anuntam ca script-ul e gata
        self.state = "finished"
        if self.on_finish_callback:
            self.on_finish_callback()

# ====================================================================
#  ZONA DE SIMULARE (FĂRĂ REȚEA - TESTAREA COLEGULUI 1 IZOLATĂ)
# ====================================================================
def demo_fals():
    print("=== START SIMULARE (Colegul 1 isi testeaza codul singur) ===")
    
    # 1. Cream "fake text file"
    cod_inventat = [
        "a = 5",
        "b = a * 2 + 10",
        "c = a + b",
        "rezultat_secundar = b / 2"
    ]
    
    motor = ProgramExecutor(cod_inventat)
    
    # 2. Punem un breakpoint la linia 3 => "c = a + b"
    motor.set_breakpoint(3)
    
    # Creez niste callback-uri false doar ca sa vad ca ele se activeaza:
    def la_pauza(linie):
        print(f"\n[SISTEM] > PROGRAM BLOCAT la linia {linie}.")
        
    def la_finalizare():
        print(f"\n[SISTEM] > Executie incheiata cu succes.")
        
    motor.on_pause_callback = la_pauza
    motor.on_finish_callback = la_finalizare
    
    # 3. LANSAREA EXECUTIEI (pe fundal!)
    print("[SISTEM] Pornim Thread-ul cu programul...")
    thread_executie = threading.Thread(target=motor.run)
    thread_executie.start()
    
    # 4. Aici e simularea Colegului 3 (Terminalul vizibil, loop infinit pana e gata)
    while motor.state != "paused" and motor.state != "finished":
        # Stam si urmarim bara de incarcare
        time.sleep(0.1)
        
    if motor.state == "paused":
        print(f"[CLIENT] Oho! A atins Breakpoint-ul.")
        print(f"[CLIENT] Dati-mi va rog statusul memoriei curente (pe b si pe a):")
        print(f"        -> a = {motor.get_variable('a')}")
        print(f"        -> b = {motor.get_variable('b')}")
        
        print(f"[CLIENT] Acum o se testez magia TRISARII prin Set.")
        print(f"[CLIENT] Voi modifica in timp real variabila 'b' din {motor.get_variable('b')} in 100.")
        valid = motor.set_variable('b', 100)
        
        print(f"[CLIENT] Valoarea injectata? {'DA' if valid else 'NU'}")
        
        print(f"[CLIENT] Trimiț comanda de reluare! (CONTINUE)")
        motor.continue_execution()
        
    # Programul original si fisierul asta Asteapta terminarea totala
    thread_executie.join()
    
    print("\n[CLIENT] Din moment ce a fost finalizat, hai sa vad cum a calculat valoarea c (care era a + b).")
    print(f"        -> c calculat automat de python: {motor.get_variable('c')}")
    print(f"        (Daca e 105, inseamna ca hack-ul pe breakpoint a functionat corect!)")
    print("\nSTATUSUL TOTAL AL MEMORIEI in Motorul Izolat:")
    print(motor.variables)
    
if __name__ == '__main__':
    demo_fals()
