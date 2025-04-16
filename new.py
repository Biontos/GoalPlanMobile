import json
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.behaviors import DragBehavior
from kivy.uix.relativelayout import RelativeLayout
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog
from kivy.core.window import Window
Window.clearcolor = (0.96, 0.94, 0.90, 1)
Window.size = (360, 640)
KV = '''
<BoardScreen>:
    name: "board"
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(8)
        spacing: dp(8)

        MDTopAppBar:
            title: "GoalPlan"
            elevation: 2
            md_bg_color: app.theme_cls.primary_color
            left_action_items: [["menu", lambda x: app.open_board_menu()]]
            right_action_items: [["plus", lambda x: app.show_add_board_dialog()]]
            size_hint_y: None
            height: dp(48)

        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(42)
            padding: dp(4)
            spacing: dp(4)
            MDFlatButton:
                text: "Список задач"
                on_release: app.scroll_to_column("Список задач")
            MDFlatButton:
                text: "В процессе"
                on_release: app.scroll_to_column("В процессе")
            MDFlatButton:
                text: "Готово"
                on_release: app.scroll_to_column("Готово")

        ScrollView:
            id: scroll_view
            do_scroll_x: True
            do_scroll_y: False

            MDBoxLayout:
                id: list_container
                spacing: dp(12)
                padding: dp(8)
                adaptive_height: True
                size_hint_x: None
                width: self.minimum_width
                orientation: "horizontal"
'''

class DraggableCard(DragBehavior, RelativeLayout):
    def __init__(self, text, list_column, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(60)
        self.list_column = list_column
        self.card_text = text

        card = MDCard(orientation="horizontal", padding=dp(8),
                      md_bg_color=[0.9, 0.95, 1, 1], radius=[10] * 4,
                      size_hint=(1, 1))
        card.add_widget(MDLabel(text=text, halign="left", valign="top", theme_text_color="Primary"))

        delete_button = MDIconButton(icon="delete", pos_hint={"center_y": 0.5},
                                     on_release=lambda x: app.remove_card_ui(self, list_column))
        card.add_widget(delete_button)
        self.add_widget(card)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                self.show_move_dialog()
        return super().on_touch_down(touch)

    def show_move_dialog(self):
        lists = list(app.boards[app.current_board].keys())
        idx = lists.index(self.list_column.list_name)

        buttons = []
        if idx > 0:
            buttons.append(MDFlatButton(text="← Назад", on_release=lambda x: self.move_to(lists[idx - 1])))
        if idx < len(lists) - 1:
            buttons.append(MDFlatButton(text="Вперёд →", on_release=lambda x: self.move_to(lists[idx + 1])))

        buttons.append(MDFlatButton(text="Отмена", on_release=lambda x: self.move_dialog.dismiss()))

        self.move_dialog = MDDialog(
            title="Переместить карточку",
            text=f"«{self.card_text}»",
            buttons=buttons
        )
        self.move_dialog.open()

    def move_to(self, target_list_name):
        app.move_card(self.list_column.list_name, target_list_name, self.card_text)
        self.move_dialog.dismiss()



class ListColumn(MDCard):
    def __init__(self, title, board_name, **kwargs):
        super().__init__(**kwargs)
        self.board_name = board_name
        self.list_name = title
        self.orientation = "vertical"
        self.size_hint = (None, None)
        self.width = dp(240)
        self.height = dp(460)
        self.padding = dp(10)
        self.spacing = dp(10)
        self.radius = [15, 15, 15, 15]
        self.md_bg_color = [1, 1, 1, 1]
        self.elevation = 4

        self.add_widget(
            MDLabel(text=title, halign="center", bold=True, font_style="H6", size_hint_y=None, height=dp(40)))

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
        card = DraggableCard(text=text, list_column=self)
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

    def remove_card(self, board, list_name, card_text):
        if board in self.boards and list_name in self.boards[board]:
            if card_text in self.boards[board][list_name]:
                self.boards[board][list_name].remove(card_text)
                self.save_data()

    def remove_card_ui(self, card, list_column):
        list_column.card_container.remove_widget(card)
        self.remove_card(self.current_board, list_column.list_name, card.card_text)

    def move_card(self, from_list, to_list, card_text):
        if from_list == to_list:
            return

        self.remove_card(self.current_board, from_list, card_text)
        self.save_card(self.current_board, to_list, card_text)

        from_column = None
        to_column = None
        for column in self.screen.ids.list_container.children:
            if hasattr(column, 'list_name'):
                if column.list_name == from_list:
                    from_column = column
                elif column.list_name == to_list:
                    to_column = column

        if from_column and to_column:
            for card in from_column.card_container.children[:]:
                if isinstance(card, DraggableCard) and card.card_text == card_text:
                    from_column.card_container.remove_widget(card)
                    card.list_column = to_column
                    to_column.card_container.add_widget(card)
                    break

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

    def scroll_to_column(self, list_name):
        for column in self.screen.ids.list_container.children:
            if hasattr(column, 'list_name') and column.list_name == list_name:
                scroll_view = self.screen.ids.scroll_view
                scroll_x = column.x / max(1, self.screen.ids.list_container.width - scroll_view.width)
                scroll_view.scroll_x = max(0.0, min(scroll_x, 1.0))
                break


if __name__ == '__main__':
    GoalPlan().run()
