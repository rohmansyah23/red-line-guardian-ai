import pygame
import sys
import random
import time

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 150
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Game Jaga Garis Merah (Warna Dinamis)")

WARNA_LATAR = (0, 0, 0)
WARNA_PUTIH = (255, 255, 255)
WARNA_PUTIH_TIDAK_SELARAS = (170, 170, 170)  # #AAAAAA
WARNA_MERAH = (189, 0, 0)
WARNA_KOTAK_PENGECOH = (190, 0, 0)  # #FF0000

lebar_bar_putih, lebar_garis_merah = 150, 5
bar_putih = pygame.Rect(0, 0, lebar_bar_putih, SCREEN_HEIGHT)
garis_merah = pygame.Rect(0, 0, lebar_garis_merah, SCREEN_HEIGHT)

lebar_kotak_pengecoh, tinggi_kotak_pengecoh = 40, 40
kotak_merah_pengecoh = pygame.Rect(0, 0, lebar_kotak_pengecoh, tinggi_kotak_pengecoh)
kecepatan_kotak_pengecoh_x = 3
kecepatan_kotak_pengecoh_y = 3

kotak_merah_pengecoh.x = random.randint(0, SCREEN_WIDTH - lebar_kotak_pengecoh)
kotak_merah_pengecoh.y = random.randint(0, SCREEN_HEIGHT - tinggi_kotak_pengecoh)
kecepatan_kotak_pengecoh_x = random.choice([-3, 3])
kecepatan_kotak_pengecoh_y = random.choice([-3, 3])

kecepatan_bar_putih = 4
kecepatan_garis_merah = 1
CHANGE_DIRECTION_CHANCE = 250
UNALIGNED_TIME_LIMIT = 5
clock = pygame.time.Clock()

game_status = 'start_menu'
warna_ronde_selesai_acak = (0, 0, 0)
round_end_message = ""
waktu_mulai_tunggu = 0
durasi_tunggu = 0
waktu_mulai_ronde, durasi_ronde = 0, 0
time_unaligned_start = 0
is_aligned = False

# Flag untuk menandai apakah ronde berakhir karena gagal
last_round_failed = False

font_utama = pygame.font.Font(None, 50)
font_instruksi = pygame.font.Font(None, 30)
font_timer = pygame.font.Font(None, 25)

def start_new_round():
    global game_status, waktu_mulai_ronde, durasi_ronde, time_unaligned_start, kecepatan_garis_merah
    global kecepatan_kotak_pengecoh_x, kecepatan_kotak_pengecoh_y, last_round_failed

    # reset flag gagal saat memulai ronde baru
    last_round_failed = False

    bar_putih.x = random.randint(0, SCREEN_WIDTH - lebar_bar_putih)
    garis_merah.x = random.randint(0, SCREEN_WIDTH - lebar_garis_merah)
    kecepatan_garis_merah = random.choice([-2, 2])

    kotak_merah_pengecoh.x = random.randint(0, SCREEN_WIDTH - lebar_kotak_pengecoh)
    kotak_merah_pengecoh.y = random.randint(0, SCREEN_HEIGHT - tinggi_kotak_pengecoh)
    kecepatan_kotak_pengecoh_x = random.choice([-3, -2, 2, 3])
    kecepatan_kotak_pengecoh_y = random.choice([-3, -2, 2, 3])

    durasi_ronde = random.uniform(15, 15)
    waktu_mulai_ronde = time.time()
    time_unaligned_start = 0
    game_status = 'playing'
    print(f"--- Ronde Baru Dimulai! Durasi: {durasi_ronde:.2f} detik ---")

