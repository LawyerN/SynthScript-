import customtkinter as ctk
import os
import re

from compiler.midi_generator import generate_midi
from compiler.visitor import SynthScriptVisitor
from parser.parser import SynthScriptParser

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SynthScriptApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SynthScript Studio")
        self.geometry("1100x680")

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=4)
        self.grid_rowconfigure(1, weight=1)

        # --- Podział na Layout ---
        self.editor_frame = ctk.CTkFrame(self)
        self.editor_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.editor_label = ctk.CTkLabel(self.editor_frame, text="Edytor SynthScript", font=("Arial", 16, "bold"))
        self.editor_label.pack(pady=(5, 0))

        self.status_file_label = ctk.CTkLabel(self.editor_frame, text="Otwarty plik: (Niezapisany skrypt)",
                                              font=("Arial", 11, "italic"), text_color="#aaaaaa")
        self.status_file_label.pack(pady=(0, 5))

        self.code_container = ctk.CTkFrame(self.editor_frame, fg_color="transparent")
        self.code_container.pack(expand=True, fill="both", padx=10, pady=5)

        self.code_editor = ctk.CTkTextbox(self.code_container, font=("Courier", 14), wrap="none")

        self.line_numbers = ctk.CTkTextbox(
            self.code_container,
            font=("Courier", 14),
            width=55,
            text_color="#777777",
            fg_color="#1d1d1d",
            wrap="none"
        )
        self.line_numbers.insert("0.0", "1")
        self.line_numbers.configure(state="disabled")

        self.line_numbers.pack(side="left", fill="y", padx=(0, 2))
        self.code_editor.pack(side="right", expand=True, fill="both")

        # --- Konfiguracja Kolorowania Składni (Tagi) ---
        self.setup_syntax_tags()

        # --- Bindy klawiszy i zdarzeń ---
        self.code_editor.bind("<KeyRelease>", self.on_content_changed)
        self.code_editor.bind("<MouseWheel>", lambda e: self.sync_scroll())
        self.code_editor.bind("<Configure>", lambda e: self.sync_line_numbers())
        self.code_editor.bind("<Tab>", self.insert_spaces_instead_of_tab)

        start_code = (
            "meter 2|4\n\n"
            "x = 2\n"
            "track \"Melodia\" {\n"
            "    instrument 1\n"
            "    tempo 130\n\n"
            "    loop x {\n"
            "        play B3 16 $f\n"
            "        play A3 16 $f\n"
            "        play G#3 16 $f\n"
            "        play A3 16 $f\n"
            "    }\n"
            "}"
        )
        self.code_editor.insert("0.0", start_code)
        self.highlight_syntax()
        self.sync_line_numbers()

        # --- Reszta komponentów UI (Kompilator, Pliki, Odtwarzacz) ---
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.control_label = ctk.CTkLabel(self.control_frame, text="Kompilator & Pliki", font=("Arial", 16, "bold"))
        self.control_label.pack(pady=5)

        self.filename_entry = ctk.CTkEntry(self.control_frame, placeholder_text="Nazwa (np. utwor)")
        self.filename_entry.pack(fill="x", padx=10, pady=5)
        self.filename_entry.insert(0, "utwor")

        self.btn_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=10, pady=5)

        self.run_btn = ctk.CTkButton(self.btn_frame, text="▶ KOMPILUJ", fg_color="#28a745",
                                     hover_color="#218838", command=self.compile_code, width=100)
        self.run_btn.pack(side="left", expand=True, padx=(0, 2))

        self.save_btn = ctk.CTkButton(self.btn_frame, text="💾 ZAPISZ KOD", fg_color="#17a2b8",
                                      hover_color="#138496", command=self.save_code, width=100)
        self.save_btn.pack(side="right", expand=True, padx=(2, 0))

        self.file_label = ctk.CTkLabel(self.control_frame, text="Przeglądarka projektu (kliknij plik):",
                                       font=("Arial", 12, "bold"))
        self.file_label.pack(pady=(10, 2), anchor="w", padx=10)

        self.file_list = ctk.CTkTextbox(self.control_frame, height=150, font=("Arial", 12), cursor="hand2")
        self.file_list.pack(fill="x", padx=10, pady=5)
        self.file_list.bind("<ButtonRelease-1>", self.on_file_select)

        self.player_label = ctk.CTkLabel(self.control_frame, text="Odtwarzacz", font=("Arial", 14, "bold"))
        self.player_label.pack(pady=(10, 0))

        self.status_midi_label = ctk.CTkLabel(self.control_frame, text="Wybrany utwór: (brak)",
                                              font=("Arial", 11, "italic"), text_color="#aaaaaa")
        self.status_midi_label.pack(pady=(0, 5))

        self.play_btn = ctk.CTkButton(self.control_frame, text="Odtwórz Wybrane MIDI", command=self.play_midi,
                                      state="disabled")
        self.play_btn.pack(fill="x", padx=10, pady=3)

        self.stop_btn = ctk.CTkButton(self.control_frame, text="Zatrzymaj", command=self.stop_midi, state="disabled",
                                      fg_color="#dc3545", hover_color="#c82333")
        self.stop_btn.pack(fill="x", padx=10, pady=3)

        self.console_frame = ctk.CTkFrame(self)
        self.console_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.console_label = ctk.CTkLabel(self.console_frame, text="Konsola wyjściowa", font=("Arial", 12, "bold"))
        self.console_label.pack(anchor="w", padx=10)

        self.console = ctk.CTkTextbox(self.console_frame, height=80, text_color="#00ff00", fg_color="black",
                                      font=("Consolas", 12))
        self.console.pack(expand=True, fill="both", padx=10, pady=(0, 10))
        self.console.insert("0.0", "System gotowy...\n")
        self.console.configure(state="disabled")

        self.refresh_file_list()

    # --- Logika Kolorowania Składni ---
    def setup_syntax_tags(self):
        # Pobieramy surowy obiekt tkinter schowany pod CustomTkinter
        textbox = self.code_editor._textbox
        textbox.tag_config("keyword", foreground="#ff79c6", font=("Courier", 14, "bold"))
        textbox.tag_config("note", foreground="#50fa7b")
        textbox.tag_config("velocity", foreground="#ffb86c")
        textbox.tag_config("comment", foreground="#6272a4", font=("Courier", 14, "italic"))
        textbox.tag_config("string", foreground="#f1fa8c")
        textbox.tag_config("number", foreground="#bd93f9")

    def highlight_syntax(self):
        textbox = self.code_editor._textbox

        # Usuwamy stare tagi przed ponownym kolorowaniem
        for tag in ["keyword", "note", "velocity", "comment", "string", "number"]:
            textbox.tag_remove(tag, "1.0", "end")

        code = textbox.get("1.0", "end-1c")

        # Definicje regexów odpowiadające tokenom z EBNF
        rules = [
            ("comment", r"//.*"),
            ("string", r'"[^"]*"'),
            ("keyword", r"\b(play|track|meter|rest|loop|if|tempo|instrument)\b"),
            ("note", r"\b[A-G](#|b)?[0-9]\b"),
            ("velocity", r"\$(pp|p|mp|mf|f|ff)\b"),
            ("number", r"\b[0-9]+\b")
        ]

        # Przeszukiwanie linii po linii i aplikowanie stylów
        for tag_name, regex in rules:
            for match in re.finditer(regex, code):
                start_idx = f"1.0 + {match.start()} chars"
                end_idx = f"1.0 + {match.end()} chars"
                textbox.tag_add(tag_name, start_idx, end_idx)

    def on_content_changed(self, event):
        # Wywoływane przy puszczeniu klawisza - aktualizuje cyfry i kolory
        self.sync_line_numbers()
        self.highlight_syntax()

    # --- Obsługa Edytora i Synchronizacji ---
    def log_to_console(self, text, is_error=False):
        self.console.configure(state="normal")
        if is_error:
            self.console.insert("end", f"[BŁĄD] {text}\n")
        else:
            self.console.insert("end", f"> {text}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def sync_line_numbers(self):
        total_lines = int(self.code_editor.index("end-1c").split(".")[0])
        lines_string = "\n".join(str(i) for i in range(1, total_lines + 1))

        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("0.0", "end")
        self.line_numbers.insert("0.0", lines_string)
        self.line_numbers.configure(state="disabled")
        self.sync_scroll()

    def sync_scroll(self):
        y_scroll_pos = self.code_editor._textbox.yview()
        self.line_numbers._textbox.yview_moveto(y_scroll_pos[0])

    def insert_spaces_instead_of_tab(self, event):
        self.code_editor.insert("insert", "    ")
        self.on_content_changed(None)
        return "break"

    def refresh_file_list(self):
        self.file_list.configure(state="normal")
        self.file_list.delete("0.0", "end")

        self.file_list._textbox.tag_config("synth_file", foreground="#3b8ed0")
        self.file_list._textbox.tag_config("midi_file", foreground="#28a745")

        pliki = [f for f in os.listdir(".") if f.endswith((".mid", ".synth"))]
        if not pliki:
            self.file_list.insert("end", "(Brak odpowiednich plików w katalogu)")
        else:
            for plik in sorted(pliki):
                if plik.endswith(".synth"):
                    self.file_list._textbox.insert("end", f"{plik}\n", "synth_file")
                elif plik.endswith(".mid"):
                    self.file_list._textbox.insert("end", f"{plik}\n", "midi_file")

        self.file_list.configure(state="disabled")

    def save_code(self):
        name_input = self.filename_entry.get().strip()
        if not name_input:
            self.log_to_console("Podaj nazwę pliku przed zapisem!", is_error=True)
            return

        base_name = os.path.splitext(os.path.splitext(name_input)[0])[0]
        script_name = base_name + ".synth"

        try:
            with open(script_name, "w", encoding="utf-8") as f:
                f.write(self.code_editor.get("0.0", "end").strip())
            self.log_to_console(f"Skrypt zapisany pomyślnie jako: {script_name}")
            self.status_file_label.configure(text=f"Otwarty plik: {script_name}", text_color="#00ff00")
            self.refresh_file_list()
        except Exception as e:
            self.log_to_console(f"Nie udało się zapisać pliku: {e}", is_error=True)

    def on_file_select(self, event):
        try:
            clicked_index = self.file_list.index(f"@{event.x},{event.y}")
            line_start = clicked_index.split(".")[0]
            selected_file = self.file_list.get(f"{line_start}.0", f"{line_start}.end").strip()

            if not selected_file or selected_file.startswith("("):
                return

            base_name = os.path.splitext(selected_file)[0]
            self.filename_entry.delete(0, "end")
            self.filename_entry.insert(0, base_name)

            if selected_file.endswith(".synth"):
                with open(selected_file, "r", encoding="utf-8") as f:
                    self.code_editor.delete("0.0", "end")
                    self.code_editor.insert("0.0", f.read())
                self.log_to_console(f"Wczytano kod ze skryptu: {selected_file}")
                self.status_file_label.configure(text=f"Otwarty plik: {selected_file}", text_color="#28a745")
                self.on_content_changed(None)

                self.status_midi_label.configure(text="Wybrany utwór: (brak)", text_color="#aaaaaa")
                self.play_btn.configure(state="disabled")

            elif selected_file.endswith(".mid"):
                self.log_to_console(f"Zaznaczono utwór MIDI: {selected_file}. Możesz go teraz odtworzyć.")
                self.status_midi_label.configure(text=f"Wybrany utwór: {selected_file}", text_color="#3b8ed0")

                self.play_btn.configure(state="normal")
                self.stop_btn.configure(state="normal")

        except Exception as e:
            pass

    def compile_code(self):
        code = self.code_editor.get("0.0", "end").strip()
        name_input = self.filename_entry.get().strip()

        base_name = os.path.splitext(os.path.splitext(name_input)[0])[0]
        filename = base_name + ".mid"

        self.log_to_console("Rozpoczynam analizę składniową...")

        try:
            parser = SynthScriptParser()
            ast = parser.parse(code)
            self.log_to_console("Składnia poprawna. Uruchamiam analizę semantyczną...")

            visitor = SynthScriptVisitor()
            music_data = visitor.program(ast)

            generate_midi(music_data, filename)

            self.log_to_console(f"SUKCES! Wygenerowano plik binarny: {filename}")
            self.status_midi_label.configure(text=f"Wybrany utwór: {filename}", text_color="#28a745")

            self.refresh_file_list()
            self.play_btn.configure(state="normal")
            self.stop_btn.configure(state="normal")

        except Exception as e:
            self.log_to_console(str(e), is_error=True)

    def play_midi(self):
        name_input = self.filename_entry.get().strip()
        base_name = os.path.splitext(os.path.splitext(name_input)[0])[0]
        filename = base_name + ".mid"

        if os.path.exists(filename):
            try:
                full_path = os.path.abspath(filename)
                self.log_to_console(f"Odtwarzanie pliku: {filename}...")

                import subprocess

                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0

                command = f'cmd.exe /c start /min "" "{full_path}"'

                self.player_process = subprocess.Popen(
                    command,
                    shell=False,
                    startupinfo=startupinfo
                )

                self.log_to_console("Muzyka gra prosto z systemu!")
                self.stop_btn.configure(state="normal")
            except Exception as e:
                self.log_to_console(f"Błąd odtwarzacza: {e}", is_error=True)
        else:
            self.log_to_console(f"Plik {filename} nie istnieje!", is_error=True)

    def stop_midi(self):
        import subprocess
        try:
            subprocess.run('taskkill /f /im wmplayer.exe', shell=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            subprocess.run('taskkill /f /im Microsoft.Media.Player.exe', shell=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except:
            pass

        self.log_to_console("Zatrzymano muzykę.")


if __name__ == "__main__":
    app = SynthScriptApp()
    app.mainloop()