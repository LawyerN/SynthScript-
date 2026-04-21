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

| Nazwa tokenu | Wzorzec (RegEx / Znak) | Opis i zastosowanie w SynthScript | Przykłady |
| :--- | :--- | :--- | :--- |
| `KW_PLAY` | `"play"` | Słowo kluczowe wywołujące odtworzenie nuty lub akordu. | `play` |
| `KW_REST` | `"rest"` | Słowo kluczowe oznaczające pauzę muzyczną. | `rest` |
| `KW_LOOP` | `"loop"` | Słowo kluczowe rozpoczynające pętlę. | `loop` |
| `KW_IF` | `"if"` | Słowo kluczowe instrukcji warunkowej. | `if` |
| `KW_TEMPO` | `"tempo"` | Słowo kluczowe do globalnej zmiany BPM. | `tempo` |
| `KW_INSTR` | `"instrument"` | Słowo kluczowe zmiany instrumentu (barwy dźwięku). | `instrument` |
| `NOTE` | `/[A-G](#\|b)?[0-9]/` | Literał nuty: litera A-G, opcjonalny krzyżyk/bemol i oktawa. | `C4`, `F#5`, `Bb3` |
| `NUMBER` | `/[0-9]+/` | Literał liczbowy całkowity. Służy do określania m.in. BPM, liczby iteracji w pętli oraz wartości rytmicznych (np. 4, 8, 16). | `120`, `16`, `4` |
| `ID` | `/[a-zA-Z_][a-zA-Z0-9_]*/` | Identyfikator (nazwa zmiennej wprowadzana przez użytkownika). | `licznik`, `moja_nuta` |
| `OP_ASSIGN` | `"="` | Operator przypisania. | `=` |
| `OP_COMP` | `"==" \| "!=" \| ">" \| "<" \| ">=" \| "<="`| Operatory relacyjne do sprawdzania warunków. | `==`, `>=` |
| `OP_ARITH` | `"+" \| "-" \| "*" \| "/"` | Operatory arytmetyczne do operacji na zmiennych. | `+`, `-` |
| `LBRACE` | `"{"` | Lewa klamra otwierająca blok kodu (np. w pętli). | `{` |
| `RBRACE` | `"}"` | Prawa klamra zamykająca blok kodu. | `}` |
| `LBRACKET` | `"["` | Lewy nawias kwadratowy otwierający definicję akordu. | `[` |
| `RBRACKET` | `"]"` | Prawy nawias kwadratowy zamykający definicję akordu. | `]` |
| `COMMA` | `","` | Przecinek jako separator nut wewnątrz akordu. | `,` |

**Dodatkowe zasady (Ignorowane przez parser):**
* **Białe znaki:** Spacje, tabulatory i znaki nowej linii (`/[ \t\n\r]+/`) są ignorowane przez skaner.
* **Komentarze:** Linie zaczynające się od `//` są ignorowane, co pozwala użytkownikowi dokumentować swój kod.
