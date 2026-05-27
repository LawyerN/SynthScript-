# SynthScript- język do algorytmicznej kompozycji i syntezy muzyki
### Dane
Bartosz Gdowski (bgdowski@student.agh.edu.pl)
Karol Jachym (kjachym@student.agh.edu.pl)

## Ogólne cele programu:
Głównym celem jest stworzenie języka (DSL) pozwalającego na programowe opisywanie struktur muzycznych (melodii, rytmu, akordów) i ich kompilację do standardowego formatu cyfrowego. Język ma wspierać:

- Definiowanie sekwencji nutowych i rytmicznych.

- Instrukcje sterujące, takie jak pętle i instrukcje warunkowe, pozwalające na algorytmiczne tworzenie rozbudowanych kompozycji.

- Zarządzanie tempem (BPM) i barwą dźwięku (wybór instrumentów w standardzie General MIDI).

- Analizę semantyczną: sprawdzanie poprawności muzycznej (np. weryfikacja poprawności wartości rytmicznych względem założonego metrum, sprawdzanie czy nuty mieszczą się w dopuszczalnych zakresach oktaw).

## Rodzaj translatora: Kompilator. 
Program będzie działał jako kompilator (źródło -> plik binarny), który analizuje cały kod wejściowy napisany przez użytkownika, wylicza odpowiednie czasy (timing) i generuje docelowy plik muzyczny bez konieczności bezpośredniego sterowania sprzętem w czasie rzeczywistym.
## Planowany wynik działania programu: 
Kompilator, który na podstawie kodu źródłowego generuje gotowy, binarny plik muzyczny w standardzie MIDI (.mid). Wygenerowany plik może zostać odtworzony w dowolnym systemowym odtwarzaczu multimedialnym lub zaimportowany bezpośrednio do programów typu DAW (np. Ableton, FL Studio) w celu odsłuchu lub przypisania bardziej zaawansowanych brzmień.

- Planowany język implementacji: Python 

Sposób realizacji skanera/parsera: Użycie biblioteki Lark (dla Pythona). Gramatyka zostanie zdefiniowana w formacie EBNF. Wykorzystany zostanie parser typu LALR(1), który na podstawie analizy wygeneruje drzewo składniowe (AST). Następnie zaimplementowany wzorzec projektowy Visitor przejdzie po węzłach drzewa, wykona analizę semantyczną (walidację muzyczną) i na podstawie zebranych instrukcji zbuduje strukturę zdarzeń, która ostatecznie zostanie zapisana do wynikowego pliku MIDI.

### Opis tokenów (Skaner)

