"""Standalone audio entrypoint (no web UI).

    python main.py

For the control panel + audio together, use:

    python dashboard_server.py
"""

from audio_runtime import AudioRuntime


def main() -> None:
    runtime = AudioRuntime(verbose=True)
    runtime.run_forever()


if __name__ == "__main__":
    main()
