"""
This code creates a basic wardrobe tracker app using the Kivy package. Currently functionality includes the ability
to add and remove items and updating the database. Planned upgrades include adding photos and item count.
"""
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivymd.uix.dialog import MDDialog
from kivy.uix.camera import Camera
import sqlite3 as sql
import time
import os

kv = ('''
<AppCamera>:
    resolution: (640, 480)
    size_hint: None,None
    size: dp(500),dp(500)
    index: 0
    canvas.before:
        PushMatrix
        Rotate:
            angle: -90
            origin: self.center
    canvas.after:
        PopMatrix
    allow_stretch: True
    play: True
    

WindowManager:
    MainWindow:
        name: "Main"
        id: main
    AddWindow:
        name: "Add"
        id: add
    ImageWindow:
        name: "Image"
        id: image
    ConfirmWindow:
        name: "Confirm"
        id: confirm
        
        
<MainWindow>:
    MDToolbar:
        title: "Wardrobe Tracker"
        size_hint:1,0.1
        pos_hint:{'top':1}
        right_action_items:
            [('filter', lambda x: root.filter_category()),
            ('plus', lambda x: root.manager.switch_to(root.manager.ids.add, direction = 'left'))]
    MDToolbar:
        title: app.title
        type: "bottom"
        mode: "free-end"
        icon: ""
    ScrollView:
        pos_hint:{'top':0.9}
        size_hint:1,0.79
        do_scroll_x: False
        GridLayout:
            id: container
            cols: 2
            spacing: 0,50
            mipmap: True
            row_default_height:
                (self.width - self.cols*self.spacing[0])/self.cols
            row_force_default: True
            size_hint_y: None
            height: self.minimum_height
            
            
<AddWindow>:
    name: "Add"
    MDToolbar:
        size_hint:1,0.1
        pos_hint:{'top':1}
        left_action_items:
            [('arrow-left', lambda x: root.manager.switch_to(root.manager.ids.main, direction = 'right'))]
        right_action_items:
            [('camera', lambda x: root.manager.switch_to(root.manager.ids.image, direction = 'left'))]
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
        
        
<ImageWindow>:
    camera: camera.__self__
    on_pre_enter: cam_toolbar.remove_notch()
    
    AppCamera:
        id: camera
        center: self.size and root.center
        
    MDToolbar:
        size_hint:1,0.1
        pos_hint:{'top':1}
        left_action_items:
            [('arrow-left', lambda x: root.manager.switch_to(root.manager.ids.add, direction = 'right'))]
            
    MDToolbar:
        id: cam_toolbar
        icon: "circle"
        type: "bottom"
        on_md_bg_color: (0.4, 0.4, 0.4, 1)
        
    MDFloatingActionButton:
        elevation_normal: 8
        icon: ''
        pos_hint: {"top": 0.08, "center_x": 0.5}
        size_hint: None,None
        size: dp(50),dp(50)
        on_press: root.capture()
        md_bg_color: (0, 0, 0, 1)
        
            
<ConfirmWindow>:
    on_pre_enter: display_image.source = root.manager.ids.image.image_id
    Image:
        id: display_image
        pos_hint:{'top': 1}
    MDToolbar:
        size_hint:1,0.1
        pos_hint:{'top':1}
        left_action_items:
            [('arrow-left', lambda x: root.manager.switch_to(root.manager.ids.image, direction = 'right'))]
        right_action_items:
            [('check', lambda x: root.manager.switch_to(root.manager.ids.add, direction = 'right'))]
        
''')

# need to -1 count when removing items too. camera wrong way around (rot left 90 degrees), does not track image
# (need android photo folder), no option to switch to front camera


class WindowManager(ScreenManager):
    ScreenManager.category = {"Tops": 0, "Bottoms": 1, "Dresses": 2, "Jackets": 3, "Accessories": 4}
    ScreenManager.current_category = "All"


class MainWindow(Screen):
    # Popup to filter item category
    def filter_category(self):

        self.manager.ids.image.camera.play = False
        self.manager.ids.image.camera.index = -1
        #self.manager.ids.image.remove_widget(self.manager.ids.image.ids.camera)

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

            # cam = AppCamera()
            # cam.center = (cam.size and self.manager.ids.image.center)
            # self.manager.ids.image.add_widget(cam)
            self.manager.ids.image.ids.camera.play = True
            self.manager.ids.image.ids.camera.index = 0

        con.commit()
        con.close()


class ImageWindow(Screen):
    #camera = ObjectProperty(None)

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
        self.camera.play = True
        self.camera.index = 0


class AppCamera(Camera):
    pass


class ConfirmWindow(Screen):
    pass


class MDApp(MDApp):

    def __init__(self, **kwargs):
        print("init")
        super().__init__(**kwargs)
        con = sql.connect("demo.db")
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS Wardrobe(item TEXT NOT NULL UNIQUE, category TEXT, image TEXT,
        desc TEXT)""")
        cur.execute("""SELECT COUNT(*) FROM Wardrobe ORDER BY category""")
        self.title = "Item Count: " + str(cur.fetchall()[0][0])
        con.commit()
        con.close()
        self.screen = Builder.load_string(kv)

    def build(self):
        print("build")
        return self.screen

    def on_start(self):
        print("on_start")
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
        print("on pause")
        self.root.ids.image.ids.camera.play = False
        self.root.ids.image.camera.index = -1
        #self.root.ids.image.remove_widget(self.root.ids.image.ids.camera)
        return True

    def on_resume(self):
        print("on resume")
        #cam = AppCamera(index = 0)
        #cam.center = (cam.size and self.root.ids.image.center)
        #self.root.ids.image.add_widget(cam)
        #self.root.ids.image.ids.camera.play = True
        #self.root.ids.image.ids.camera.index = 0

    def on_stop(self):
        print("on_stop")


if __name__ == "__main__":
    # run app
    MDApp().run()