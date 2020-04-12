"""
This code creates a basic wardrobe tracker app using the Kivy package. Currently functionality includes the ability
to add and remove items and updating the database. Planned upgrades include use of front category + removing items.
"""
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivymd.uix.dialog import MDDialog
import sqlite3 as sql
import time
import os


class WindowManager(ScreenManager):
    ScreenManager.category = {"Tops": 0, "Bottoms": 1, "Dresses": 2, "Jackets": 3, "Accessories": 4}
    ScreenManager.current_category = "All"


class MainWindow(Screen):
    # Popup to filter item category
    def filter_category(self):

        # self.manager.ids.image.ids.camera.index = -1

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
                Image(source=row[2])
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
            wardrobe_category = self.manager.category[wardrobe_category]
            image_source = self.manager.ids.image.image_id
            # Add to screen if filter matches input category
            if wardrobe_category == self.manager.current_category or self.manager.current_category == "All":
                self.manager.ids.main.ids.container.add_widget(Image(source=image_source))

                app = MDApp.get_running_app()
                item_count = int(app.title.split(": ")[1]) + 1
                app.title = "Item Count: " + str(item_count)

            cur.execute("""INSERT INTO Wardrobe (item, image, category) VALUES (?,?,?)""",
                        (wardrobe_item, image_source, wardrobe_category))

            self.ids.wardrobe_item.text = ''
            self.manager.switch_to(self.manager.ids.main, direction='right')

        # If item exists, display error popup
        else:
            dup_dialog = MDDialog(title="Existing Item", text="This item already exists", text_button_ok="Go Back",
                                  size_hint=[0.9, 0.5])
            dup_dialog.open()

            #self.manager.ids.image.ids.camera.index = 0

        con.commit()
        con.close()


class ImageWindow(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_id = ''
        self._request_android_permissions()

    @staticmethod
    def is_android():
        return platform == 'android'

    def _request_android_permissions(self):
        """
        Requests CAMERA permission on Android.
        """
        if not self.is_android():
            return
        from android.permissions import request_permission, Permission
        request_permission(Permission.CAMERA)

    def capture(self):
        '''
        Function to capture the images and give them the names
        according to their captured time and date.
        '''
        camera = self.ids.camera
        time_str = time.strftime("%Y%m%d_%H%M%S")
        self.image_id = "IMG_{}.png".format(time_str)

        root_dir = os.path.dirname(os.path.abspath(__file__))
        self.image_id = os.path.join(root_dir, self.image_id)
        camera.export_to_png(self.image_id)
        self.manager.switch_to(self.manager.ids.confirm, direction = 'left')

    def on_pre_enter(self, *args):
        self.ids.cam_toolbar.remove_notch()
        self.ids.camera.play = True
        #self.ids.camera.index = 0


class ConfirmWindow(Screen):
    pass


class MDApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        con = sql.connect("demo.db")
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS Wardrobe(item TEXT NOT NULL UNIQUE, category TEXT, image TEXT,
        desc TEXT)""")
        cur.execute("""SELECT COUNT(*) FROM Wardrobe ORDER BY category""")
        self.title = "Item Count: " + str(cur.fetchall()[0][0])
        con.commit()
        con.close()
        self.screen = Builder.load_file("my.kv")

    def build(self):
        return self.screen

    def on_start(self):
        con = sql.connect("demo.db")
        cur = con.cursor()
        cur.execute("""SELECT * FROM Wardrobe ORDER BY category""")
        rows = cur.fetchall()
        con.close()

        # Add item to scroll view
        for row in rows:
            self.root.ids.main.ids.container.add_widget(
                Image(source=row[2])
            )

    def on_pause(self):
        self.root.ids.image.ids.camera.play = False
        return True


if __name__ == "__main__":
    # run app
    MDApp().run()