| Nazwa tokenu     | Wzorzec (RegEx / Znak)                       | Opis i zastosowanie w SynthScript                                                                                            | Przykłady              |
|:-----------------|:---------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------|:-----------------------|
| `KW_PLAY`        | `"play"`                                     | Słowo kluczowe wywołujące odtworzenie nuty lub akordu.                                                                       | `play`                 |
| `KW_TRACK`       | `"track"`                                    | Słowo kluczowe rozpoczynające blok definicji ścieżki dla danego instrumentu.                                                 | `track`                |
| `KW_METER`       | `"meter"`                                    | Słowo kluczowe definiujące globalne metrum utworu.                                                                           | `meter`                |
| `KW_REST`        | `"rest"`                                     | Słowo kluczowe oznaczające pauzę muzyczną.                                                                                   | `rest`                 |
| `KW_LOOP`        | `"loop"`                                     | Słowo kluczowe rozpoczynające pętlę.                                                                                         | `loop`                 |
| `KW_IF`          | `"if"`                                       | Słowo kluczowe instrukcji warunkowej.                                                                                        | `if`                   |
| `KW_TEMPO`       | `"tempo"`                                    | Słowo kluczowe do globalnej zmiany BPM.                                                                                      | `tempo`                |
| `KW_INSTR`       | `"instrument"`                               | Słowo kluczowe zmiany instrumentu (barwy dźwięku).                                                                           | `instrument`           |
| `NOTE`           | `/[A-G](#\|b)?[0-9]/`                        | Literał nuty: litera A-G, opcjonalny krzyżyk/bemol i oktawa.                                                                 | `C4`, `F#5`, `Bb3`     |
| `VELOCITY_LABEL` | `/(pp\|p\|mp\|mf\|f\|ff)/`                   | Symbole głośności.                                                                                                           | `f`, `pp`              |
| `NUMBER`         | `/[0-9]+/`                                   | Literał liczbowy całkowity. Służy do określania m.in. BPM, liczby iteracji w pętli oraz wartości rytmicznych (np. 4, 8, 16). | `120`, `16`, `4`       |
| `ID`             | `/[a-zA-Z_][a-zA-Z0-9_]*/`                   | Identyfikator (nazwa zmiennej wprowadzana przez użytkownika).                                                                | `licznik`, `moja_nuta` |
| `OP_ASSIGN`      | `"="`                                        | Operator przypisania.                                                                                                        | `=`                    |
| `OP_COMP`        | `"==" \| "!=" \| ">" \| "<" \| ">=" \| "<="` | Operatory relacyjne do sprawdzania warunków.                                                                                 | `==`, `>=`             |
| `OP_ARITH`       | `"+" \| "-" \| "*" \| "/"`                   | Operatory arytmetyczne do operacji na zmiennych.                                                                             | `+`, `-`               |
| `LBRACE`         | `"{"`                                        | Lewa klamra otwierająca blok kodu (np. w pętli).                                                                             | `{`                    |
| `RBRACE`         | `"}"`                                        | Prawa klamra zamykająca blok kodu.                                                                                           | `}`                    |
| `LBRACKET`       | `"["`                                        | Lewy nawias kwadratowy otwierający definicję akordu.                                                                         | `[`                    |
| `RBRACKET`       | `"]"`                                        | Prawy nawias kwadratowy zamykający definicję akordu.                                                                         | `]`                    |
| `BAR`            | `"\|"`                                       | Separator licznika i mianownika w metrum.                                                                                    | `\|`                   |
| `COMMA`          | `","`                                        | Przecinek jako separator nut wewnątrz akordu.                                                                                | `,`                    |
| `KW_FUNC`        | `"func"`                                     | Słowo kluczowe rozpoczynające definicję makra.                                                                               | `func`                 |
| `KW_AND`         | `"and"`                                      | Operator logiczny koniunkcji (oraz) używany w warunkach złożonych.                                                           | `and`                  |
| `KW_OR`          | `"or"`                                       | Operator logiczny alternatywy (lub) używany w warunkach złożonych.                                                           | `or`                   |
| `KW_NOT`         | `"not"`                                      | Operator logiczny negacji (nie) używany w warunkach złożonych.                                                               | `not`                  |
| `STRING`         | `/"[^"]*"/`                                  | Literał tekstowy w podwójnym cudzysłowie (służy do nazywania ścieżek).                                                       | `"Bas"`, `"Piano"`     |
| `LPAR`           | `"("`                                        | Lewy nawias okrągły (grupowanie wyrażeń, parametry funkcji, warunki if).                                                     | `(`                    |
| `RPAR`           | `")"`                                        | Prawy nawias okrągły zamykający.                                                                                             | `)`                    |
**Dodatkowe zasady (Ignorowane przez parser):**
* **Białe znaki:** Spacje, tabulatory i znaki nowej linii (`/[ \t\n\r]+/`) są ignorowane przez skaner.
* **Komentarze:** Linie zaczynające się od `//` są ignorowane, co pozwala użytkownikowi dokumentować swój kod.

### Gramatyka języka (Lark EBNF)

Poniżej znajduje się kompletna gramatyka wykorzystywana przez kompilator:

```ebnf
?start: program

program: meter_stmt? func_def* track+

track: KW_TRACK STRING LBRACE statement* RBRACE

func_def: KW_FUNC ID LPAR [parameters] RPAR LBRACE statement* RBRACE
parameters: ID (COMMA ID)*

?statement: assignment
          | play_stmt
          | rest_stmt
          | tempo_stmt
          | instr_stmt
          | loop_stmt
          | if_stmt
          | func_call

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

func_call: ID LPAR [arguments] RPAR
arguments: expression (COMMA expression)*

note: NOTE

chord: LBRACKET note (COMMA note)* RBRACKET

?condition: or_test

?or_test: and_test (KW_OR and_test)*
?and_test: not_test (KW_AND not_test)*
?not_test: KW_NOT not_test -> logical_not
         | expression OP_COMP expression
         | LPAR condition RPAR

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
KW_FUNC: "func"

KW_AND: "and"
KW_OR: "or"
KW_NOT: "not"

NOTE.2: /[A-G](#|b)?[0-9]/
VELOCITY_LABEL.2: "pp" | "p" | "mp" | "mf" | "f" | "ff"

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