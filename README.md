# SynthScript-
### Dane
Bartosz Gdowski (bgdowski@student.agh.edu.pl)
Karol Jachym (kjachym@student.agh.edu.pl)

## Ogólne cele programu:
Głównym celem jest stworzenie języka pozwalającego na programowe opisywanie struktur muzycznych (melodii, rytmu, akordów) i ich natychmiastową interpretację. Język ma wspierać:

- Definiowanie sekwencji nutowych i rytmicznych.

- Instrukcje sterujące, takie jak pętle i instrukcje warunkowe, pozwalające na tworzenie dynamicznych kompozycji.

- Zarządzanie tempem (BPM) i barwą dźwięku (wybór instrumentów).

- Analizę semantyczną: sprawdzanie poprawności muzycznej (np. zakresy oktaw, poprawność wartości rytmicznych).

## Rodzaj translatora: Interpreter. 
Program będzie działał w trybie ciągłym, parsując instrukcje użytkownika i wykonując je bezpośrednio za pomocą silnika dźwiękowego bez generowania pośredniego pliku binarnego.

## Planowany wynik działania programu: 
Interpreter, który na podstawie kodu źródłowego generuje w czasie rzeczywistym komunikaty MIDI, przesyłane do wirtualnego syntezatora w systemie (np. systemowy MIDI Synth lub DAW typu Ableton/FL Studio). Użytkownik słyszy efekt pracy kodu natychmiast po jego uruchomieniu.

- Planowany język implementacji: Python 

Sposób realizacji skanera/parsera: Użycie biblioteki Lark (dla Pythona). Gramatyka zostanie zdefiniowana w formacie EBNF. Wykorzystany zostanie parser typu LALR, który wygeneruje drzewo składniowe (AST). Następnie wzorzec projektowy Visitor przejdzie po drzewie, wykonując analizę semantyczną i generując zdarzenia dźwiękowe.
