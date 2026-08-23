import os
import shutil
import threading
from managers.manager_base import Manager
from managers.media.media_base import BaseMediaProcessor
from logger.logger import log


class ConvertManager(Manager):
    def __init__(self):
        super().__init__()
        self.media = BaseMediaProcessor()
        self._thread = None
        self._cancel_flag = False

    def _init0(self):
        log.info("Initializing ConvertManager...")
        self.media.clean_temp_dir()

    def _shutdown0(self):
        log.info("Shutting down ConvertManager...")
        self.cancel_task()

    def start_conversion(self, input_file: str, output_file: str, use_gpu: bool, progress_cb, finish_cb, error_cb):
        if self._thread and self._thread.is_alive():
            error_cb("Операція вже триває!")
            return

        self._cancel_flag = False
        self._thread = threading.Thread(
            target=self._convert_task,
            args=(input_file, output_file, use_gpu, progress_cb, finish_cb, error_cb),
            daemon=True
        )
        self._thread.start()

    def cancel_task(self):
        self._cancel_flag = True

    def _is_cancelled(self) -> bool:
        return self._cancel_flag

    def _convert_task(self, input_file: str, output_file: str, use_gpu: bool, progress_cb, finish_cb, error_cb):
        log.info(f"Starting conversion for {input_file} to {output_file} (GPU: {use_gpu})")
        self.media.clean_temp_dir()
        self.media.create_temp_dir()

        temp_output = os.path.join(self.media.temp_dir, os.path.basename(output_file))

        try:
            in_ext = os.path.splitext(input_file)[1].lower()
            out_ext = os.path.splitext(output_file)[1].lower()

            if in_ext == out_ext:
                progress_cb("Копіювання...")
                shutil.copy(input_file, output_file)
                finish_cb("Файл вже у цьому форматі. Скопійовано.", output_file)
                return

            if out_ext == '.gif':
                duration = self.media.get_media_duration(input_file)
                if duration > 60:
                    error_cb("Тривалість відео для створення GIF не може перевищувати 1 хвилину!")
                    return

            progress_cb("Конвертація...")
            cmd = ['ffmpeg', '-y', '-v', 'error', '-i', input_file]

            if use_gpu and not out_ext in ['.gif', '.mp3', '.wav', '.flac', '.ogg', '.m4a']:
                gpu_enc = self.media.get_gpu_encoder()
                if gpu_enc:
                    cmd.extend(['-c:v', gpu_enc])

            cmd.append(temp_output)

            if not self.media.run_ffmpeg_process(cmd, self._is_cancelled):
                error_cb("Скасовано")
                return

            shutil.move(temp_output, output_file)
            log.info("Conversion finished successfully")
            finish_cb("Успішно", output_file)

        except RuntimeError as e:
            log.error(f"FFmpeg process failed: {e}")
            error_cb("Помилка FFmpeg при конвертації.")
        except Exception as e:
            log.error(f"Conversion error: {e}")
            error_cb(f"Помилка конвертації: {e}")
        finally:
            self.media.clean_temp_dir()