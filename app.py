import json
import sys

from compiler.midi_generator import generate_midi
from compiler.visitor import SynthScriptVisitor
from parser.parser import SynthScriptParser


def compile_synthscript(source_code_path, output_midi_path="song2.mid"):
    with open(source_code_path, 'r', encoding='utf-8') as f:
        code = f.read()

    print("analiza skladniowa w sumie parsowanie")
    parser = SynthScriptParser()
    ast = parser.parse(code)

    print("analiza semantyczna ")
    visitor = SynthScriptVisitor()
    music_data = visitor.program(ast)
    print(json.dumps(music_data, indent=2))

    print("Kompilowanie do pliku binarnego MIDI")
    generate_midi(music_data, output_midi_path)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        compile_synthscript(file_path)
    else:
        print("Podaj ścieżkę do pliku z kodem SynthScript, np.: python app.py piosenka.synth")