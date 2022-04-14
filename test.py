from math import cos, pi, sin
import dearpygui.dearpygui as dpg

dpg.create_context()
dpg.create_viewport(title='Custom Title', width=411, height=200)  # width=600, height=200

with dpg.window(label="Label", width=800, height=600):
    pass


def on_key_la(sender, app_data):
    if dpg.is_key_down(dpg.mvKey_A):
        print("Ctrl + A")

def on_key_h(sender, app_data):
    print('H pressed!')
    print(sender, app_data)


with dpg.handler_registry():
    dpg.add_key_press_handler(dpg.mvKey_Control, callback=on_key_la)
    dpg.add_key_press_handler(dpg.mvKey_H, callback=on_key_h)

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()