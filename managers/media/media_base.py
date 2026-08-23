import os
import shutil
import subprocess
import time
from logger.logger import log

class BaseMediaProcessor:
    def __init__(self, temp_folder_name: str = "Temp"):
        self.program_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.temp_dir = os.path.join(self.program_dir, temp_folder_name)

    def create_temp_dir(self):
        os.makedirs(self.temp_dir, exist_ok=True)
        log.info(f"Ensured Temp directory exists: {self.temp_dir}")

    def clean_temp_dir(self):
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                log.info("Temp directory cleaned.")
            except Exception as e:
                log.error(f"Failed to clean Temp directory: {e}")

    def get_video_codec(self, file_path: str) -> str:
        try:
            cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                   'stream=codec_name', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            return res.stdout.strip().lower()
        except Exception as e:
            log.warn(f"Failed to get codec for {file_path}: {e}")
            return ""

    def reencode_to_h264(self, file_path: str, is_cancelled_func) -> bool:
        temp_output = file_path + ".temp.mp4"
        cmd = ['ffmpeg', '-v', 'error', '-y', '-i', file_path, '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'copy',
               temp_output]

        success = self.run_ffmpeg_process(cmd, is_cancelled_func)

        if success and os.path.exists(temp_output):
            os.replace(temp_output, file_path)
        elif os.path.exists(temp_output):
            os.remove(temp_output)

        return success

    def get_gpu_encoder(self) -> str | None:
        try:
            res = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True)
            enc = res.stdout.lower()
            if 'h264_nvenc' in enc: return 'h264_nvenc'
            if 'h264_qsv' in enc: return 'h264_qsv'
            if 'h264_amf' in enc: return 'h264_amf'
            if 'h264_vaapi' in enc: return 'h264_vaapi'
        except Exception as e:
            log.warn(f"Failed to detect GPU encoder: {e}")
        return None

    def get_media_duration(self, file_path: str) -> float:
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                   '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            return float(res.stdout.strip())
        except Exception:
            return 0.0

    def run_ffmpeg_process(self, cmd: list, is_cancelled_func) -> bool:
        p = subprocess.Popen(cmd, cwd=self.temp_dir)

        while p.poll() is None:
            if is_cancelled_func():
                p.terminate()
                p.wait()
                return False
            time.sleep(0.5)

        if p.returncode != 0:
            raise RuntimeError(f"FFmpeg process failed with code {p.returncode}")
        return True