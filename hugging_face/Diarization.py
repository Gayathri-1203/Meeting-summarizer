import os
import whisperx
import gc

def transcribe_audio_files(folder_path):
    model = whisperx.load_model("large-v2", "cpu", compute_type="float32")
    device = "cpu"
    diarize_model = whisperx.DiarizationPipeline(use_auth_token="token", device=device)

    for file_name in os.listdir(folder_path):
        if file_name.endswith(('.wav', '.mp3')):
            audio_file_path = os.path.join(folder_path, file_name)
            print(f"Processing file: {audio_file_path}")

            audio = whisperx.load_audio(audio_file_path)

            result = model.transcribe(audio)

            model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)

            result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)

            output_file = os.path.join(folder_path, f"{os.path.splitext(file_name)[0]}_transcription.txt")
            with open(output_file, "w") as file:
                for segment in result["segments"]:
                    start = int(segment['start'])
                    end = int(segment['end'])
                    file.write(f"Speaker: {segment['speaker']}, Start: {start}, End: {end},\n Text: {segment['text']}\n")
                    file.write("\n")

            print(f"Output saved to {output_file}")

    gc.collect()

