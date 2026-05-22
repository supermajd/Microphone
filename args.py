"""args.py: CLI parsing and recording-metadata resolution."""

import argparse
from datetime import date

def parse_args(argv=None) -> argparse.Namespace:
    """ Parses command-line arguments. Any metadata not passed as a flag
    is prompted for interactively (unless --non-interactive is set).
    :param argv: Optional argument list (defaults to sys.argv)
    :return args: Parsed arguments namespace
    """

    parser = argparse.ArgumentParser(
        description='Transcribe an audio file from data/audio using OpenAI.')

    parser.add_argument('--speaker', help='Name of the speaker')
    parser.add_argument('--subject', help='Subject of the recording')
    parser.add_argument('--description', help='Short description of the recording')
    parser.add_argument('--date', help='Recording date (YYYY-MM-DD). Defaults to today.')
    parser.add_argument(
        '--non-interactive', action='store_true',
        help='Never prompt; use defaults for any missing metadata (for CI/cron).')

    return parser.parse_args(argv)

def _resolve(value: str, prompt_text: str, interactive: bool) -> str:
    """ Returns the provided value, else prompts for it (when interactive),
    else falls back to an empty string.
    """

    if value is not None:
        return value.strip()

    if interactive:
        return input(prompt_text).strip()

    return ''

def get_metadata(args: argparse.Namespace) -> dict:
    """ Builds recording metadata from CLI args, prompting for anything missing.
    Empty inputs stay empty, except date which defaults to today.
    :param args: Parsed command-line arguments
    :return meta: Dictionary with speaker, subject, description, and date
    """

    interactive = not args.non_interactive

    speaker = _resolve(args.speaker, 'Who is the speaker? ', interactive)
    subject = _resolve(args.subject, 'What is the subject? ', interactive)
    description = _resolve(args.description, 'Short description? ', interactive)
    date_input = _resolve(args.date, 'Date (YYYY-MM-DD)? ', interactive)

    if not date_input:
        date_input = date.today().isoformat()

    return {
        'speaker': speaker,
        'subject': subject,
        'description': description,
        'date': date_input}