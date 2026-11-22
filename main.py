import os
import shutil
import random
from kivy.uix.image import Image
from PIL import Image as PILImage, ImageOps
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
try:
    from plyer import filechooser
except ImportError:
    filechooser = None
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.slider import Slider




# Calcola il percorso sicuro senza bisogno di permessi su Android 10+
if platform == 'android':
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    context = PythonActivity.mActivity
    external_files_dir = context.getExternalFilesDir(None).getAbsolutePath()
    DEFAULT_PATH = os.path.join(external_files_dir, "MemoPhotos")
else:
    DEFAULT_PATH = os.path.join(os.path.expanduser("~"), "Downloads", "MemoPhotos")

# Crea la cartella se non esiste ancora
os.makedirs(DEFAULT_PATH, exist_ok=True)

DEFAULT_VICTORY_MSG = "Complimenti! Hai trovato tutte le coppie!"
if platform == 'android':
    CONFIG_PATH = os.path.join(external_files_dir, "memo_config.json")
else:
    CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memo_config.json")

store = JsonStore(CONFIG_PATH)



class RoundedButton(Button):
    """Pulsante personalizzato con angoli arrotondati ed effetto rilievo."""
    def __init__(self, bg_color=(0.18, 0.75, 0.42, 1), radius=25, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)  # Rende trasparente lo sfondo standard
        self.bg_color = bg_color
        self.radius = [radius]
        self.bold = True

        with self.canvas.before:
            # Ombra inferiore per dare profondità 3D
            self.shadow_color = Color(0, 0, 0, 0.35)
            self.shadow_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
            # Colore principale del pulsante
            self.rect_color = Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)

        self.bind(pos=self._update_graphics, size=self._update_graphics, state=self._update_state)

    def _update_graphics(self, *args):
        # L'ombra resta leggermente spostata verso il basso
        self.shadow_rect.pos = (self.x, self.y - 5)
        self.shadow_rect.size = self.size
        # Se il tasto è premuto si abbassa leggermente per simulare il click
        offset = -3 if self.state == 'down' else 0
        self.rect.pos = (self.x, self.y + offset)
        self.rect.size = self.size

    def _update_state(self, instance, value):
        if value == 'down':
            # Scurisce leggermente il colore alla pressione
            self.rect_color.rgba = (
                self.bg_color[0] * 0.8,
                self.bg_color[1] * 0.8,
                self.bg_color[2] * 0.8,
                1
            )
        else:
            self.rect_color.rgba = self.bg_color
        self._update_graphics()


