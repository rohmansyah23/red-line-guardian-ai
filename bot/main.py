#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
import cv2
import mss
import numpy as np
import time
import random
import json
import os
import threading
from pynput.mouse import Button, Controller
from pynput.keyboard import Key, Listener
import traceback

# =============================================================================
# KELAS LOGIKA BOT (DENGAN KESABARAN DAN FOKUS PADA TARGET)
# Versi dioptimalkan: mengurangi pekerjaan berulang, memperbaiki lifecycle, dan
# mengumpulkan operasi mouse/klik menjadi helper.
# =============================================================================
class GameBot:
    def __init__(self, debug: bool = False):
        # area_game: dict with keys top,left,width,height
        self.area_game = {}
        self.is_paused = True
        self.stop_event = threading.Event()
        self.status_text = "Menunggu"
        self.display_level = "Medium"
        self.keputusan = "DIAM"

        # drawing/setup state
        self.drawing = False
        self.ix = self.iy = -1
        self.full_screenshot_img = None
        self.setup_complete = False

        # color thresholds (BGR)
        self.putih_bawah = np.array([160, 160, 160], dtype=np.uint8)
        self.putih_atas = np.array([255, 255, 255], dtype=np.uint8)
        self.merah_bawah = np.array([0, 0, 189], dtype=np.uint8)
        self.merah_atas = np.array([0, 0, 189], dtype=np.uint8)

        # PID-ish control params and presets
        self.intelligence_presets = {
            "Low": (0.08, 0.10, 30),
            "Medium": (0.15, 0.25, 60),
            "Pro": (0.22, 0.35, 90),
            "Expert": (0.30, 0.40, 120)
        }
        self.P_FACTOR, self.D_FACTOR, self.TARGET_FPS = self.intelligence_presets["Medium"]
        self.FRAME_TIME = 1.0 / self.TARGET_FPS
        self.last_error = 0

        # click timing
        self.click_delay = 1.5
        self.use_random_delay = False
        self.random_delay_min = 1.1
        self.random_delay_max = 1.5

        # misc
        self.scaling_factor = 0.5
        self.stuck_timer_start = 0
        self.recovery_timeout = 30

        # mouse controller
        self.mouse = Controller()

        # runtime state
        self.waiting_for_state_change_after_click = False
        self.resume_action_pending = False

        # resource reuse
        self._sct = None

        # debugging
        self.debug = debug

    # -------------------------
    # Setup area with OpenCV
    # -------------------------
    def _select_area_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            # show rectangle overlay
            img_copy = self.full_screenshot_img.copy()
            cv2.rectangle(img_copy, (self.ix, self.iy), (x, y), (0, 255, 0), 2)
            cv2.imshow('Setup: Klik dan Seret Area', img_copy)
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            width = abs(x - self.ix)
            height = abs(y - self.iy)
            if width > 10 and height > 10:
                left, top = min(self.ix, x), min(self.iy, y)
                self.area_game = {'top': top, 'left': left, 'width': width, 'height': height}
                self.setup_complete = True
                cv2.destroyAllWindows()

    def setup_manual(self):
        """
        Tampilkan screenshot fullscreen dan biarkan user klik+drag untuk memilih area.
        Mengembalikan dict area jika selesai, atau None kalau dibatalkan.
        """
        self.setup_complete = False
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                full_screenshot = sct.grab(monitor)
                # convert BGRA -> BGR
                self.full_screenshot_img = cv2.cvtColor(np.array(full_screenshot), cv2.COLOR_BGRA2BGR)
        except Exception as e:
            print("Gagal mengambil screenshot untuk setup:", e)
            traceback.print_exc()
            return None

        overlay = self.full_screenshot_img.copy()
        cv2.putText(overlay, "KLIK DAN SERET UNTUK MEMILIH AREA, LALU LEPASKAN MOUSE",
                    (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.7, self.full_screenshot_img, 0.3, 0, self.full_screenshot_img)
        cv2.namedWindow('Setup: Klik dan Seret Area', cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty('Setup: Klik dan Seret Area', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.setMouseCallback('Setup: Klik dan Seret Area', self._select_area_callback)
        cv2.imshow('Setup: Klik dan Seret Area', self.full_screenshot_img)

        while not self.setup_complete and cv2.getWindowProperty('Setup: Klik dan Seret Area', cv2.WND_PROP_VISIBLE) >= 1:
            # small wait to give CPU breathing space
            if cv2.waitKey(10) & 0xFF == 27:  # ESC untuk batal
                break

        cv2.destroyAllWindows()
        return self.area_game if self.setup_complete else None

    # -------------------------
    # Utility helpers
    # -------------------------
    def set_intelligence(self, level_name: str):
        if level_name == "Random":
            self.display_level = "Random"
            return
        if level_name in self.intelligence_presets:
            self.P_FACTOR, self.D_FACTOR, self.TARGET_FPS = self.intelligence_presets[level_name]
            self.FRAME_TIME = 1.0 / self.TARGET_FPS
            self.display_level = level_name
            if self.debug:
                print(f"Kecerdasan diatur ke: {level_name}")

    def set_click_delay(self, delay: float):
        self.click_delay = float(delay)
        if not self.use_random_delay and self.debug:
            print(f"Delay klik diatur ke: {self.click_delay:.2f} detik")

    def set_random_delay_mode(self, enabled: bool):
        self.use_random_delay = bool(enabled)
        if self.debug:
            if self.use_random_delay:
                print("Mode delay acak diaktifkan.")
            else:
                print("Mode delay acak dinonaktifkan.")

    def _get_current_delay(self):
        if self.use_random_delay:
            d = random.uniform(self.random_delay_min, self.random_delay_max)
            if self.debug:
                print(f"Menggunakan delay acak: {d:.2f}")
            return d
        return self.click_delay

    def _click_center(self):
        """Click safely in the center of area_game."""
        try:
            cx = self.area_game['left'] + (self.area_game['width'] // 2)
            cy = self.area_game['top'] + (self.area_game['height'] // 2)
            self.mouse.position = (cx, cy)
            time.sleep(0.05)
            self.mouse.click(Button.left, 1)
        except Exception as e:
            if self.debug:
                print("Error saat melakukan klik:", e)

    # -------------------------
    # Analisis state permainan
    # -------------------------
    def analyze_game_state(self, img_bgr):
        """
        Mengembalikan satu dari: "BERMAIN", "MENUNGGU", "PERLU_KLIK".
        Menggunakan operasi pada frame berukuran apa pun (full atau scaled).
        """
        # gunakan countNonZero daripada np.sum untuk kecepatan dan akurasi threshold
        mask_putih = cv2.inRange(img_bgr, self.putih_bawah, self.putih_atas)
        putih_ditemukan = int(cv2.countNonZero(mask_putih)) > 500  # threshold lebih konservatif pada scaled
        mask_merah = cv2.inRange(img_bgr, self.merah_bawah, self.merah_atas)
        merah_ditemukan = int(cv2.countNonZero(mask_merah)) > 30

        if putih_ditemukan and merah_ditemukan:
            return "BERMAIN"
        elif merah_ditemukan and not putih_ditemukan:
            return "MENUNGGU"
        else:
            return "PERLU_KLIK"

    # -------------------------
    # Loop utama bot
    # -------------------------
    def run(self):
        # reuse mss instance for performance
        if self._sct is None:
            self._sct = mss.mss()

        is_random_mode = self.display_level == "Random"
        cooldown_end_time = 0
        is_in_cooldown = False
        self.waiting_for_state_change_after_click = False

        try:
            while not self.stop_event.is_set():
                frame_start_time = time.monotonic()

                if self.is_paused:
                    self.status_text = "Dijeda"
                    self.stuck_timer_start = 0
                    time.sleep(0.1)
                    continue

                # grab once per loop
                try:
                    screenshot = self._sct.grab(self.area_game)
                except Exception as e:
                    # jika gagal mengambil screenshot, coba ulang beberapa kali
                    if self.debug:
                        print("Gagal grab area:", e)
                    time.sleep(0.1)
                    continue

                # BGRA -> BGR (slice cukup, mss format BGRA)
                frame = np.array(screenshot)[:, :, :3]
                # downscale untuk sebagian besar analisis (lebih cepat)
                small_frame = cv2.resize(frame, (0, 0), fx=self.scaling_factor, fy=self.scaling_factor, interpolation=cv2.INTER_LINEAR)

                # gunakan scaled frame untuk analisis keseluruhan (threshold tetap valid)
                game_state = self.analyze_game_state(small_frame)

                # stuck recovery: jika sudah lama dan masih membutuhkan klik -> klik pemulihan
                if self.stuck_timer_start != 0 and (time.monotonic() - self.stuck_timer_start > self.recovery_timeout):
                    if game_state == "PERLU_KLIK":
                        self.status_text = "Pemulihan..."
                        if self.debug:
                            print(f"Bot tampaknya macet selama {self.recovery_timeout} detik. Melakukan klik pemulihan...")
                        # release untuk menjaga keadaan mouse
                        try:
                            self.mouse.release(Button.left)
                        except Exception:
                            pass
                        self._click_center()
                        time.sleep(0.5)
                        self.stuck_timer_start = time.monotonic()
                        # lanjut loop tanpa perhitungan kontrol
                        elapsed_time = time.monotonic() - frame_start_time
                        sleep_time = self.FRAME_TIME - elapsed_time
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                        continue
                    else:
                        self.stuck_timer_start = 0

                # resume pending handling
                if self.resume_action_pending:
                    self.resume_action_pending = False
                    if game_state == "PERLU_KLIK" and not is_in_cooldown:
                        self.status_text = "Melanjutkan & Mengklik..."
                        current_delay = self._get_current_delay()
                        is_in_cooldown = True
                        cooldown_end_time = time.monotonic() + current_delay
                        if self.debug:
                            print(f"Resume pending -> menunggu cooldown {current_delay:.2f}s sebelum klik")
                        time.sleep(self.FRAME_TIME)
                        continue

                if game_state != "PERLU_KLIK":
                    self.waiting_for_state_change_after_click = False

                # STATE: BERMAIN -> tracking white + red (gunakan small_frame untuk kecepatan)
                if game_state == "BERMAIN":
                    self.stuck_timer_start = 0
                    self.status_text = "Bermain..."
                    is_in_cooldown = False

                    mask_putih = cv2.inRange(small_frame, self.putih_bawah, self.putih_atas)
                    kontur_putih, _ = cv2.findContours(mask_putih, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    posisi_putih_x = -1
                    if kontur_putih:
                        # pilih kontur terbesar yang signifikan
                        c = max(kontur_putih, key=cv2.contourArea)
                        area = cv2.contourArea(c)
                        if area > 20:
                            M = cv2.moments(c)
                            if M.get("m00", 0) != 0:
                                posisi_putih_x = int((M["m10"] / M["m00"]) / self.scaling_factor)

                    # detect red vertical line-ish shapes
                    mask_merah = cv2.inRange(small_frame, self.merah_bawah, self.merah_atas)
                    kontur_merah, _ = cv2.findContours(mask_merah, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    posisi_merah_x = -1
                    min_height = small_frame.shape[0] * 0.8
                    # pilih kontur yang tinggi dan sempit
                    line_contours = []
                    for cnt in kontur_merah:
                        x, y, w, h = cv2.boundingRect(cnt)
                        if h > min_height and w < (20 * self.scaling_factor):
                            line_contours.append(cnt)

                    if line_contours:
                        c = max(line_contours, key=cv2.contourArea)
                        M = cv2.moments(c)
                        if M.get("m00", 0) != 0:
                            posisi_merah_x = int((M["m10"] / M["m00"]) / self.scaling_factor)

                    if posisi_merah_x != -1 and posisi_putih_x != -1:
                        error = posisi_merah_x - posisi_putih_x
                        derivative = error - self.last_error
                        control_output = (error * self.P_FACTOR) + (derivative * self.D_FACTOR)
                        self.last_error = error
                        self.keputusan = "DIAM"
                        # threshold kecil untuk mengurangi jitter
                        if control_output > 1.0:
                            self.keputusan = "KLIK"
                            try:
                                self.mouse.press(Button.left)
                            except Exception:
                                pass
                        elif control_output < -1.0:
                            self.keputusan = "LEPAS"
                            try:
                                self.mouse.release(Button.left)
                            except Exception:
                                pass
                    else:
                        self.keputusan = "Mencari target..."

                # STATE: MENUNGGU
                elif game_state == "MENUNGGU":
                    self.stuck_timer_start = 0
                    self.status_text = "Countdown (DIAM!)"
                    self.keputusan = "DIAM"
                    try:
                        self.mouse.release(Button.left)
                    except Exception:
                        pass

                # STATE: PERLU_KLIK
                elif game_state == "PERLU_KLIK":
                    self.status_text = "Perlu Klik..."
                    if not is_in_cooldown and not self.waiting_for_state_change_after_click:
                        self.keputusan = "Mulai Cooldown Otomatis"
                        current_delay = self._get_current_delay()
                        if self.debug:
                            print(f"Layar perlu klik terdeteksi. Cooldown {current_delay:.2f} detik...")
                        try:
                            self.mouse.release(Button.left)
                        except Exception:
                            pass
                        is_in_cooldown = True
                        cooldown_end_time = time.monotonic() + current_delay

                # cooldown selesai -> lakukan klik
                if is_in_cooldown and time.monotonic() >= cooldown_end_time:
                    self.status_text = "Mengklik..."
                    if self.debug:
                        print("Cooldown selesai. Mengirim klik...")
                    try:
                        self.mouse.release(Button.left)
                    except Exception:
                        pass
                    self._click_center()
                    time.sleep(0.25)
                    self.stuck_timer_start = time.monotonic()
                    self.last_error = 0
                    self.waiting_for_state_change_after_click = True
                    is_in_cooldown = False

                    # jika mode random intelligence, ganti parameter pid+fps acak
                    if is_random_mode:
                        random_level = random.choice(list(self.intelligence_presets.keys()))
                        self.P_FACTOR, self.D_FACTOR, self.TARGET_FPS = self.intelligence_presets[random_level]
                        self.FRAME_TIME = 1.0 / self.TARGET_FPS
                        self.display_level = f"Random ({random_level})"

                # maintain target fps
                elapsed_time = time.monotonic() - frame_start_time
                sleep_time = self.FRAME_TIME - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except Exception as e:
            # log unexpected error
            print("Error di thread bot:", e)
            if self.debug:
                traceback.print_exc()
        finally:
            # release mouse state cleanly
            try:
                self.mouse.release(Button.left)
            except Exception:
                pass
            if self.debug:
                print("Thread Bot telah berhenti.")

# =============================================================================
# KELAS APLIKASI GUI (Tidak ada perubahan besar pada fungsionalitas)
# =============================================================================
class BotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel Kontrol Bot")
        self.root.geometry("420x360")
        self.root.minsize(420, 360)
        self.root.resizable(False, False)

        self.bot = GameBot(debug=False)  # set True untuk log lebih detail
        self.bot_thread = None
        self.config_file = "area_config.json"

        # UI vars
        self.area_label_var = tk.StringVar(value="Area belum dipilih")
        self.status_var = tk.StringVar(value="Status: Menunggu")
        self.level_var = tk.StringVar(value="Level: Medium")
        self.decision_var = tk.StringVar(value="Keputusan: DIAM")
        self.intelligence_level_var = tk.StringVar(value="Medium")

        self.click_delay_var = tk.DoubleVar(value=1.5)
        self.delay_label_var = tk.StringVar(value=f"{self.click_delay_var.get():.2f} detik")
        self.random_delay_var = tk.BooleanVar(value=False)

        self._create_widgets()
        self._load_area_config()
        self.on_delay_change(self.click_delay_var.get())

        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.keyboard_listener = Listener(on_press=self._on_global_press)
        self.keyboard_listener.start()

    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        setup_frame = ttk.LabelFrame(main_frame, text="Pengaturan Area", padding="5")
        setup_frame.pack(fill=tk.X, pady=5)
        ttk.Button(setup_frame, text="Pilih Area Permainan", command=self.select_area).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Label(setup_frame, textvariable=self.area_label_var, wraplength=180).pack(side=tk.LEFT, padx=5)

        control_frame = ttk.LabelFrame(main_frame, text="Kontrol (Tombol atau F4)", padding="5")
        control_frame.pack(fill=tk.X, pady=5)
        options = list(self.bot.intelligence_presets.keys()) + ["Random"]
        self.level_menu = ttk.OptionMenu(control_frame, self.intelligence_level_var, "Medium", *options, command=self.on_level_change)
        self.level_menu.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.toggle_button = ttk.Button(control_frame, text="Mulai Bot", command=self.toggle_bot, width=15)
        self.toggle_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.toggle_button.state(['disabled'])

        delay_frame = ttk.LabelFrame(main_frame, text="Pengaturan Delay Klik Otomatis", padding="5")
        delay_frame.pack(fill=tk.X, pady=5)
        ttk.Label(delay_frame, text="Delay:").pack(side=tk.LEFT, padx=(5,0))
        self.delay_slider = ttk.Scale(delay_frame, from_=0.5, to=5.0, orient=tk.HORIZONTAL, variable=self.click_delay_var, command=self.on_delay_change)
        self.delay_slider.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Label(delay_frame, textvariable=self.delay_label_var, width=10).pack(side=tk.LEFT, padx=(0,5))

        self.random_delay_check = ttk.Checkbutton(delay_frame, text="Acak", variable=self.random_delay_var, command=self.on_random_delay_toggle)
        self.random_delay_check.pack(side=tk.LEFT, padx=5)

        # disable until area chosen
        self.delay_slider.state(['disabled'])
        self.random_delay_check.state(['disabled'])

        status_frame = ttk.LabelFrame(main_frame, text="Status Real-time", padding="5")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(status_frame, textvariable=self.status_var).pack(anchor="w")
        ttk.Label(status_frame, textvariable=self.level_var).pack(anchor="w")
        ttk.Label(status_frame, textvariable=self.decision_var).pack(anchor="w")

    def _load_area_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    area = json.load(f)
                if all(k in area for k in ('top', 'left', 'width', 'height')):
                    self.bot.area_game = area
                    self.area_label_var.set(f"Area: {area['width']}x{area['height']} di ({area['left']},{area['top']})")
                    self.toggle_button.state(['!disabled'])
                    self.delay_slider.state(['!disabled'])
                    self.random_delay_check.state(['!disabled'])
                    if self.bot.debug:
                        print("Konfigurasi area berhasil dimuat.")
            except Exception as e:
                self.area_label_var.set("Gagal memuat config")
                print(f"Error memuat config: {e}")

    def select_area(self):
        # minimize root while selecting
        self.root.withdraw()
        time.sleep(0.2)
        selected_area = self.bot.setup_manual()
        if selected_area:
            self.area_label_var.set(f"Area: {selected_area['width']}x{selected_area['height']} di ({selected_area['left']},{selected_area['top']})")
            self.toggle_button.state(['!disabled'])
            self.delay_slider.state(['!disabled'])
            self.random_delay_check.state(['!disabled'])
            try:
                with open(self.config_file, 'w') as f:
                    json.dump(selected_area, f)
                if self.bot.debug:
                    print("Konfigurasi area baru disimpan.")
            except IOError as e:
                print(f"Gagal menyimpan area: {e}")
        self.root.deiconify()

    def on_delay_change(self, value):
        delay_value = float(value)
        self.delay_label_var.set(f"{delay_value:.2f} detik")
        self.bot.set_click_delay(delay_value)

    def on_random_delay_toggle(self):
        is_enabled = self.random_delay_var.get()
        self.bot.set_random_delay_mode(is_enabled)
        if is_enabled:
            self.delay_slider.state(['disabled'])
            self.delay_label_var.set("Acak")
        else:
            self.delay_slider.state(['!disabled'])
            self.on_delay_change(self.click_delay_var.get())

    def on_level_change(self, level):
        self.bot.set_intelligence(level)

    def _on_global_press(self, key):
        if key == Key.f4:
            self.root.after(0, self.toggle_bot)

    def toggle_bot(self):
        if 'disabled' in self.toggle_button.state():
            print("Peringatan: Area belum dipilih. Tekan F4 diabaikan.")
            return

        if self.bot_thread and self.bot_thread.is_alive():
            # currently running thread -> toggle pause/resume
            if self.bot.is_paused:
                print("Melanjutkan bot...")
                self.bot.resume_action_pending = True
                self.bot.is_paused = False
                self.toggle_button.config(text="Jeda Bot")
                self.level_menu.config(state='disabled')
                self.delay_slider.config(state='disabled')
                self.random_delay_check.config(state='disabled')
            else:
                print("Menjeda bot...")
                self.bot.is_paused = True
                self.toggle_button.config(text="Lanjutkan")
                self.level_menu.config(state='normal')
                self.random_delay_check.config(state='normal')
                if not self.random_delay_var.get():
                    self.delay_slider.config(state='normal')
        else:
            # start for first time
            print("Memulai bot untuk pertama kali...")
            self.bot.is_paused = False
            self.bot.stop_event.clear()
            self.bot_thread = threading.Thread(target=self.bot.run, daemon=True)
            self.bot_thread.start()
            self.toggle_button.config(text="Jeda Bot")
            self.level_menu.config(state='disabled')
            self.delay_slider.config(state='disabled')
            self.random_delay_check.config(state='disabled')
            self._update_status_labels()

    def _update_status_labels(self):
        self.status_var.set(f"Status: {self.bot.status_text}")
        self.level_var.set(f"Level: {self.bot.display_level}")
        self.decision_var.set(f"Keputusan: {self.bot.keputusan}")
        if self.bot_thread and self.bot_thread.is_alive():
            self.root.after(100, self._update_status_labels)

    def quit_app(self):
        print("Menutup aplikasi...")
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        # request bot stop and wait a short time
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot.stop_event.set()
            self.bot_thread.join(timeout=1.0)
        self.root.destroy()

if __name__ == "__main__":
    try:
        root = ThemedTk(theme="arc")
    except Exception as e:
        print(f"Gagal memuat tema 'arc', menggunakan tema default Tk. Error: {e}")
        root = tk.Tk()
    app = BotApp(root)
    root.mainloop()