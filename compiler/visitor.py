import re
from lark.visitors import Interpreter
from lark import Token, Tree


class SemanticError(Exception):
    """Wyjątek rzucany w przypadku błędów semantycznych (muzycznych lub logicznych)."""
    pass


class SynthScriptVisitor(Interpreter):
    def __init__(self):
        super().__init__()
        self.music_data = {
            "meter": "4|4",
            "tracks": []
        }
        self.variables = {}
        self.functions = {}
        self.current_track = None

    def program(self, tree):
        """Punkt startowy programu."""
        meter_node = tree.find_data('meter_stmt')
        for m in meter_node:
            self.visit(m)

        for child in tree.children:
            if isinstance(child, Tree) and child.data in ('assignment', 'func_def'):
                self.visit(child)

        track_nodes = tree.find_data('track')
        for t in track_nodes:
            self.visit(t)

        return self.music_data

    def meter_stmt(self, tree):
        """meter_stmt: KW_METER NUMBER BAR NUMBER"""
        num1 = tree.children[1].value
        num2 = tree.children[3].value
        self.music_data["meter"] = f"{num1}|{num2}"

    def track(self, tree):
        """track: KW_TRACK STRING LBRACE statement* RBRACE"""
        track_name = tree.children[1].value.strip('"')

        self.current_track = {
            "name": track_name,
            "events": []
        }
        self.music_data["tracks"].append(self.current_track)

        for child in tree.children:
            if hasattr(child, 'data'):
                self.visit(child)

    def assignment(self, tree):
        """assignment: ID OP_ASSIGN expression"""
        var_name = tree.children[0].value
        expr_value = self._evaluate(tree.children[2])
        self.variables[var_name] = expr_value

    # --- OBSŁUGA PLAY_STMT (Zsynchronizowana z Twoją gramatyką) ---

    def play_default(self, tree):
        """play_stmt: KW_PLAY (note | chord)"""
        pitch = self._get_pitch(tree.children[1])
        self._add_play_event(pitch, duration=4, velocity="mf")

    def play_dur(self, tree):
        """play_stmt: KW_PLAY (note | chord) expression"""
        pitch = self._get_pitch(tree.children[1])
        duration = self._evaluate(tree.children[2])
        self._add_play_event(pitch, duration, velocity="mf")

    def play_dur_vel_num(self, tree):
        """play_stmt: KW_PLAY (note | chord) expression expression (głośność jako liczba)"""
        pitch = self._get_pitch(tree.children[1])
        duration = self._evaluate(tree.children[2])
        velocity = self._evaluate(tree.children[3])

        if not (0 <= velocity <= 127):
            raise SemanticError(f"Głośność poza zakresem MIDI (0-127): {velocity}")

        self._add_play_event(pitch, duration, velocity)

    def play_dur_vel_lab(self, tree):
        """play_stmt: KW_PLAY (note | chord) expression VELOCITY_LABEL"""
        pitch = self._get_pitch(tree.children[1])
        duration = self._evaluate(tree.children[2])
        velocity = tree.children[3].value.strip("$")

        self._add_play_event(pitch, duration, velocity)

    def play_vel_label(self, tree):
        """play_stmt: KW_PLAY (note | chord) VELOCITY_LABEL"""
        pitch = self._get_pitch(tree.children[1])
        velocity = tree.children[2].value.strip("$")
        self._add_play_event(pitch, duration=4, velocity=velocity)

    # --- INNE INSTRUKCJE MUZYCZNE ---

    def rest_stmt(self, tree):
        """rest_stmt: KW_REST expression"""
        duration = self._evaluate(tree.children[1])
        self.current_track["events"].append({
            "type": "rest",
            "duration": duration
        })

    def tempo_stmt(self, tree):
        """tempo_stmt: KW_TEMPO expression"""
        bpm = self._evaluate(tree.children[1])
        if bpm <= 0:
            raise SemanticError(f"BPM musi być większe od zera! Podano: {bpm}")

        self.current_track["events"].append({
            "type": "tempo",
            "bpm": bpm
        })

    def instr_stmt(self, tree):
        """instr_stmt: KW_INSTR expression"""
        instr_id = self._evaluate(tree.children[1])
        if not (1 <= instr_id <= 128):
            raise SemanticError(f"Identyfikator instrumentu General MIDI musi być w zakresie 1-128. Podano: {instr_id}")

        self.current_track["events"].append({
            "type": "instrument",
            "id": instr_id
        })

    def loop_stmt(self, tree):
        """loop_stmt: KW_LOOP expression LBRACE statement* RBRACE"""
        iterations = self._evaluate(tree.children[1])


        statements_to_execute = []
        for child in tree.children[2:]:
            if isinstance(child, Tree):
                statements_to_execute.append(child)

        for _ in range(iterations):
            for stmt in statements_to_execute:
                self.visit(stmt)

    # --- OBSŁUGA WYRAŻEŃ ARYTMETYCZNYCH ---

    def expression(self, tree):
        """expression: term (OP_ARITH term)*"""
        result = self._evaluate(tree.children[0])
        i = 1
        while i < len(tree.children):
            op = tree.children[i].value
            next_val = self._evaluate(tree.children[i + 1])

            if op == '+':
                result += next_val
            elif op == '-':
                result -= next_val
            elif op == '*':
                result *= next_val
            elif op == '/':
                result = result // next_val
            i += 2
        return result

    def term(self, tree):
        """term: NUMBER | ID | LPAR expression RPAR """
        token = tree.children[0]
        if isinstance(token, Token) and token.type == 'NUMBER':
            return int(token.value)
        elif isinstance(token, Token) and token.type == 'ID':
            var_name = token.value
            if var_name not in self.variables:
                raise SemanticError(f"Użyto niezdefiniowanej zmiennej: '{var_name}'")
            return self.variables[var_name]
        else:
            return self._evaluate(tree.children[1])

    # --- UNIWERSALNA METODA POMOCNICZA ---

    def _evaluate(self, node_or_token):
        """Bezpiecznie wylicza wartość, obsługując również nuty i akordy przekazywane jako zmienne."""
        if isinstance(node_or_token, Token):
            if node_or_token.type == 'NUMBER':
                return int(node_or_token.value)
            elif node_or_token.type == 'ID':
                var_name = node_or_token.value
                if var_name not in self.variables:
                    raise SemanticError(f"Użyto niezdefiniowanej zmiennej: '{var_name}'")
                return self.variables[var_name]
            elif node_or_token.type == 'NOTE':
                return node_or_token.value
            return node_or_token.value

        if getattr(node_or_token, 'data', None) == 'chord':
            return [n.children[0].value for n in node_or_token.children if getattr(n, 'data', None) == 'note']

        return self.visit(node_or_token)

    def _get_pitch(self, target_node):
        """Pomocniczo wyciąga nutę, listę nut (akord) lub odczytuje je ze zmiennej."""
        if isinstance(target_node, Token) and target_node.type == 'ID':
            var_name = target_node.value
            if var_name not in self.variables:
                raise SemanticError(f"Zmienna dla nuty '{var_name}' nie została zdefiniowana!")

            pitch_val = self.variables[var_name]

            if isinstance(pitch_val, list):
                for p in pitch_val:
                    self._validate_note_octave(p)
            else:
                self._validate_note_octave(pitch_val)
            return pitch_val

        if target_node.data == 'note':
            pitch = target_node.children[0].value
            self._validate_note_octave(pitch)
            return pitch
        elif target_node.data == 'chord':
            pitch_list = []
            for n in target_node.children:
                if hasattr(n, 'data') and n.data == 'note':
                    note_val = n.children[0].value
                    self._validate_note_octave(note_val)
                    pitch_list.append(note_val)
            return pitch_list

    def _add_play_event(self, pitch, duration, velocity):
        """Dodaje sformatowane zdarzenie do aktualnego utworu."""
        self.current_track["events"].append({
            "type": "play",
            "pitch": pitch,
            "duration": duration,
            "velocity": velocity
        })

    def _validate_note_octave(self, note_str):
        """Sprawdza czy oktawa mieści się w standardowym zakresie muzycznym (0-8)."""
        match = re.match(r"[A-G][#b]?([0-9])", note_str)
        if match:
            octave = int(match.group(1))
            if octave > 8:
                raise SemanticError(f"Oktawa poza dopuszczalnym zakresem muzycznym (0-8): {note_str}")

        # --- IF ORAZ WARUNKI LOGICZNE ---

    def if_stmt(self, tree):
        """if_stmt: KW_IF LPAR condition RPAR LBRACE statement* RBRACE"""
        condition_node = tree.children[2]

        if self._eval_condition(condition_node):
            for child in tree.children:
                if isinstance(child, Tree) and child != condition_node:
                    self.visit(child)

    def _eval_condition(self, node):
        """Ewaluacja warunków logicznych zbudowanych z EBNF (and, or, ==, !=, >, < itp.)"""
        if isinstance(node, Token):
            return bool(self._evaluate(node))

        if node.data == 'or_test':
            for i in range(0, len(node.children), 2):
                if self._eval_condition(node.children[i]): return True
            return False

        if node.data == 'and_test':
            for i in range(0, len(node.children), 2):
                if not self._eval_condition(node.children[i]): return False
            return True

        if node.data == 'logical_not':
            return not self._eval_condition(node.children[1])  # children[0] to token KW_NOT

        if node.data == 'not_test':
            # postać: expression OP_COMP expression
            left = self._evaluate(node.children[0])
            op = node.children[1].value
            right = self._evaluate(node.children[2])

            if op == '==': return left == right
            if op == '!=': return left != right
            if op == '>': return left > right
            if op == '<': return left < right
            if op == '>=': return left >= right
            if op == '<=': return left <= right

        return bool(self._evaluate(node))

        # --- MAKRA I FUNKCJE ---

    def func_def(self, tree):
        """"func_def: KW_FUNC ID LPAR [parameters] RPAR LBRACE statement* RBRACE"""
        func_name = tree.children[1].value
        params = []

        # 1. Próba znalezienia węzła (jeśli Lark go nie zoptymalizował)
        param_nodes = list(tree.find_data('parameters'))
        if param_nodes:
            for child in param_nodes[0].children:
                if isinstance(child, Token) and child.type == 'ID':
                    params.append(child.value)
        else:
            # 2. Ręczne wyciągnięcie parametrów spomiędzy nawiasów LPAR i RPAR
            in_params = False
            for child in tree.children:
                if isinstance(child, Token) and child.type == 'LPAR':
                    in_params = True
                    continue
                if isinstance(child, Token) and child.type == 'RPAR':
                    break

                # Zbieramy tokeny typu ID (np. 'nuta_basowa', 'powtorzenia')
                if in_params and isinstance(child, Token) and child.type == 'ID':
                    params.append(child.value)

        # Ciało funkcji to wszystkie Drzewa (instrukcje), które nie są parametrami
        statements = [c for c in tree.children if isinstance(c, Tree) and c.data not in ('parameters', 'arguments')]

        self.functions[func_name] = {
            'params': params,
            'body': statements
        }

    def func_call(self, tree):
        """func_call: ID LPAR [arguments] RPAR"""
        func_name = tree.children[0].value
        if func_name not in self.functions:
            raise SemanticError(f"Próba wywołania nieznanej funkcji: '{func_name}'")

        func = self.functions[func_name]
        args = []

        # 1. Próba znalezienia węzła argumentów
        args_nodes = list(tree.find_data('arguments'))
        if args_nodes:
            for child in args_nodes[0].children:
                if getattr(child, 'type', None) != 'COMMA':
                    args.append(self._evaluate(child))
        else:
            # 2. Ręczne wyciągnięcie argumentów spomiędzy nawiasów LPAR i RPAR
            in_args = False
            for child in tree.children:
                if isinstance(child, Token) and child.type == 'LPAR':
                    in_args = True
                    continue
                if isinstance(child, Token) and child.type == 'RPAR':
                    break

                if in_args:
                    # Łapiemy wszystko co nie jest przecinkiem i ewaluujemy (np. zmienne, liczby, nuty)
                    if isinstance(child, Tree) or (isinstance(child, Token) and child.type != 'COMMA'):
                        args.append(self._evaluate(child))

        #Zabezpieczenie przed podaniem złej liczby argumentów
        if len(args) != len(func['params']):
            raise SemanticError(
                f"Funkcja '{func_name}' oczekuje {len(func['params'])} argumentów, podano {len(args)}.")

        # Izolacja zmiennych (scope)
        previous_vars = self.variables.copy()

        # Przypisujemy argumenty do odpowiednich zmiennych
        for param_name, arg_value in zip(func['params'], args):
            self.variables[param_name] = arg_value

        # Wykonujemy instrukcje wewnątrz makra
        for stmt in func['body']:
            self.visit(stmt)

        # Przywracamy zmienne
        self.variables = previous_vars