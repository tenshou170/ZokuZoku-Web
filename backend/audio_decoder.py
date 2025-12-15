import os
import subprocess
import shutil
from typing import Optional

class AudioDecoder:
    def __init__(self):
        # Check for vgmstream-cli in PATH
        self.vgmstream_path = shutil.which("vgmstream-cli")
        if not self.vgmstream_path:
             self.vgmstream_path = shutil.which("vgmstream")
             
    def check_availability(self):
        return self.vgmstream_path is not None

    def decode_cue(self, awb_path: str, cue_index: int) -> bytes:
        """
        Decodes a specific cue (subsong) from an AWB/ACB file to WAV bytes.
        cue_index is assumed to be 0-based from the frontend, converted to 1-based for vgmstream.
        """
        if not self.vgmstream_path:
            raise RuntimeError("vgmstream-cli not found. Please install it/add to PATH.")

        if not os.path.exists(awb_path):
            raise FileNotFoundError(f"Audio file not found: {awb_path}")

        # vgmstream uses 1-based indexing for subsongs
        subsong_index = cue_index + 1
        
        cmd = [
            self.vgmstream_path,
            "-s", str(subsong_index),
            "-p", # Pipe to stdout
            "-F", # Force (ignore existing extensions/logic if needed, though -p implies simple decode)
            awb_path
        ]
        
        # Note: -p pipes the decoded WAV (RIFF header + PCM) to stdout
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
            raise RuntimeError(f"Decoding failed: {error_msg}")

decode_service = AudioDecoder()
