import os
import random
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

# Richiede i permessi di lettura solo su Android
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.READ_MEDIA_IMAGES
    ])
    DEFAULT_PATH = "/storage/emulated/0/Download/MemoPhotos"
else:
    # Su Windows/Mac/Linux usa automaticamente la cartella Download dell'utente
    DEFAULT_PATH = os.path.join(os.path.expanduser("~"), "Downloads", "MemoPhotos")

DEFAULT_VICTORY_MSG = "Complimenti! Hai trovato tutte le coppie!"
store = JsonStore('memo_config.json')


class MainMenuScreen(Screen):
    """Schermata principale pulita con avvio rapido e accesso alle opzioni."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        layout.add_widget(Label(text="Memo Game", font_size=36, size_hint_y=0.3))
        
        btn_play = Button(
            text="Gioca", 
            font_size=24, 
            size_hint_y=0.2, 
            background_color=(0.2, 0.7, 0.3, 1)
        )
        btn_play.bind(on_press=self.start_game)
        layout.add_widget(btn_play)
        
        btn_options = Button(
            text="Opzioni", 
            font_size=20, 
            size_hint_y=0.15, 
            background_color=(0.2, 0.6, 1, 1)
        )
        btn_options.bind(on_press=self.go_to_options)
        layout.add_widget(btn_options)
        
        self.error_label = Label(
            text="", 
            color=(1, 0.3, 0.3, 1), 
            halign='center',
            size_hint_y=0.2
        )       
        self.error_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width * 0.9, None)))
        layout.add_widget(self.error_label)
        
        self.add_widget(layout)

    def on_enter(self):
        self.error_label.text = ""

    def get_saved_path(self):
        if store.exists('settings'):
            return store.get('settings').get('folder_path', DEFAULT_PATH)
        return DEFAULT_PATH

    def start_game(self, instance):
        folder_path = self.get_saved_path()
        
        if not os.path.exists(folder_path):
            self.error_label.text = f"Cartella non trovata:\n{folder_path}\nConfigurala nelle Opzioni."
            return
            
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
        images = [
            os.path.join(folder_path, f) 
            for f in os.listdir(folder_path) 
            if f.lower().endswith(valid_extensions)
        ]
        
        if len(images) < 4:
            self.error_label.text = f"Servono almeno 4 immagini in:\n{folder_path}"
            return
            
        game_screen = self.manager.get_screen('game')
        game_screen.setup_game(images)
        self.manager.current = 'game'

    def go_to_options(self, instance):
        self.manager.current = 'options'


class OptionsScreen(Screen):
    """Schermata dedicata alla configurazione del percorso e del messaggio di vittoria."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=25, spacing=12)
        
        layout.add_widget(Label(text="Opzioni", font_size=28, size_hint_y=0.15))
        
        layout.add_widget(Label(text="Percorso della cartella con le foto:", size_hint_y=0.08))
        self.path_input = TextInput(multiline=False, size_hint_y=0.12)
        layout.add_widget(self.path_input)
        
        layout.add_widget(Label(text="Messaggio di vittoria:", size_hint_y=0.08))
        self.victory_msg_input = TextInput(multiline=False, size_hint_y=0.12)
        layout.add_widget(self.victory_msg_input)
        
        btn_save = Button(
            text="Salva Impostazioni", 
            size_hint_y=0.15, 
            background_color=(0.2, 0.6, 1, 1)
        )
        btn_save.bind(on_press=self.save_settings)
        layout.add_widget(btn_save)

        btn_back = Button(text="Torna al Menu", size_hint_y=0.13)
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        
        self.status_label = Label(text="", size_hint_y=0.12)
        layout.add_widget(self.status_label)
        
        self.add_widget(layout)

    def on_enter(self):
        self.status_label.text = ""
        if store.exists('settings'):
            settings = store.get('settings')
            self.path_input.text = settings.get('folder_path', DEFAULT_PATH)
            self.victory_msg_input.text = settings.get('victory_msg', DEFAULT_VICTORY_MSG)
        else:
            self.path_input.text = DEFAULT_PATH
            self.victory_msg_input.text = DEFAULT_VICTORY_MSG

    def save_settings(self, instance):
        folder_path = self.path_input.text.strip().strip('"').strip("'")
        victory_msg = self.victory_msg_input.text.strip()
        
        if not os.path.exists(folder_path):
            self.status_label.color = (1, 0.3, 0.3, 1)
            self.status_label.text = "Errore: Il percorso inserito non esiste!"
            return

        if not victory_msg:
            victory_msg = DEFAULT_VICTORY_MSG

        self.path_input.text = folder_path
        store.put('settings', folder_path=folder_path, victory_msg=victory_msg)
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
        self.font_size = 32

    def flip(self):
        if not self.is_flipped and not self.is_matched:
            self.is_flipped = True
            self.text = ""
            self.background_normal = self.image_path
            return True
        return False

    def hide(self):
        self.is_flipped = False
        self.text = "?"
        self.background_normal = ''

    def set_matched(self):
        self.is_matched = True
        self.disabled = True
        self.background_disabled_normal = self.image_path


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
        
        self.total_pairs = min(8, len(image_list))
        selected_images = random.sample(image_list, self.total_pairs)
        
        game_cards = selected_images * 2
        random.shuffle(game_cards)
        
        self.grid.cols = 4 if len(game_cards) >= 8 else 2
        
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
                Clock.schedule_once(self.check_match, 1.0)

    def check_match(self, dt):
        if self.first_selected.image_path == self.second_selected.image_path:
            self.first_selected.set_matched()
            self.second_selected.set_matched()
            self.matched_pairs += 1
            
            if self.matched_pairs == self.total_pairs:
                Clock.schedule_once(self.trigger_victory, 0.6)
        else:
            self.first_selected.hide()
            self.second_selected.hide()
            
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
    

