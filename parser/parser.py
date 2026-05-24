from lark import Lark

SYNTH_SCRIPT_GRAMMAR = r"""
?start: program

program: meter_stmt? track+

track: KW_TRACK STRING LBRACE statement* RBRACE

?statement: assignment
          | play_stmt
          | rest_stmt
          | tempo_stmt
          | instr_stmt
          | loop_stmt
          | if_stmt
          | meter_stmt

meter_stmt: KW_METER NUMBER BAR NUMBER

assignment: ID OP_ASSIGN expression

play_stmt: KW_PLAY (note | chord)                   -> play_default
         | KW_PLAY (note | chord) expression         -> play_dur
         | KW_PLAY (note | chord) expression expression -> play_dur_vel_num
         | KW_PLAY (note | chord) expression VELOCITY_LABEL -> play_dur_vel_lab
         | KW_PLAY (note | chord) VELOCITY_LABEL    -> play_vel_label

rest_stmt: KW_REST expression

tempo_stmt: KW_TEMPO expression

instr_stmt: KW_INSTR expression

loop_stmt: KW_LOOP expression LBRACE statement* RBRACE

if_stmt: KW_IF LPAR condition RPAR LBRACE statement* RBRACE

note: NOTE

chord: LBRACKET note (COMMA note)* RBRACKET

condition: expression OP_COMP expression

?expression: term (OP_ARITH term)*

?term: NUMBER
     | ID
     | LPAR expression RPAR

// --- TERMINALE (TOKENY) ---

KW_PLAY: "play"
KW_TRACK: "track"
KW_METER: "meter"
KW_REST: "rest"
KW_LOOP: "loop"
KW_IF: "if"
KW_TEMPO: "tempo"
KW_INSTR: "instrument"

NOTE.2: /[A-G](#|b)?[0-9]/

# Dodajemy prefiks $, aby lekser nigdy nie pomylił głośności ze zmienną ID
VELOCITY_LABEL: "$pp" | "$p" | "$mp" | "$mf" | "$f" | "$ff"

NUMBER: /[0-9]+/
STRING: /"[^"]*"/
ID: /[a-zA-Z_][a-zA-Z0-9_]*/

BAR: "|"
OP_ASSIGN: "="
OP_COMP: "==" | "!=" | ">" | "<" | ">=" | "<="
OP_ARITH: "+" | "-" | "*" | "/"

LBRACE: "{"
RBRACE: "}"
LBRACKET: "["
RBRACKET: "]"
LPAR: "("
RPAR: ")"
COMMA: ","

%import common.WS
%ignore WS

COMMENT: /\/\/.*/
%ignore COMMENT
"""

class SynthScriptParser:
    def __init__(self):
        self.parser = Lark(SYNTH_SCRIPT_GRAMMAR, parser='lalr', start='program')

    def parse(self, code_text):
        return self.parser.parse(code_text)