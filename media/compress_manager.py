import os
import shutil
import threading
import subprocess
import json
import math
from managers.manager_base import Manager
from managers.media.media_base import BaseMediaProcessor
from logger.logger import log


class CompressManager(Manager):
    def __init__(self):
        super().__init__()
        self.media = BaseMediaProcessor()
        self._thread = None
        self._cancel_flag = False

    def _init0(self):
        log.info("Initializing CompressManager...")
        self.media.clean_temp_dir()

    def _shutdown0(self):
        log.info("Shutting down CompressManager...")
        self.cancel_task()

    def start_compression(self, input_file: str, output_file: str, target_size_mb: float, allow_resize: bool,
                          progress_cb, finish_cb, error_cb):
        if self._thread and self._thread.is_alive():
            error_cb("Операція вже триває!")
            return

        self._cancel_flag = False
        self._thread = threading.Thread(
            target=self._compress_task,
            args=(input_file, output_file, target_size_mb, allow_resize, progress_cb, finish_cb, error_cb),
            daemon=True
        )
        self._thread.start()

    def cancel_task(self):
        self._cancel_flag = True

    def _is_cancelled(self) -> bool:
        return self._cancel_flag

    def _compress_task(self, input_file: str, output_file: str, target_size_mb: float, allow_resize: bool, progress_cb,
                       finish_cb, error_cb):
        log.info(f"Starting compression for {input_file} to {target_size_mb}MB (Resize: {allow_resize})")

        self.media.clean_temp_dir()
        self.media.create_temp_dir()

        temp_output = os.path.join(self.media.temp_dir, os.path.basename(output_file))

        try:
            target_size_bytes = target_size_mb * 1024 * 1024
            current_size = os.path.getsize(input_file)
            current_size_mb = current_size / (1024 * 1024)

            in_ext = os.path.splitext(input_file)[1].lower()
            out_ext = os.path.splitext(output_file)[1].lower()
            is_gif = (out_ext == '.gif' or in_ext == '.gif')

            duration = self.media.get_media_duration(input_file)

            if is_gif and duration > 120:
                error_cb("Тривалість для стиснення або створення GIF не може перевищувати 2 хвилини!")
                return

            if is_gif:
                min_allowed_ratio = 0.02
            else:
                min_allowed_ratio = 0.02 if allow_resize else 0.10

            if target_size_mb < (current_size_mb * min_allowed_ratio):
                error_cb(
                    f"Екстремальне стиснення!\nНеможливо стиснути файл {current_size_mb:.1f} МБ до {target_size_mb} МБ.\nМінімальний дозволений розмір: {current_size_mb * min_allowed_ratio:.1f} МБ.")
                return

            if not is_gif and current_size <= target_size_bytes:
                if in_ext == out_ext:
                    shutil.copy(input_file, output_file)
                    finish_cb("Файл вже менший за вказаний розмір. Скопійовано.", output_file)
                    return
                else:
                    progress_cb("Швидка конвертація...")
                    cmd = ['ffmpeg', '-y', '-v', 'error', '-i', input_file, '-c:v', 'libx264', '-crf', '23', '-preset',
                           'fast', temp_output]
                    if not self.media.run_ffmpeg_process(cmd, self._is_cancelled):
                        error_cb("Скасовано")
                        return

                    shutil.move(temp_output, output_file)
                    finish_cb("Успішно!", output_file)
                    return

            if is_gif:
                progress_cb("Стиснення GIF (Аналіз розмірів)...")

                cmd_info = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                            '-show_entries', 'format=duration', '-of', 'json', input_file]
                try:
                    info_res = subprocess.run(cmd_info, capture_output=True, text=True)
                    info = json.loads(info_res.stdout)
                    w = info['streams'][0].get('width', 0)
                    h = info['streams'][0].get('height', 0)
                    d = float(info['format'].get('duration', 0))
                except:
                    w, h, d = 0, 0, duration

                if d > 0 and w > 0 and h > 0:
                    estimated_size = w * h * 15 * d * 0.7
                    if estimated_size > target_size_bytes:
                        ratio = target_size_bytes / estimated_size
                        scale_factor = math.sqrt(ratio) * 0.85
                        scale_factor = min(scale_factor, 1.0)
                        target_width = int(w * scale_factor)
                        target_width = target_width - (target_width % 2)
                        scale_filter = f"scale='min({target_width},iw)':-1"
                    else:
                        scale_filter = "scale='min(720,iw)':-1"
                else:
                    scale_filter = "scale='min(720,iw)':-1"

                progress_cb("Стиснення GIF...")
                cmd = [
                    'ffmpeg', '-y', '-v', 'error', '-i', input_file,
                    '-filter_complex',
                    f'fps=15,{scale_filter}:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
                    temp_output
                ]
                if not self.media.run_ffmpeg_process(cmd, self._is_cancelled):
                    error_cb("Скасовано")
                    return

                shutil.move(temp_output, output_file)
                finish_cb("Успіх", output_file)
                return

            if duration <= 0:
                error_cb("Неможливо визначити тривалість відео")
                return

            effective_size_bytes = min(current_size, target_size_bytes)
            safe_target_kb = (effective_size_bytes / 1024) - 150
            if safe_target_kb < 100:
                safe_target_kb = (effective_size_bytes / 1024) * 0.9

            total_bitrate_kbps = (safe_target_kb * 8) / duration
            audio_bitrate_kbps = 128
            video_bitrate_kbps = int(total_bitrate_kbps - audio_bitrate_kbps)

            if video_bitrate_kbps < 50:
                audio_bitrate_kbps = 64
                video_bitrate_kbps = int(total_bitrate_kbps - audio_bitrate_kbps)
                if video_bitrate_kbps < 30:
                    error_cb(
                        f"Цільовий розмір занадто малий!\nНавіть з найнижчою якістю, бітрейт падає до {video_bitrate_kbps} kbps (мінімум 30).\nНе впихайте невпихуйме!")
                    return

            scale_args = []
            if allow_resize:
                if video_bitrate_kbps < 250:
                    progress_cb("Стиснення (Оптимізація під 360p)...")
                    scale_args = ['-vf', "scale='min(iw,640)':'min(ih,360)'"]
                elif video_bitrate_kbps < 500:
                    progress_cb("Стиснення (Оптимізація під 480p)...")
                    scale_args = ['-vf', "scale='min(iw,854)':'min(ih,480)'"]
                elif video_bitrate_kbps < 1000:
                    progress_cb("Стиснення (Оптимізація під 720p)...")
                    scale_args = ['-vf', "scale='min(iw,1280)':'min(ih,720)'"]
                else:
                    progress_cb("Стиснення (Етап 1/2)...")
            else:
                progress_cb("Стиснення (Етап 1/2)...")

            passlog_base = os.path.join(self.media.temp_dir, "ffmpeg2pass")

            pass1_cmd = [
                            'ffmpeg', '-y', '-v', 'error', '-i', input_file, '-c:v', 'libx264', '-preset', 'fast',
                            '-b:v', f'{video_bitrate_kbps}k', '-maxrate', f'{video_bitrate_kbps}k', '-bufsize',
                            f'{video_bitrate_kbps * 2}k'
                        ] + scale_args + [
                            '-pass', '1', '-passlogfile', passlog_base, '-an', '-f', 'null', '/dev/null'
                        ]

            if not self.media.run_ffmpeg_process(pass1_cmd, self._is_cancelled):
                error_cb("Скасовано користувачем")
                return

            if not allow_resize or video_bitrate_kbps >= 1000:
                progress_cb("Стиснення (Етап 2/2)...")
            else:
                progress_cb("Стиснення (Фінал)...")

            pass2_cmd = [
                            'ffmpeg', '-y', '-v', 'error', '-i', input_file, '-c:v', 'libx264', '-preset', 'fast',
                            '-b:v', f'{video_bitrate_kbps}k', '-maxrate', f'{video_bitrate_kbps}k', '-bufsize',
                            f'{video_bitrate_kbps * 2}k'
                        ] + scale_args + [
                            '-pass', '2', '-passlogfile', passlog_base, '-c:a', 'aac', '-b:a', f'{audio_bitrate_kbps}k',
                            temp_output
                        ]

            if not self.media.run_ffmpeg_process(pass2_cmd, self._is_cancelled):
                error_cb("Скасовано")
                return

            for ext in ['-0.log', '-0.log.mbtree']:
                try:
                    os.remove(passlog_base + ext)
                except:
                    pass

            shutil.move(temp_output, output_file)

            log.info("Compression finished successfully")
            finish_cb("Успішно стиснено!", output_file)

        except RuntimeError as e:
            log.error(f"FFmpeg process failed: {e}")
            error_cb("Помилка FFmpeg при обробці відео.\nМожливо файл пошкоджений або формат не підтримується.")
        except Exception as e:
            log.error(f"Compression error: {e}")
            error_cb(f"Невідома помилка: {e}")

        finally:
            self.media.clean_temp_dir()