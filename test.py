import dearpygui.dearpygui as dpg

dpg.create_context()


# def apply_text_multiplier(sender, data):
#     font_multiplier = dpg.get_value("Font Size Multiplier")
#     dpg.set_global_font_scale(font_multiplier)


# def apply_theme(sender, data):
#     theme = dpg.get_value("Themes")
#     dpg.bind_theme(theme)

# with dpg.window(width=600, height=400):
#     dpg.add_combo(("Dark", "Light", "Classic", "Dark 2", "Grey", "Dark Grey", "Cherry", "Purple", "Gold", "Red"),\
#      label="Themes", default_value="Dark", callback=apply_theme)

#     dpg.add_slider_float(tag="Font Size Multiplier", default_value=1.0, min_value=0.0, max_value=2.0,
#                  callback=apply_text_multiplier)

def update_list(sender, app_data, user_data):
    print(id(num_list)) 
    user_data.append(5)
    print(id(num_list)) 
    

def update_text(sender, app_data, user_data):
    print('udpate_text', id(user_data))
    dpg.delete_item('subg')
    with dpg.group(tag='subg', parent='g'):
        for n in user_data:
            dpg.add_text(default_value=n)

with dpg.window(width=600, height=400):
    num_list = [1,2,3,4]
    print(id(num_list))
    dpg.add_button(label='Update List', callback=update_list, user_data=num_list)
    dpg.add_button(label='Update Text', callback=update_text, user_data=num_list)
    with dpg.group(tag='g'):
        with dpg.group(tag='subg'):
            for n in num_list:
                dpg.add_text(default_value=n)

dpg.create_viewport(title='Test Theme')
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()