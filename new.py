import json
import os
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog

KV = '''
<BoardScreen>:
    name: "board"
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(10)

        MDTopAppBar:
            title: "GoalPlan"
            right_action_items: [["plus", lambda x: app.show_add_board_dialog()]]
            left_action_items: [["menu", lambda x: app.open_board_menu()]]

        ScrollView:
            do_scroll_y: False
            MDBoxLayout:
                id: list_container
                spacing: dp(15)
                padding: dp(10)
                adaptive_height: True
                size_hint_x: None
                width: self.minimum_width
                orientation: "horizontal"
'''

class ListColumn(MDCard):
    def __init__(self, title, board_name, **kwargs):
        super().__init__(**kwargs)
        self.board_name = board_name
        self.list_name = title
        self.orientation = "vertical"
        self.size_hint = (None, None)
        self.width = dp(280)
        self.height = dp(500)
        self.padding = dp(10)
        self.spacing = dp(10)
        self.radius = [15, 15, 15, 15]
        self.md_bg_color = [1, 1, 1, 1]
        self.elevation = 4

        self.add_widget(MDLabel(text=title, halign="center", bold=True, font_style="H6", size_hint_y=None, height=dp(40)))

        self.scroll = MDScrollView(size_hint=(1, 1))
        self.card_container = MDBoxLayout(orientation="vertical", adaptive_height=True, size_hint_y=None)
        self.scroll.add_widget(self.card_container)
        self.add_widget(self.scroll)

        self.input = MDTextField(hint_text="Новая карточка", size_hint_x=1)
        self.add_widget(self.input)

        self.add_widget(MDRaisedButton(text="Добавить", pos_hint={"center_x": 0.5}, on_release=self.add_card))

    def add_card(self, _):
        card_text = self.input.text.strip()
        if card_text:
            self.add_card_to_ui(card_text)
            self.input.text = ""
            app.save_card(self.board_name, self.list_name, card_text)

    def add_card_to_ui(self, text):
        card = MDCard(orientation="vertical", padding=dp(8), size_hint_y=None, height=dp(70), md_bg_color=[0.9, 0.95, 1, 1], radius=[10]*4)
        card.add_widget(MDLabel(text=text, halign="left", valign="top", theme_text_color="Primary"))
        self.card_container.add_widget(card)

class BoardScreen(MDScreen):
    pass

class GoalPlan(MDApp):
    def build(self):
        global app
        app = self
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        Builder.load_string(KV)

        self.data_file = "boards.json"
        self.load_data()

        self.screen = BoardScreen()
        self.board_menu = None
        self.current_board = list(self.boards.keys())[0] if self.boards else "Новая доска"
        if self.current_board not in self.boards:
            self.boards[self.current_board] = {}
        self.load_board(self.current_board)

        return self.screen

    def load_data(self):
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                self.boards = json.load(f).get("boards", {})
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            self.boards = {"Новая доска": {"Список задач": [], "В процессе": [], "Готово": []}}
            self.save_data()

    def save_data(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump({"boards": self.boards}, f, ensure_ascii=False, indent=4)

    def save_card(self, board, list_name, card_text):
        if board in self.boards and list_name in self.boards[board]:
            self.boards[board][list_name].append(card_text)
            self.save_data()

    def load_board(self, board_name):
        self.screen.ids.list_container.clear_widgets()
        self.current_board = board_name
        for list_name, cards in self.boards[board_name].items():
            column = ListColumn(title=list_name, board_name=board_name)
            for card in cards:
                column.add_card_to_ui(card)
            self.screen.ids.list_container.add_widget(column)

    def open_board_menu(self):
        menu_items = [{"text": board, "on_release": lambda x=board: self.select_board(x)} for board in self.boards]
        self.board_menu = MDDropdownMenu(caller=self.screen.ids.list_container, items=menu_items, width_mult=4)
        self.board_menu.open()

    def select_board(self, board_name):
        if self.board_menu:
            self.board_menu.dismiss()
        self.load_board(board_name)

    def show_add_board_dialog(self):
        self.dialog_input = MDTextField(hint_text="Название доски")
        self.dialog = MDDialog(
            title="Новая доска",
            type="custom",
            content_cls=self.dialog_input,
            buttons=[
                MDRaisedButton(text="Создать", on_release=self.create_board),
                MDRaisedButton(text="Отмена", on_release=lambda x: self.dialog.dismiss())
            ]
        )
        self.dialog.open()

    def create_board(self, _):
        board_name = self.dialog_input.text.strip()
        if board_name and board_name not in self.boards:
            self.boards[board_name] = {"Список задач": [], "В процессе": [], "Готово": []}
            self.save_data()
            self.dialog.dismiss()
            self.load_board(board_name)

if __name__ == '__main__':
    GoalPlan().run()
