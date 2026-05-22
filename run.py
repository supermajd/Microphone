
"""transcribe.py: Transcribes audio files from the audio folder using OpenAI Whisper."""

__author__ = "Majd Jamal"

import re
import shutil
from pathlib import Path
from datetime import date

from openai import OpenAI
from pydub import AudioSegment

from dotenv import load_dotenv
from args import parse_args, get_metadata

load_dotenv()

SUPPORTED_FORMATS = {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm'}
MAX_FILE_SIZE_MB = 20
MAX_AUDIO_SECONDS = 1400          
CHUNK_SECONDS = 1200            


class Microphone:
    """
    Audio Transcriber
    """

    def __init__(self, speaker, description, date, subject):
        """ Initializes the transcriber with recording metadata.
        :param speaker: Name of the speaker
        :param description: Short description of the recording
        :param date: Recording date
        :param subject: Subject of the recording
        """

        self.speaker = speaker
        self.description = description
        self.date = date
        self.subject = subject

        self.model = 'gpt-4o-transcribe'
        self.client = OpenAI()

    def chunker(self, audio: Path) -> list:
        """ Chunks the audio file so that it matches the requirements.
        :param audio: Path to the audio file, which is by default data/audio
        :return chunks: A list of chunks
        """ 
        sound = AudioSegment.from_file(str(audio))
        total_ms = len(sound)

        # Chunk by DURATION, not file size: gpt-4o-transcribe caps audio at 1400 s.
        chunk_ms = CHUNK_SECONDS * 1000

        chunks_dir = Path('data/chunks')
        chunks_dir.mkdir(parents=True, exist_ok=True)
        for f in chunks_dir.iterdir():
            if f.is_file():
                f.unlink()

        chunks = []
        for i, start in enumerate(range(0, total_ms, chunk_ms)):
            end = min(start + chunk_ms, total_ms)
            segment = sound[start:end]
            chunk_path = chunks_dir / f"chunk_{i:03d}.mp3"
            segment.export(str(chunk_path), format='mp3', bitrate='128k')
            chunks.append(chunk_path)

        print(f'Created {len(chunks)} chunks')
        return chunks
        
    def transcribe(self, audio_path: Path, prompt: str = "") -> str:
        """ Transcribes a single audio file.
        :param audio_path: Path to the audio file
        :param prompt: Optional context prompt to guide the model
        :return text: Transcribed text
        """

        with open(audio_path, 'rb') as audio_file:

            response = self.client.audio.transcriptions.create(
                model = self.model,
                file = audio_file,
                prompt = prompt)

        text = response.text

        return text

    def organize(self, text: str) -> str:
        """ Organizes the transcribed text into paragraphs
        and places metadata at the top.
        :param text: Raw transcribed text
        :return organized: Final transcript with metadata header and paragraphs
        """

        if not text:
            raise ValueError('Cannot organize an empty transcript.')

        # Build metadata header
        header_lines = []

        if self.subject:
            header_lines.append(f'Subject: {self.subject}')

        if self.speaker:
            header_lines.append(f'Speaker: {self.speaker}')

        if self.date:
            header_lines.append(f'Date: {self.date}')

        if self.description:
            header_lines.append(f'Description: {self.description}')

        header = '\n'.join(header_lines)

        # Split transcript into sentences, then group into paragraphs
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        sentences_per_paragraph = 5
        paragraphs = []

        for i in range(0, len(sentences), sentences_per_paragraph):

            paragraph = ' '.join(sentences[i:i + sentences_per_paragraph])
            paragraphs.append(paragraph)

        body = '\n\n'.join(paragraphs)

        if header:
            organized = f'{header}\n\n{body}'
        else:
            organized = body

        return organized

    def save(self, text: str, audio_path: Path, txt_dir: Path = Path('data/txt')) -> Path:
        """ Saves the transcribed text to a .txt file in the output folder.
        The filename matches the input audio file's name.
        :param text: Transcribed text to save
        :param audio_path: Path to the source audio file (used for the filename)
        :param txt_dir: Folder to write the transcript into
        :return path: Path to the saved transcript
        """

        txt_dir.mkdir(parents=True, exist_ok=True)

        filename = f'{audio_path.stem}.txt'   # e.g. interview_filippa.wav -> interview_filippa.txt

        path = txt_dir / filename
        path.write_text(text, encoding='utf-8')

        print(f'Saved transcript to {path}')

        return path


def archive_previous_transcripts(
        txt_dir: Path = Path('data/txt'),
        history_dir: Path = Path('data/history/txt')) -> None:
    """ Moves existing transcripts from the txt folder into history.
    :param txt_dir: Folder holding current transcripts
    :param history_dir: Folder where old transcripts are archived
    """

    if not txt_dir.exists():
        return

    history_dir.mkdir(parents = True, exist_ok = True)

    files = [f for f in txt_dir.iterdir() if f.is_file()]

    for f in files:
        shutil.move(str(f), str(history_dir / f.name))


def load_audio(audio_dir: Path = Path('data/audio')) -> Path:
    """ Loads the audio file from the audio folder.
    :param audio_dir: Folder holding the audio file
    :return path: Path to the audio file
    """

    if not audio_dir.exists():
        raise ValueError(f'Audio folder not found: {audio_dir}')

    path = next(
        (f for f in audio_dir.iterdir()
         if f.is_file() and not f.name.startswith('.')),
        None)

    if path is None:
        raise ValueError(f'No audio file found in {audio_dir}')

    return path


def validate_audio(path: Path) -> bool:
    """ Validates the audio file against the Whisper API criteria.
    Raises ValueError for unsupported formats. Returns whether the file
    needs chunking based on the 20 MB size limit.
    :param path: Path to the audio file
    :return needs_chunking: True if the file exceeds the size limit
    """

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(
            f'Unsupported audio format: {suffix}. '
            f'Supported formats are {sorted(SUPPORTED_FORMATS)}.')

    size_mb = path.stat().st_size / (1024 * 1024)
    duration_s = len(AudioSegment.from_file(str(path))) / 1000

    # Chunk if EITHER limit is exceeded.
    return size_mb > MAX_FILE_SIZE_MB or duration_s > MAX_AUDIO_SECONDS

def main(argv=None) -> None:

    # =-=-=-=-
    # Get metadata 
    # =-=-=-=-

    args = parse_args(argv)

    print('\n =-=-=-=- Recording metadata -=-=-=-= \n')

    meta = get_metadata(args)
    archive_previous_transcripts()

    microphone = Microphone(
        speaker=meta['speaker'],
        description=meta['description'],
        date=meta['date'],
        subject=meta['subject'])

    print('\n =-=-=-=- Loading audio -=-=-=-= \n')

    audio_path = load_audio()

    print(f'Loaded audio: {audio_path.name}')

    # =-=-=-=-
    # 2. Check if it meets criterias,
    #    Max File Size: 20 MB.
    #    Supported Formats: mp3, mp4, mpeg, mpga, m4a, wav, and webm.
    # =-=-=-=-

    print('\n =-=-=-=- Validating audio -=-=-=-= \n')

    needs_chunking = validate_audio(audio_path)
    print(f'Chunking needed: {needs_chunking}')

    # =-=-=-=-
    # 3. Transcribe
    # =-=-=-=-

    print('\n =-=-=-=- Transcribing -=-=-=-= \n')

    base_prompt = microphone.description

    if needs_chunking:

        chunks = microphone.chunker(audio_path)
        transcripts = []

        for i, chunk in enumerate(chunks):
            chunk_txt = microphone.transcribe(chunk, prompt=base_prompt)
            transcripts.append(chunk_txt)
            print(f'Transcribed chunk {i + 1}/{len(chunks)}')

        txt = ' '.join(transcripts)

    else:
        txt = microphone.transcribe(audio_path, prompt = base_prompt)

    print(f'Transcribed {len(txt)} characters')

    # =-=-=-=-
    # 4. Save to txt and puts audio in history/audio.
    # =-=-=-=-
    
    print('\n =-=-=-=- Saving -=-=-=-= \n')

    organized = microphone.organize(txt)
    microphone.save(organized, audio_path)

    history_audio_dir = Path('data/history/audio')
    history_audio_dir.mkdir(parents = True, exist_ok = True)
    shutil.move(str(audio_path), str(history_audio_dir / audio_path.name))

    print(f'Archived audio to {history_audio_dir}')



if __name__ == "__main__":
    main()