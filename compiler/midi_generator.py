from midiutil import MIDIFile


def text_to_midi_pitch(note_str):

    notes = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4,
             'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9,
             'A#': 10, 'Bb': 10, 'B': 11}

    import re
    match = re.match(r"([A-G][#b]?)([0-9])", note_str)
    if not match:
        return 60

    note_name, octave = match.groups()
    return 12 * (int(octave) + 1) + notes[note_name]


def generate_midi(music_data, output_filename="output.mid"):
    num_tracks = len(music_data["tracks"])
    midi_file = MIDIFile(num_tracks)

    velocity_map = {"pp": 30, "p": 50, "mp": 70, "mf": 90, "f": 110, "ff": 127}

    for track_idx, track in enumerate(music_data["tracks"]):
        time = 0.05
        midi_file.addTrackName(track_idx, time, track["name"])


        for event in track["events"]:
            if event["type"] == "tempo":
                midi_file.addTempo(track_idx, time, event["bpm"])

            elif event["type"] == "instrument":
                midi_file.addProgramChange(track_idx, 0, time, event["id"] - 1)

            elif event["type"] == "rest":

                duration_in_beats = 4 / event["duration"]
                time += duration_in_beats

            elif event["type"] == "play":
                duration_in_beats = 4 / event["duration"]

                vel_val = event["velocity"]
                vel = velocity_map.get(vel_val, 90) if isinstance(vel_val, str) else vel_val

                pitches = event["pitch"] if isinstance(event["pitch"], list) else [event["pitch"]]

                for p in pitches:
                    midi_pitch = text_to_midi_pitch(p)
                    midi_file.addNote(track_idx, 0, midi_pitch, time, duration_in_beats, vel)

                time += duration_in_beats
            elif event["type"] == "meter":
                num, den = map(int, event["value"].split("|"))
                import math
                den_power = int(math.log2(den))
                midi_file.addTimeSignature(track_idx, time, num, den_power, 24, 8)

    with open(output_filename, "wb") as output_file:
        midi_file.writeFile(output_file)