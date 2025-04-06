import arcade
from arcade.gui import UIManager, UIAnchorLayout, UIFlatButton, UIGridLayout, UILabel


class MainMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.ui_manager = UIManager()
        self.setup()

    def setup(self):
        self.ui_manager.clear()

        grid_layout = UIGridLayout(column_count=1, row_count=4,
                                   horizontal_spacing=20, vertical_spacing=20)

        # Heading
        heading = UILabel(
            text="Tactical Tanks",
            width=450,
            height=60,
            font_size=32,
            font_name="Kenney Future",
            text_color=arcade.color.WHITE
        )

        # Buttons
        self.create_server_btn = UIFlatButton(text="Create Game", width=250)
        self.server_list_btn = UIFlatButton(text="Join Game", width=250)


        grid_layout.add(heading, row=0, column=0)
        grid_layout.add(self.create_server_btn, row=1, column=0)
        grid_layout.add(self.server_list_btn, row=2, column=0)


        anchor = UIAnchorLayout(children=[grid_layout])
        self.ui_manager.add(anchor)

        # Connect buttons
        self.create_server_btn.on_click = self.on_create_server
        self.server_list_btn.on_click = self.on_server_list


    def on_create_server(self, event):
        print("Create Server clicked")
        # Create and show new view
        create_view = CreateServerView(self)
        self.window.show_view(create_view)

    def on_server_list(self, event):
        print("Server List clicked")
        # Create and show new view
        list_view = ServerListView(self)
        self.window.show_view(list_view)



    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        try:
            arcade.load_font("kenney_future.ttf")
        except:
            print("Note: kenney_future.ttf not found - using default font")

    def on_draw(self):
        self.clear()
        self.ui_manager.draw()


class CreateServerView(arcade.View):
    def __init__(self, previous_view):
        super().__init__()
        self.previous_view = previous_view
        self.ui_manager = UIManager()
        self.setup()

    def setup(self):
        self.ui_manager.clear()

        grid = UIGridLayout(column_count=1, row_count=2, vertical_spacing=20)

        # Back button
        back_btn = UIFlatButton(text="Back", width=200)
        back_btn.on_click = self.on_back

        grid.add(back_btn, row=0, column=0)

        anchor = UIAnchorLayout(children=[grid])
        self.ui_manager.add(anchor)

    def on_back(self, event):
        self.window.show_view(self.previous_view)

    def on_draw(self):
        self.clear()
        arcade.draw_text(
            "Create Server Screen",
            self.window.width / 2,
            self.window.height / 2,
            arcade.color.WHITE,
            font_size=30,
            anchor_x="center"
        )
        self.ui_manager.draw()


class ServerListView(arcade.View):
    def __init__(self, previous_view):
        super().__init__()
        self.previous_view = previous_view
        self.ui_manager = UIManager()
        self.setup()

    def setup(self):
        self.ui_manager.clear()

        grid = UIGridLayout(column_count=1, row_count=2, vertical_spacing=20)

        back_btn = UIFlatButton(text="Back", width=200)
        back_btn.on_click = self.on_back

        grid.add(back_btn, row=0, column=0)

        anchor = UIAnchorLayout(children=[grid])
        self.ui_manager.add(anchor)

    def on_back(self, event):
        self.window.show_view(self.previous_view)

    def on_draw(self):
        self.clear()
        arcade.draw_text(
            "Server List Screen",
            self.window.width / 2,
            self.window.height / 2,
            arcade.color.WHITE,
            font_size=30,
            anchor_x="center"
        )
        self.ui_manager.draw()


def main():
    window = arcade.Window(800, 600, "Tactical Tanks", resizable=False)
    window.set_vsync(True)
    menu_view = MainMenuView()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()
