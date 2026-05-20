import pretty_midi
import subprocess
import os
from pydub import AudioSegment

# ================= CONFIGURATION =================
SOUNDFONT_PATH = "FluidR3_GM.sf2"  
OUTPUT_DIR = "dataset_wav-04-2s-FluidR3"             
INSTRUMENT_PROGRAM_START = 2
INSTRUMENT_PROGRAM_LAST = 3
VELOCITY = 100                         
DURATION = 2.0                         # Durée voulue par note
NOTE_MIN = 36                          
NOTE_MAX = 42                          
MARGIN = 2.0                           # Marge de silence entre chaque note pour éviter qu'elles ne se chevauchent
# =================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

for instru in range(INSTRUMENT_PROGRAM_START, INSTRUMENT_PROGRAM_LAST+1):
    
    # 1. Créer UN SEUL objet MIDI pour toutes les notes
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=instru)

    print("1/3 : Création de la partition MIDI globale...")
    current_time = 0.0

    for pitch in range(NOTE_MIN, NOTE_MAX + 1):
        note = pretty_midi.Note(
            velocity=VELOCITY, 
            pitch=pitch, 
            start=current_time, 
            end=current_time + DURATION
        )
        instrument.notes.append(note)
        
        # On avance le temps pour la prochaine note (Durée + un peu de silence)
        current_time += (DURATION + MARGIN)

    midi.instruments.append(instrument)
    temp_midi_path = "temp_all_notes.mid"
    midi.write(temp_midi_path)

    # 2. Lancer FluidSynth UNE SEULE FOIS pour tout rendre
    temp_wav_path = "temp_all_notes.wav"
    command =[
        "fluidsynth", "-ni", 
        "-R", "0", "-C", "0", 
        "-F", temp_wav_path, 
        SOUNDFONT_PATH, temp_midi_path
    ]

    print("2/3 : Génération de l'audio par FluidSynth (Calcul en arrière-plan...)")

    # Astuce spéciale Windows : Masquer totalement la fenêtre d'invite de commande
    creationflags = 0
    if os.name == 'nt':  # Si on est sur Windows
        creationflags = 0x08000000 # CREATE_NO_WINDOW

    subprocess.run(
        command, 
        check=True, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL,
        creationflags=creationflags # Empêche la fenêtre de popper !
    )

    # 3. Découper le grand fichier WAV en petits fichiers de 2 secondes
    print("3/3 : Découpage et normalisation des fichiers...")
    full_audio = AudioSegment.from_wav(temp_wav_path)

    current_time_ms = 0
    target_duration_ms = int(DURATION * 1000)
    step_ms = int((DURATION + MARGIN) * 1000)

    for pitch in range(NOTE_MIN, NOTE_MAX + 1):
        # Extraire la bonne portion du gros fichier audio
        slice_audio = full_audio[current_time_ms : current_time_ms + target_duration_ms]
        
        # Appliquer le fondu de fermeture
        slice_audio = slice_audio.fade_out(150)
        
        # Sauvegarder la note individuelle
        output_wav = os.path.join(OUTPUT_DIR, f"inst_{instru}_note_{pitch}.wav")
        slice_audio.export(output_wav, format="wav")
        
        # Avancer au prochain bloc
        current_time_ms += step_ms

    # 4. Nettoyer les gros fichiers temporaires
    if os.path.exists(temp_midi_path):
        os.remove(temp_midi_path)
    if os.path.exists(temp_wav_path):
        os.remove(temp_wav_path)

print("Terminé ! Vous pouvez utiliser votre ordinateur tranquillement :)")