class MainMenuScreen(Screen):
    """Schermata principale pulita con avvio rapido e accesso alle opzioni."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=[40, 30, 40, 30], spacing=25)
        
        # Titolo più grande e in grassetto
        title = Label(
            text="MEMO GAME", 
            font_size=44, 
            bold=True,
            color=(0.95, 0.97, 1, 1),
            size_hint_y=0.32
        )
        layout.add_widget(title)
        
        # Tasto GIOCA grande, arrotondato e con simbolo play
        btn_play = RoundedButton(
            text="GIOCA", 
            font_size=32, 
            size_hint_y=0.28, 
            bg_color=(0.15, 0.78, 0.42, 1),
            radius=30
        )
        btn_play.bind(on_press=self.start_game)
        layout.add_widget(btn_play)
        
        # Tasto Opzioni coordinato ma più compatto
        btn_options = RoundedButton(
            text="Opzioni", 
            font_size=22, 
            size_hint_y=0.16, 
            bg_color=(0.22, 0.55, 0.92, 1),
            radius=22
        )
        btn_options.bind(on_press=self.go_to_options)
        layout.add_widget(btn_options)
        
        self.error_label = Label(
            text="", 
            color=(1, 0.35, 0.35, 1), 
            halign='center',
            size_hint_y=0.18
        )       
        self.error_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width * 0.9, None)))
        layout.add_widget(self.error_label)
        
        self.add_widget(layout)

    def on_enter(self):
        self.error_label.text = ""

    def get_saved_path(self):
        if store.exists('settings'):
            saved = store.get('settings').get('folder_path', DEFAULT_PATH)
            if os.path.exists(saved):
                return saved
        return DEFAULT_PATH

    def start_game(self, instance):
        folder_path = self.get_saved_path()
        os.makedirs(folder_path, exist_ok=True)
            
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
        images = [
            os.path.join(folder_path, f) 
            for f in os.listdir(folder_path) 
            if f.lower().endswith(valid_extensions)
        ]
        
        if len(images) < 2:
            self.error_label.text = f"Trovate solo {len(images)} foto.\nVai in Opzioni e importa almeno 4 foto!"
            return
            
        game_screen = self.manager.get_screen('game')
        game_screen.setup_game(images)
        self.manager.current = 'game'

    def go_to_options(self, instance):
        self.manager.current = 'options'


class OptionsScreen(Screen):
    """Schermata dedicata all'importazione foto e al messaggio di vittoria."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=25, spacing=12)
        
        layout.add_widget(Label(text="Opzioni", font_size=28, size_hint_y=0.12))
        
        # Pulsante per aprire la Galleria
        btn_import = Button(
            text="Importa Foto dalla Galleria", 
            font_size=18,
            size_hint_y=0.15, 
            background_color=(0.2, 0.7, 0.3, 1)
        )
        btn_import.bind(on_press=self.open_gallery)
        layout.add_widget(btn_import)

        # Pulsante per cancellare le foto attuali
        btn_clear = Button(
            text="Svuota Foto Caricate", 
            font_size=16,
            size_hint_y=0.11, 
            background_color=(0.8, 0.3, 0.3, 1)
        )
        btn_clear.bind(on_press=self.clear_photos)
        layout.add_widget(btn_clear)
        self.pairs_label = Label(text="Numero di coppie (foto): 8", size_hint_y=0.08)
        layout.add_widget(self.pairs_label)

        self.pairs_slider = Slider(min=2, max=12, value=8, step=1, size_hint_y=0.1)
        self.pairs_slider.bind(value=self.on_pairs_change)
        layout.add_widget(self.pairs_slider)

        layout.add_widget(Label(text="Messaggio di vittoria:", size_hint_y=0.08))
        self.victory_msg_input = TextInput(multiline=False, size_hint_y=0.12)
        layout.add_widget(self.victory_msg_input)
        
        btn_save = Button(
            text="Salva Impostazioni", 
            size_hint_y=0.13, 
            background_color=(0.2, 0.6, 1, 1)
        )
        btn_save.bind(on_press=self.save_settings)
        layout.add_widget(btn_save)

        btn_back = Button(text="Torna al Menu", size_hint_y=0.13)
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        
        self.status_label = Label(text="", size_hint_y=0.16, halign='center')
        self.status_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width * 0.9, None)))
        layout.add_widget(self.status_label)
        self.on_enter()

        self.add_widget(layout)

    def on_pairs_change(self, instance, value):
        num_pairs = int(value)
        self.pairs_label.text = f"Numero di coppie (foto): {num_pairs} ({num_pairs * 2} carte)"
        current_msg = store.get('settings').get('victory_msg', DEFAULT_VICTORY_MSG) if store.exists('settings') else DEFAULT_VICTORY_MSG
        store.put('settings', folder_path=DEFAULT_PATH, victory_msg=current_msg, num_pairs=num_pairs)

    def on_enter(self):
        self.update_photo_count()
        if store.exists('settings'):
            settings = store.get('settings')
            self.victory_msg_input.text = settings.get('victory_msg', DEFAULT_VICTORY_MSG)
            saved_pairs = settings.get('num_pairs', 8)
            self.pairs_slider.value = saved_pairs
            self.on_pairs_change(self.pairs_slider, saved_pairs)
        else:
            self.victory_msg_input.text = DEFAULT_VICTORY_MSG
            self.pairs_slider.value = 8




    def update_photo_count(self):
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
        count = len([f for f in os.listdir(DEFAULT_PATH) if f.lower().endswith(valid_extensions)])
        self.status_label.color = (0.8, 0.9, 1, 1)
        self.status_label.text = f"Foto pronte per il gioco: {count}"

    def open_gallery(self, instance):
        try:
            filechooser.open_file(
                on_selection=self.handle_selection,
                multiple=True,
                filters=[["Immagini", "*.png", "*.jpg", "*.jpeg", "*.webp"]]
            )
        except Exception as e:
            self.status_label.color = (1, 0.3, 0.3, 1)
            self.status_label.text = f"Errore apertura galleria: {e}"

    def handle_selection(self, selection):
        # Plyer esegue questo callback su un thread secondario: usiamo Clock per aggiornare la UI
        Clock.schedule_once(lambda dt: self._copy_selected_files(selection), 0)

    def _copy_selected_files(self, selection):
        if not selection:
            return
            
        copied = 0
        for src_path in selection:
            if os.path.exists(src_path):
                filename = f"foto_{random.randint(10000, 99999)}.jpg"
                dst_path = os.path.join(DEFAULT_PATH, filename)
                try:
                    with PILImage.open(src_path) as img:
                        # 1. Corregge l'orientamento (evita foto sdraiate su Android)
                        img = ImageOps.exif_transpose(img)
                        # 2. Converte in RGB (necessario per salvare PNG/WEBP come JPG)
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        # 3. Ridimensiona mantenendo le proporzioni (max 600x600 px)
                        img.thumbnail((600, 600), PILImage.Resampling.LANCZOS)
                        img.save(dst_path, "JPEG", quality=85)
                    copied += 1
                except Exception as e:
                    print(f"Errore elaborazione {src_path}: {e}")
                    
        self.update_photo_count()
        if copied > 0:
            self.status_label.color = (0.3, 1, 0.3, 1)
            self.status_label.text = f"Importate {copied} nuove foto!\n" + self.status_label.text

    def clear_photos(self, instance):
        removed = 0
        for f in os.listdir(DEFAULT_PATH):
            file_path = os.path.join(DEFAULT_PATH, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
                removed += 1
        self.status_label.color = (1, 0.8, 0.3, 1)
        self.status_label.text = f"Rimosse {removed} foto. Ora ce ne sono 0."

    def save_settings(self, instance):
        victory_msg = self.victory_msg_input.text.strip()
        if not victory_msg:
            victory_msg = DEFAULT_VICTORY_MSG

        num_pairs = int(self.pairs_slider.value)
        store.put('settings', folder_path=DEFAULT_PATH, victory_msg=victory_msg, num_pairs=num_pairs)
        self.status_label.color = (0.3, 1, 0.3, 1)
        self.status_label.text = "Impostazioni salvate con successo!"

    def go_back(self, instance):
        self.manager.current = 'menu'


class MemoryButton(Button):
    def __init__(self, image_path, **kwargs):
        super().__init__(**kwargs)
        self.image_path = image_path
        self.is_flipped = False
        self.is_matched = False
        self.text = "?"
        self.font_size = 36
        self.bold = True
        self.background_normal = ''
        self.background_color = (0.22, 0.32, 0.48, 1)  # Colore elegante del dorso carta

        # Widget Image interno per mostrare la foto senza deformarla
        self.card_img = Image(
            source=self.image_path,
            fit_mode="contain",  # Mantiene le proporzioni originali senza tagliare
            opacity=0            # Nascosta finché la carta è coperta
        )
        self.add_widget(self.card_img)
        self.bind(pos=self._update_img_layout, size=self._update_img_layout)

    def _update_img_layout(self, *args):
        # Lascia un piccolo margine di 6px intorno alla foto
        padding = 6
        self.card_img.pos = (self.x + padding, self.y + padding)
        self.card_img.size = (max(0, self.width - padding * 2), max(0, self.height - padding * 2))

    def flip(self):
        if not self.is_flipped and not self.is_matched:
            self.is_flipped = True
            self.text = ""
            self.background_color = (0.95, 0.95, 0.95, 1)  # Sfondo chiaro dietro la foto
            self.card_img.opacity = 1
            return True
        return False

    def hide(self):
        self.is_flipped = False
        self.text = "?"
        self.background_color = (0.22, 0.32, 0.48, 1)
        self.card_img.opacity = 0

    def set_matched(self):
        self.is_matched = True
        self.background_color = (0.2, 0.78, 0.42, 1)
        self.card_img.opacity = 1



class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        self.score_label = Label(text="Tentativi: 0", font_size=18)
        
        btn_back = Button(text="Menu", size_hint_x=0.3)
        btn_back.bind(on_press=self.go_back)
        
        top_bar.add_widget(btn_back)
        top_bar.add_widget(self.score_label)
        self.main_layout.add_widget(top_bar)
        
        self.grid = GridLayout(cols=4, spacing=10, size_hint_y=0.9)
        self.main_layout.add_widget(self.grid)
        
        self.add_widget(self.main_layout)
        
        self.first_selected = None
        self.second_selected = None
        self.attempts = 0
        self.total_pairs = 0
        self.matched_pairs = 0
        self.current_images = []

    def setup_game(self, image_list):
        self.current_images = image_list
        self.grid.clear_widgets()
        self.attempts = 0
        self.matched_pairs = 0
        self.score_label.text = "Tentativi: 0"
        self.first_selected = None
        self.second_selected = None
        
                # Legge direttamente il numero scelto nello slider delle Opzioni
        desired_pairs = int(self.manager.get_screen('options').pairs_slider.value)
        self.total_pairs = min(desired_pairs, len(image_list))
        selected_images = random.sample(image_list, self.total_pairs)
        
        game_cards = selected_images * 2
        random.shuffle(game_cards)
        
        # Adatta le colonne della griglia in base a quante carte ci sono
        total_cards = len(game_cards)
        if total_cards <= 4:
            self.grid.cols = 2
        elif total_cards <= 12:
            self.grid.cols = 3
        else:
            self.grid.cols = 4

        
        for img_path in game_cards:
            card = MemoryButton(image_path=img_path)
            card.bind(on_press=self.on_card_click)
            self.grid.add_widget(card)

    def on_card_click(self, card):
        if self.first_selected and self.second_selected:
            return
            
        if card.flip():
            if not self.first_selected:
                self.first_selected = card
            elif card != self.first_selected:
                self.second_selected = card
                self.attempts += 1
                self.score_label.text = f"Tentativi: {self.attempts}"
                Clock.schedule_once(self.check_match, 2.0)

    def check_match(self, dt):
        if not self.first_selected or not self.second_selected:
            return
            
        try:
            if self.first_selected.image_path == self.second_selected.image_path:
                self.first_selected.set_matched()
                self.second_selected.set_matched()
                self.matched_pairs += 1
                
                if self.matched_pairs == self.total_pairs:
                    Clock.schedule_once(self.trigger_victory, 0.6)
            else:
                self.first_selected.hide()
                self.second_selected.hide()
        finally:
            # Sblocca SEMPRE le carte selezionate per permettere i clic successivi
            self.first_selected = None
            self.second_selected = None


    def trigger_victory(self, dt):
        victory_screen = self.manager.get_screen('victory')
        victory_screen.set_results(self.attempts, self.current_images)
        self.manager.current = 'victory'

    def go_back(self, instance):
        self.manager.current = 'menu'


class VictoryScreen(Screen):
    """Schermata mostrata al completamento della partita con messaggio personalizzato."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.images_cache = []
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        self.message_label = Label(
            text=DEFAULT_VICTORY_MSG,
            font_size=28,
            halign='center',
            valign='middle',
            size_hint_y=0.45
        )
        self.message_label.bind(size=self._update_text_width)
        layout.add_widget(self.message_label)
        
        self.stats_label = Label(
            text="",
            font_size=20,
            color=(0.8, 0.9, 1, 1),
            size_hint_y=0.15
        )
        layout.add_widget(self.stats_label)
        
        btn_replay = Button(
            text="Gioca Ancora",
            font_size=22,
            size_hint_y=0.18,
            background_color=(0.2, 0.7, 0.3, 1)
        )
        btn_replay.bind(on_press=self.play_again)
        layout.add_widget(btn_replay)
        
        btn_menu = Button(
            text="Torna al Menu",
            font_size=20,
            size_hint_y=0.15,
            background_color=(0.2, 0.6, 1, 1)
        )
        btn_menu.bind(on_press=self.go_to_menu)
        layout.add_widget(btn_menu)
        
        self.add_widget(layout)

    def _update_text_width(self, instance, value):
        instance.text_size = (instance.width * 0.9, None)

    def set_results(self, attempts, images):
        self.images_cache = images
        self.stats_label.text = f"Partita completata in {attempts} tentativi!"
        
        if store.exists('settings'):
            custom_msg = store.get('settings').get('victory_msg', DEFAULT_VICTORY_MSG)
        else:
            custom_msg = DEFAULT_VICTORY_MSG
            
        self.message_label.text = custom_msg

    def play_again(self, instance):
        game_screen = self.manager.get_screen('game')
        game_screen.setup_game(self.images_cache)
        self.manager.current = 'game'

    def go_to_menu(self, instance):
        self.manager.current = 'menu'


class MemoApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='menu'))
        sm.add_widget(OptionsScreen(name='options'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(VictoryScreen(name='victory'))
        return sm


if __name__ == '__main__':
    MemoApp().run()
	
