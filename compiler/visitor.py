import re
from lark.visitors import Interpreter
from lark import Token


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
        self.current_track = None

    def program(self, tree):
        """Punkt startowy programu."""
        meter_node = tree.find_data('meter_stmt')
        for m in meter_node:
            self.visit(m)

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

        for _ in range(iterations):
            for child in tree.children:
                # Wykonujemy instrukcje pomijając węzeł przechowujący warunek pętli
                if hasattr(child, 'data') and child.data != 'expression':
                    self.visit(child)

    # --- OBSŁUGA WYRAŻEŃ ARYTMETYCZNYCH ---

    def expression(self, tree):
        """expression: term (OP_ARITH term)*"""
        result = self.visit(tree.children[0])
        i = 1
        while i < len(tree.children):
            op = tree.children[i].value
            next_val = self.visit(tree.children[i + 1])

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
            return self.visit(tree.children[1])

    # --- UNIWERSALNA METODA POMOCNICZA ---

    def _evaluate(self, node_or_token):
        """Bezpiecznie wylicza wartość niezależnie od tego, czy Lark zwrócił zoptymalizowany Token czy Tree."""
        if isinstance(node_or_token, Token):
            if node_or_token.type == 'NUMBER':
                return int(node_or_token.value)
            elif node_or_token.type == 'ID':
                var_name = node_or_token.value
                if var_name not in self.variables:
                    raise SemanticError(f"Użyto niezdefiniowanej zmiennej: '{var_name}'")
                return self.variables[var_name]
            return node_or_token.value

        return self.visit(node_or_token)

    def _get_pitch(self, target_node):
        """Pomocniczo wyciąga nutę lub listę nut (akord) z drzewa."""
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