import os
import threading
import time
import shutil
import subprocess
import yt_dlp
from managers.manager_base import Manager
from managers.media.media_base import BaseMediaProcessor
from logger.logger import log
import re


class CancelledError(BaseException):
    pass


class DownloadManager(Manager):
    def __init__(self):
        super().__init__()
        self.media = BaseMediaProcessor()
        self._download_thread = None
        self._cancel_flag = False

    def _init0(self):
        log.info("Initializing DownloadManager...")
        self.media.clean_temp_dir()

    def _shutdown0(self):
        log.info("Shutting down DownloadManager...")
        self.cancel_download()
        self.media.clean_temp_dir()

    def start_download(self, url: str, options: dict, progress_cb, finish_cb, error_cb):
        if self._download_thread and self._download_thread.is_alive():
            error_cb("Завантаження вже триває!")
            return

        self._cancel_flag = False
        self._download_thread = threading.Thread(
            target=self._download_task,
            args=(url, options, progress_cb, finish_cb, error_cb),
            daemon=True
        )
        self._download_thread.start()

    def cancel_download(self):
        self._cancel_flag = True
        log.info("Download cancellation requested")

    def _get_downloaded_file_from_temp(self):
        valid_exts = ('.mp4', '.mp3', '.mkv', '.webm', '.m4a', '.jpg', '.jpeg', '.png', '.webp')
        for f in os.listdir(self.media.temp_dir):
            if f.lower().endswith(valid_exts):
                return os.path.join(self.media.temp_dir, f)
        return ""

    def _run_nightly_fallback(self, url: str, options: dict, progress_cb) -> tuple[bool, str]:
        log.info("Initiating yt-dlp-nightly...")

        nightly_max_retries = 2
        ansi_escape = re.compile(r'\x1b\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]')

        cmd = ['yt-dlp-nightly', '--newline', '--ignore-errors']

        if getattr(self, 'verbose_ytdlp', False):
            cmd.extend(['-v', '--write-pages'])

        cmd.extend(['-o', os.path.join(self.media.temp_dir, '%(title)s.%(ext)s')])

        if options.get('thumbnail'):
            cmd.extend(['--write-thumbnail', '--skip-download'])
        else:
            if options.get('type') == 'audio':
                cmd.extend(['-f', 'bestaudio/best', '-x', '--audio-format', 'mp3', '--audio-quality', '192K'])
            else:
                if options.get('max_1080p'):
                    cmd.extend(
                        ['-f', 'bestvideo[height<=1080][vcodec^=avc1]+bestaudio/best', '--merge-output-format', 'mp4'])
                else:
                    cmd.extend(['-f', 'bestvideo[vcodec^=avc1]+bestaudio/best', '--merge-output-format', 'mp4'])

        if not options.get('playlist'):
            cmd.append('--no-playlist')

        if not options.get('thumbnail'):
            cmd.append('--add-metadata')

        cmd.append(url)

        for attempt in range(1, nightly_max_retries + 1):
            if self._cancel_flag: break

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            playlist_prefix = ""
            for line in process.stdout:
                if self._cancel_flag:
                    process.terminate()
                    return False, ""

                line = line.strip()
                line = ansi_escape.sub('', line)

                if "Downloading video" in line and "of" in line:
                    m = re.search(r'Downloading video (\d+) of (\d+)', line)
                    if m:
                        playlist_prefix = f"[{m.group(1)}/{m.group(2)}] "

                if "[download]" in line and "%" in line:
                    try:
                        percent = line.split('%')[0].split()[-1] + "%"
                        progress_cb(f"{playlist_prefix}Завантаження: {percent}")
                    except:
                        pass

            process.wait()

            if process.returncode == 0:
                final_file = self._get_downloaded_file_from_temp()
                if final_file or (options.get('playlist') and len(os.listdir(self.media.temp_dir)) > 0):
                    return True, final_file

            log.warn(f"yt-dlp-nightly attempt {attempt} failed")
            if attempt < nightly_max_retries and not self._cancel_flag:
                time.sleep(2)

        return False, ""

    def _download_task(self, url: str, options: dict, progress_cb, finish_cb, error_cb):
        log.info(f"Starting download for: {url} with options: {options}")

        if "tiktok.com" in url.lower() and "/photo/" in url.lower():
            error_cb("TIKTOK_PHOTO")
            return

        self.media.clean_temp_dir()
        self.media.create_temp_dir()

        try:
            ansi_escape = re.compile(r'\x1b\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]')

            def hook(d):
                if self._cancel_flag:
                    raise CancelledError("CANCELLED")

                info = d.get('info_dict', {})
                p_index = info.get('playlist_index')
                p_count = info.get('playlist_count')
                prefix = f"[{p_index}/{p_count}] " if p_index and p_count else ""

                if d['status'] == 'downloading':
                    percent = d.get('_percent_str', '...').strip()
                    percent = ansi_escape.sub('', percent)
                    progress_cb(f"{prefix}Завантаження: {percent}")

                elif d['status'] == 'finished':
                    progress_cb(f"{prefix}Збірка файлу...")

            def check_cancel(info, *, incomplete):
                if self._cancel_flag:
                    raise CancelledError("CANCELLED")
                return None

            class YTDLLogger:
                def __init__(self, is_verbose):
                    self.error_msg = ""
                    self.is_verbose = is_verbose

                def debug(self, msg):
                    if self.is_verbose: log.info(f"[yt-dlp] {msg}")

                def warning(self, msg):
                    if self.is_verbose: log.warn(f"[yt-dlp] {msg}")

                def error(self, msg):
                    self.error_msg += msg + " "
                    if self.is_verbose: log.error(f"[yt-dlp] {msg}")

            ydl_logger = YTDLLogger(getattr(self, 'verbose_ytdlp', False))

            ydl_opts = {
                'outtmpl': os.path.join(self.media.temp_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [hook],
                'match_filter': check_cancel,
                'logger': ydl_logger,
                'quiet': not getattr(self, 'verbose_ytdlp', False),
                'verbose': getattr(self, 'verbose_ytdlp', False),
                'writepages': getattr(self, 'verbose_ytdlp', False),
                'noprogress': True,
                'ignoreerrors': True,
                'postprocessors': []
            }

            if options.get('thumbnail'):
                ydl_opts['writethumbnail'] = True
                ydl_opts['skip_download'] = True
            else:
                if options.get('type') == 'audio':
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'].append({
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    })
                else:
                    if options.get('max_1080p'):
                        ydl_opts['format'] = 'bestvideo[height<=1080][vcodec^=avc1]+bestaudio/best'
                    else:
                        ydl_opts['format'] = 'bestvideo[vcodec^=avc1]+bestaudio/best'
                    ydl_opts['merge_output_format'] = 'mp4'

            if not options.get('playlist'):
                ydl_opts['noplaylist'] = True

            if not options.get('thumbnail'):
                ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata'})

            stable_max_retries = 3
            attempt = 1
            success = False
            is_blocked = False
            last_error_msg = ""
            final_filepath = ""
            playlist_errors_count = 0

            while attempt <= stable_max_retries and not self._cancel_flag:
                try:
                    ydl_logger.error_msg = ""
                    progress_cb(f"Підключення...")

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info_dict = ydl.extract_info(url, download=True)

                        if info_dict is None:
                            raise Exception(
                                ydl_logger.error_msg if ydl_logger.error_msg else "Unknown extraction error")

                        if 'entries' in info_dict:
                            final_filepath = self.media.temp_dir
                            for entry in info_dict.get('entries', []):
                                if entry is None:
                                    playlist_errors_count += 1
                        else:

                            if options.get('thumbnail'):
                                final_filepath = self._get_downloaded_file_from_temp()
                            else:
                                base_filepath = ydl.prepare_filename(info_dict)
                                if options.get('type') == 'audio':
                                    final_filepath = os.path.splitext(base_filepath)[0] + '.mp3'
                                else:
                                    final_filepath = os.path.splitext(base_filepath)[0] + '.mp4'

                    success = True
                    break

                except CancelledError:
                    log.info("Download aborted")
                    break

                except Exception as e:
                    last_error_msg = str(e)
                    log.warn(f"Stable download attempt {attempt} failed: {e}")
                    msg_lower = last_error_msg.lower()

                    if any(word in msg_lower for word in
                           ["private video", "video unavailable", "drm", "unsupported url", "members-only",
                            "premieres in", "permission", "is not a valid url", "accessing"]):
                        break
                    if any(word in msg_lower for word in ["429", "too many requests", "rate-limit"]):
                        break

                    if any(word in msg_lower for word in
                           ["sign in to confirm", "bot", "403", "unexpected", "unable to extract universal data"]):
                        is_blocked = True

                    attempt += 1
                    if attempt <= stable_max_retries:
                        time.sleep(2)

            if not success and is_blocked and not self._cancel_flag:
                nightly_success, nightly_file = self._run_nightly_fallback(url, options, progress_cb)
                if nightly_success:
                    success = True
                    final_filepath = nightly_file
                else:
                    last_error_msg = "Nightly fallback failed"

            if self._cancel_flag:
                error_cb("Скасовано")
            elif success:
                try:
                    save_dir = options.get('save_dir')

                    if options.get('type') == 'video' and not options.get('thumbnail'):
                        progress_cb("Процес майже закінчено...")
                        for file_name in os.listdir(self.media.temp_dir):
                            if file_name.lower().endswith('.mp4'):
                                temp_path = os.path.join(self.media.temp_dir, file_name)
                                codec = self.media.get_video_codec(temp_path)

                                if codec and codec not in ['h264', 'avc1']:
                                    log.info(f"Re-encoding {file_name} from {codec} to H.264")
                                    self.media.reencode_to_h264(temp_path, lambda: self._cancel_flag)

                                    if self._cancel_flag:
                                        break

                    if self._cancel_flag:
                        error_cb("Скасовано")
                        return

                    if save_dir and os.path.exists(save_dir) and final_filepath:
                        if os.path.isdir(final_filepath):
                            progress_cb("Переміщення файлів плейлиста...")
                            for file_name in os.listdir(final_filepath):
                                src_path = os.path.join(final_filepath, file_name)

                                if os.path.isfile(src_path) and file_name.lower().endswith(
                                        ('.mp4', '.mp3', '.mkv', '.webm', '.m4a', '.jpg', '.jpeg', '.png', '.webp')):
                                    try:
                                        dst_path = os.path.join(save_dir, file_name)
                                        shutil.move(src_path, dst_path)
                                    except Exception as e:
                                        log.error(f"Failed to move {file_name}: {e}")

                            final_filepath = save_dir
                            if playlist_errors_count > 0:
                                finish_msg = f"Завантаження плейлиста завершено.\nДеякі медіа пропущено через помилки: {playlist_errors_count}"
                            else:
                                finish_msg = "Плейлист успішно завантажено"

                            log.info("Playlist download finished")
                            finish_cb(finish_msg, final_filepath)

                        elif os.path.isfile(final_filepath):
                            try:
                                progress_cb("Переміщення файлу...")
                                filename = os.path.basename(final_filepath)
                                new_filepath = os.path.join(save_dir, filename)

                                shutil.move(final_filepath, new_filepath)
                                final_filepath = new_filepath
                                log.info(f"File moved to target directory: {new_filepath}")
                            except Exception as e:
                                log.error(f"Failed to move file to {save_dir}: {e}")

                            log.info("Download finished successfully")
                            finish_cb("Завантажено успішно", final_filepath)

                    else:
                        log.warn("Download flagged as success, but no file found in Temp")
                        error_cb("Файл не знайдено")

                except Exception as post_error:
                    log.error(f"Post-processing failed: {post_error}")
                    error_cb(f"Помилка під час збереження файлу")

            else:
                log.error("All download attempts failed")
                msg_lower = last_error_msg.lower()

                if "drm" in msg_lower:
                    error_cb("DRM")
                elif "unsupported url" in msg_lower or "is not a valid url" in msg_lower:
                    error_cb("UNSUPPORTED_URL")
                elif "private video" in msg_lower or "video unavailable" in msg_lower or "permission" in msg_lower or "accessing" in msg_lower:
                    error_cb("PRIVATE")
                elif "age-restricted" in msg_lower or "confirm your age" in msg_lower:
                    error_cb("AGE_RESTRICTED")
                elif "available in your country" in msg_lower or "geo-restricted" in msg_lower:
                    error_cb("GEO_RESTRICTED")
                elif any(word in msg_lower for word in ["429", "too many requests", "rate-limit"]):
                    error_cb("RATE_LIMIT")
                elif "members-only" in msg_lower:
                    error_cb("MEMBERS_ONLY")
                elif "premieres in" in msg_lower or "live event will begin" in msg_lower:
                    error_cb("PREMIERE")
                elif is_blocked or any(word in msg_lower for word in ["sign in to", "bot", "403", "unexpected", "unable to extract universal data"]):
                    error_cb("BLOCKED")
                else:
                    error_cb("Невідома помилка")

        finally:
            self.media.clean_temp_dir()