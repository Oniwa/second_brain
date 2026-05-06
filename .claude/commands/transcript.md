# /transcript — Fetch YouTube Transcripts

Fetch and save a YouTube transcript using the youtube_transcript project at C:\projects\youtube_transcript.

## Usage
The user provides a YouTube URL or video ID. Run:

```
python C:\projects\youtube_transcript\main.py <url>
```

## Workflow
1. Parse the URL or video ID from the user's message.
2. Run the CLI command above using the Bash tool.
3. Report the output file path and the channel name / video title extracted from the transcript.
4. If the user asks to process the transcript (summarize, extract ideas, pan for gold, etc.), read the output file and proceed.

## Error Handling
- If no URL is provided, ask the user for a valid YouTube URL or video ID.
- If the script fails, show the full error output and suggest verifying that `yt-dlp` is installed (`pip install yt-dlp`).
- If the output file is not created, check that the `transcripts/` directory exists inside the youtube_transcript project.

## Future Improvements
- **Machine-agnostic path resolution** — the tool path (`C:\projects\youtube_transcript`) and Python executable are hardcoded for the home Windows PC. Should support multiple machines (Linux/Pi, other Windows installs) via a lookup table or by checking a `YOUTUBE_TRANSCRIPT_PATH` env var before falling back to known paths.