def start_countdown():
    global game_status, waktu_mulai_tunggu, durasi_tunggu
    game_status = 'waiting'
    waktu_mulai_tunggu = time.time()
    durasi_tunggu = random.uniform(5, 15)
    print(f"Jeda dimulai. Ronde berikutnya dalam {durasi_tunggu:.2f} detik...")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_status == 'start_menu':
                start_countdown()
            elif game_status == 'prompt_next_round':
                start_countdown()
            elif game_status == 'waiting':
                # Klik terlalu awal -> gagal
                game_status = 'prompt_next_round'
                # Saat klik terlalu awal, gunakan warna kotak sebagai warna ronde selesai
                warna_ronde_selesai_acak = WARNA_KOTAK_PENGECOH
                round_end_message = "GAGAL: KLIK TERLALU AWAL"
                last_round_failed = True
                print("--- GAGAL! Klik terdeteksi saat countdown! Bot terjebak! ---")

   
    if game_status == 'playing':
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]: bar_putih.x += kecepatan_bar_putih
        else: bar_putih.x -= kecepatan_bar_putih
        if bar_putih.left < 0: bar_putih.left = 0
        if bar_putih.right > SCREEN_WIDTH: bar_putih.right = SCREEN_WIDTH

        garis_merah.x += kecepatan_garis_merah
        if random.randint(1, CHANGE_DIRECTION_CHANCE) == 1:
            kecepatan_garis_merah *= -1
        if garis_merah.left <= 0 or garis_merah.right >= SCREEN_WIDTH:
            kecepatan_garis_merah *= -1
            if kecepatan_garis_merah > 0:
                kecepatan_garis_merah = random.randint(2, kecepatan_bar_putih)
            else:
                kecepatan_garis_merah = random.randint(-kecepatan_bar_putih, -2)
        
        kotak_merah_pengecoh.x += kecepatan_kotak_pengecoh_x
        kotak_merah_pengecoh.y += kecepatan_kotak_pengecoh_y
        if kotak_merah_pengecoh.left <= 0 or kotak_merah_pengecoh.right >= SCREEN_WIDTH:
            kecepatan_kotak_pengecoh_x *= -1
        if kotak_merah_pengecoh.top <= 0 or kotak_merah_pengecoh.bottom >= SCREEN_HEIGHT:
            kecepatan_kotak_pengecoh_y *= -1

        waktu_ronde_berlalu = time.time() - waktu_mulai_ronde
        if waktu_ronde_berlalu > durasi_ronde:
            game_status = 'prompt_next_round'
            round_end_message = "RONDE SELESAI"
            # waktu habis = sukses, bukan gagal
            last_round_failed = False
            # gunakan warna latar atau warna lain untuk hasil sukses
            warna_ronde_selesai_acak = WARNA_LATAR
            print("--- Waktu Habis! Anda Bertahan! Ronde Selesai ---")

        is_aligned = garis_merah.centerx >= bar_putih.left and garis_merah.centerx <= bar_putih.right
        if is_aligned:
            time_unaligned_start = 0
        else:
            if time_unaligned_start == 0:
                time_unaligned_start = time.time()
            else:
                waktu_tidak_selaras = time.time() - time_unaligned_start
                if waktu_tidak_selaras > UNALIGNED_TIME_LIMIT:
                    game_status = 'prompt_next_round'
                    round_end_message = "RONDE SELESAI"
                    # Gagal karena tidak selaras -> tandai sebagai gagal
                    last_round_failed = True
                    warna_ronde_selesai_acak = WARNA_KOTAK_PENGECOH
                    print(f"--- Gagal Bertahan lebih dari {UNALIGNED_TIME_LIMIT} detik! Ronde Selesai ---")

    elif game_status == 'waiting':
        kotak_merah_pengecoh.x += kecepatan_kotak_pengecoh_x
        kotak_merah_pengecoh.y += kecepatan_kotak_pengecoh_y
        if kotak_merah_pengecoh.left <= 0 or kotak_merah_pengecoh.right >= SCREEN_WIDTH:
            kecepatan_kotak_pengecoh_x *= -1
        if kotak_merah_pengecoh.top <= 0 or kotak_merah_pengecoh.bottom >= SCREEN_HEIGHT:
            kecepatan_kotak_pengecoh_y *= -1
        if time.time() - waktu_mulai_tunggu > durasi_tunggu:
            start_new_round()

   
    if game_status == 'start_menu':
        screen.fill(WARNA_LATAR)
        judul_teks = font_utama.render("Jaga Garis Merah", True, WARNA_PUTIH)
        mulai_teks = font_instruksi.render("Klik Kiri untuk Memulai Permainan", True, WARNA_PUTIH)
        posisi_judul = judul_teks.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 20))
        posisi_mulai = mulai_teks.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 20))
        screen.blit(judul_teks, posisi_judul)
        screen.blit(mulai_teks, posisi_mulai)

    elif game_status == 'playing':
        screen.fill(WARNA_LATAR)
       
        # Ganti warna bar berdasarkan keselarasan dengan garis merah
        bar_warna_terpakai = WARNA_PUTIH if is_aligned else WARNA_PUTIH_TIDAK_SELARAS

        pygame.draw.rect(screen, bar_warna_terpakai, bar_putih)
        pygame.draw.rect(screen, WARNA_MERAH, garis_merah)
        pygame.draw.rect(screen, WARNA_KOTAK_PENGECOH, kotak_merah_pengecoh)
        
        waktu_tersisa_ronde = durasi_ronde - (time.time() - waktu_mulai_ronde)
        teks_timer = font_timer.render(f"Bertahan: {int(waktu_tersisa_ronde)}s", True, WARNA_PUTIH)
        screen.blit(teks_timer, (10, 10))
        if time_unaligned_start != 0:
            waktu_tersisa_gagal = UNALIGNED_TIME_LIMIT - (time.time() - time_unaligned_start)
           
            teks_gagal = font_timer.render(f"Gagal dalam: {waktu_tersisa_gagal:.1f}s", True, WARNA_MERAH)
            screen.blit(teks_gagal, (10, 30))
    
    elif game_status == 'prompt_next_round':
        # Jika ronde berakhir karena gagal, fill = warna kotak; kalau tidak, gunakan warna hasil ronde yang lain
        if last_round_failed:
            screen.fill(WARNA_KOTAK_PENGECOH)
        else:
            screen.fill(warna_ronde_selesai_acak)
        teks_selesai = font_utama.render(round_end_message, True, WARNA_PUTIH)
        teks_mulai_lagi = font_instruksi.render("Klik Kiri untuk Memulai Jeda", True, WARNA_PUTIH)
        posisi_selesai = teks_selesai.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 20))
        posisi_mulai_lagi = teks_mulai_lagi.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 20))
        screen.blit(teks_selesai, posisi_selesai)
        screen.blit(teks_mulai_lagi, posisi_mulai_lagi)
        
    elif game_status == 'waiting':
        screen.fill(WARNA_LATAR)
        pygame.draw.rect(screen, WARNA_KOTAK_PENGECOH, kotak_merah_pengecoh)
        waktu_tersisa = durasi_tunggu - (time.time() - waktu_mulai_tunggu)
        teks_menunggu = font_instruksi.render(f"Ronde Berikutnya dalam {int(waktu_tersisa)} detik", True, WARNA_PUTIH)
        posisi_menunggu = teks_menunggu.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        screen.blit(teks_menunggu, posisi_menunggu)

    pygame.display.update()
    clock.tick(60)