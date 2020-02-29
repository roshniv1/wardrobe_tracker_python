""" This code creates a basic wardrobe tracker app using the Kivy package. Currently functionality includes the ability
to add and remove items and updating the database. Planned upgrades include adding different wardrobe categories,
checking for duplicate items and adding photos.
"""

from kivy.uix.screenmanager import Screen
from kivymd.uix.dialog import MDDialog, MDInputDialog
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.factory import Factory
from kivymd.uix.list import OneLineAvatarIconListItem
import sqlite3 as sql

kv = '''   
<ListItemWithIcon@OneLineAvatarIconListItem>:
    IconRightWidget:
        icon: "minus"
        on_release:
            root.confirm_dialog()
                 
ViewWindow:
    name : "View"
    MDToolbar:
        size_hint:1,0.1
        pos_hint:{"top":1}
        title: "Wardrobe"
        right_action_items: [["plus", lambda x: root.input_dialog()]]
    ScrollView:
        pos_hint:{"top":0.9}
        size_hint:1,0.9
        MDList:
            id: container       
'''


class ListItemWithIcon(OneLineAvatarIconListItem):
    # Popup to confirm delete
    def confirm_dialog(self):
        # create instance
        print([self.text])
        my_dialog = MDDialog(title="Delete Confirmation", text="Are you sure you want to delete '" + self.text + "'?",
                             auto_dismiss=False, events_callback=self.remove_item, text_button_ok="Delete",
                             text_button_cancel="Cancel", size_hint=[0.5, 0.5])
        my_dialog.open()

    # Remove item from widget and table
    def remove_item(self, selection_text, popup_widget):
        if selection_text == "Delete":
            con = sql.connect("demo.db")
            cur = con.cursor()
            cur.execute("""DELETE FROM Wardrobe WHERE item = (?)""", [self.text])
            con.commit()
            con.close()
            app = MDApp.get_running_app()
            app.root.ids.container.remove_widget(self)


class ViewWindow(Screen):
    # Popup to add wardrobe item
    def input_dialog(self):
        my_dialog = MDInputDialog(title="Add Item", hint_text="Type new wardrobe item", text_button_ok="Add",
                                  events_callback=self.add_item, size_hint=[0.5, 0.5])
        my_dialog.open()

    # Adds item to widget and table
    def add_item(self, selection_text, popup_widget):
        self.ids.container.add_widget(Factory.ListItemWithIcon(text=popup_widget.text_field.text))
        con = sql.connect("demo.db")
        cur = con.cursor()
        cur.execute("""INSERT INTO Wardrobe (item) VALUES (?)""", [popup_widget.text_field.text])
        con.commit()
        con.close()


class MyMainApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen = Builder.load_string(kv)

    def build(self):
        return self.screen

    def on_start(self):
        con = sql.connect("demo.db")
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS Wardrobe(item text)""")
        cur.execute("""SELECT * FROM WARDROBE""")
        rows = cur.fetchall()

        # Add item to scrollview
        for row in rows:
            print(row[0])
            self.screen.ids.container.add_widget(
                Factory.ListItemWithIcon(text=row[0])
            )
        con.commit()
        con.close()


if __name__ == "__main__":
    # run app
    MyMainApp().run()
