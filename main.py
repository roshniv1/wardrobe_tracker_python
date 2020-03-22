"""
This code creates a basic wardrobe tracker app using the Kivy package. Currently functionality includes the ability
to add and remove items and updating the database. Planned upgrades include adding photos and item count.
"""

from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.dialog import MDDialog
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.factory import Factory
from kivymd.uix.list import OneLineAvatarIconListItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
import sqlite3 as sql

kv = '''   
#:import MDDropdownMenu kivymd.uix.menu.MDDropdownMenu


<ListItemWithIcon@OneLineAvatarIconListItem>:

    IconRightWidget:
        icon: "minus"
        on_release:
            root.confirm_dialog()
   
   
WindowManager:

    MainWindow:
        id: main
        name: "Main"
        
    AddWindow:
        id: add
    
    
<MainWindow>:
    name : "Main"
    
    MDToolbar:
        title: "Wardrobe Tracker"
        size_hint:1,0.1
        pos_hint:{'top':1}
        right_action_items: [['filter', lambda x: root.filter_category()], \
        ['plus', lambda x: root.manager.switch_to(root.manager.ids.add, direction = 'left')]]
    
    MDToolbar:
        title: app.title
        type: "bottom"
        mode: "free-end"
        icon: ""

    ScrollView:
        pos_hint:{'top':0.9}
        size_hint:1,0.79
        MDList:
            id: container     
            
            
<AddWindow>:

    on_pre_enter: wardrobe_item.text = ''
    name: "Add"
    
    MDToolbar:
        size_hint:1,0.1
        pos_hint:{'top':1}
        left_action_items: [('arrow-left', lambda x: root.manager.switch_to(root.manager.ids.main, direction = 'right'))]
        
    MDTextField:
        id: wardrobe_item
        pos_hint: {"top": 0.85, "center_x": 0.5}
        size_hint: 0.9,None
        helper_text: "Name your wardrobe item and select category"
        helper_text_mode: "persistent"
        
    MDDropDownItem:
        id: wardrobe_category
        pos_hint: {"top":0.5, "center_x": 0.5}
        items: root.manager.category
        dropdown_bg: [1, 1, 1, 1]
        dropdown_width_mult : 4  
        
    Button:
        text: "Add"
        pos_hint: {"top":0.1}
        size_hint: 1,0.1
        on_press: root.add_item(wardrobe_item.text, wardrobe_category.current_item)
'''


class WindowManager(ScreenManager):
    ScreenManager.category = {"Tops": 0, "Bottoms": 1, "Dresses": 2, "Jackets": 3, "Accessories": 4}
    ScreenManager.current_category = "All"


class MainWindow(Screen):
    # Popup to filter item category
    def filter_category(self):
        # List of categories to display as buttons
        wardrobe_category = self.manager.category

        # Buttons shown in popup
        box = BoxLayout(orientation='vertical')
        popup = Popup(title='Category', content=box, size_hint=(0.7, 0.5), separator_color=(0.4, 0.4, 0.4, 1))

        box.add_widget(Button(text="All", background_normal='', color=(0, 0, 0, 1),
                              on_press=lambda button: self.filter_view(button.text),
                              on_release=lambda x: popup.dismiss()))

        for key, value in enumerate(wardrobe_category):
            box.add_widget(Button(text=value, background_normal='', color=(0, 0, 0, 1),
                                  on_press=lambda button: self.filter_view(button.text),
                                  on_release=lambda x: popup.dismiss()))
        popup.open()

    def filter_view(self, wardrobe_category):
        # Filter items, clear widgets and select by category
        self.ids.container.clear_widgets()

        con = sql.connect("demo.db")
        cur = con.cursor()

        if wardrobe_category == "All":
            cur.execute("""SELECT * FROM Wardrobe""")
        else:
            wardrobe_category = self.manager.category[wardrobe_category]
            self.manager.current_category = wardrobe_category
            cur.execute("""SELECT * FROM Wardrobe WHERE category = (?)""", [wardrobe_category])

        rows = cur.fetchall()

        # Add item to scroll view
        for row in rows:
            self.ids.container.add_widget(
                Factory.ListItemWithIcon(text=row[0])
            )

        if wardrobe_category == "All":
            cur.execute("""SELECT COUNT(*) FROM Wardrobe""")
        else:
            cur.execute("""SELECT COUNT(*) FROM Wardrobe WHERE category = (?)""", [wardrobe_category])

        app = MDApp.get_running_app()
        app.title = "Item Count: " + str(cur.fetchall()[0][0])

        con.close()


class AddWindow(Screen):

    def add_item(self, wardrobe_item, wardrobe_category):
        # Add wardrobe items to scroll view and database

        con = sql.connect("demo.db")
        cur = con.cursor()
        cur.execute("""SELECT * FROM Wardrobe WHERE item = (?)""", [wardrobe_item])

        # If item does not already exist, add item
        if cur.fetchone() is None:
            self.manager.ids.main.ids.container.add_widget(Factory.ListItemWithIcon(text=wardrobe_item))
            wardrobe_category = self.manager.category[wardrobe_category]
            cur.execute("""INSERT INTO Wardrobe (item, category) VALUES (?,?)""",
                        (wardrobe_item, wardrobe_category))

            if wardrobe_category == self.manager.current_category or self.manager.current_category  == "All":
                app = MDApp.get_running_app()
                item_count = int(app.title.split(": ")[1]) + 1
                app.title = "Item Count: " + str(item_count)

            self.manager.switch_to(self.parent.ids.main, direction='right')

        # If item exists, display error popup
        else:
            dup_dialog = MDDialog(title="Existing Item", text="This item already exists", text_button_ok="Go Back",
                                  size_hint=[0.9, 0.5])
            dup_dialog.open()

        con.commit()
        con.close()


class ListItemWithIcon(OneLineAvatarIconListItem):
    # Popup to confirm delete
    def confirm_dialog(self):
        confirm_dialog = MDDialog(title="Delete Confirmation", text="Are you sure you want to delete '" + self.text + "'?",
                                  events_callback=self.remove_item, text_button_ok="Delete",
                                  text_button_cancel="Cancel", size_hint=[0.9, 0.5])
        # Removed auto_dismiss=False
        confirm_dialog.open()

    # Remove item from widget and table
    def remove_item(self, selection_text, popup_widget):
        if selection_text == "Delete":
            con = sql.connect("demo.db")
            cur = con.cursor()
            cur.execute("""DELETE FROM Wardrobe WHERE item = (?)""", [self.text])
            con.commit()
            con.close()
            app = MDApp.get_running_app()
            app.root.ids.main.ids.container.remove_widget(self)


class MyMainApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        con = sql.connect("demo.db")
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS Wardrobe(item TEXT NOT NULL UNIQUE, category TEXT)""")
        cur.execute("""SELECT COUNT(*) FROM Wardrobe ORDER BY category""")
        self.title = "Item Count: " + str(cur.fetchall()[0][0])
        con.commit()
        con.close()
        self.screen = self.screen = Builder.load_string(kv)

    def build(self):
        return self.screen

    def on_start(self):
        con = sql.connect("demo.db")
        cur = con.cursor()
        cur.execute("""SELECT * FROM Wardrobe ORDER BY category""")
        rows = cur.fetchall()

        # Add item to scroll view
        for row in rows:
            self.root.ids.main.ids.container.add_widget(
                Factory.ListItemWithIcon(text=row[0])
            )

        con.close()


if __name__ == "__main__":
    # run app
    MyMainApp().run()
