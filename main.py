import flet as ft
import sqlite3
import requests
from datetime import datetime

FUEL_COEFFICIENT = 0.45

def init_db():
    conn = sqlite3.connect("barbarg_bandar.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS drivers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    national_code TEXT,
                    plate TEXT,
                    driver_exp TEXT,
                    vehicle_exp TEXT,
                    total_km INTEGER DEFAULT 0
                )''')
    conn.commit()
    conn.close()

def get_drivers():
    conn = sqlite3.connect("barbarg_bandar.db")
    c = conn.cursor()
    c.execute("SELECT id, name, national_code, plate, driver_exp, vehicle_exp, total_km FROM drivers")
    rows = c.fetchall()
    conn.close()
    return rows

def add_driver_to_db(name, n_code, plate, d_exp, v_exp, km):
    conn = sqlite3.connect("barbarg_bandar.db")
    c = conn.cursor()
    c.execute("INSERT INTO drivers (name, national_code, plate, driver_exp, vehicle_exp, total_km) VALUES (?, ?, ?, ?, ?, ?)",
              (name, n_code, plate, d_exp, v_exp, int(km)))
    conn.commit()
    conn.close()

def update_km_db(driver_id, added_km):
    conn = sqlite3.connect("barbarg_bandar.db")
    c = conn.cursor()
    c.execute("UPDATE drivers SET total_km = total_km + ? WHERE id = ?", (int(added_km), driver_id))
    conn.commit()
    conn.close()

def main(page: ft.Page):
    init_db()
    page.title = "سناتور پلاس - باربرگ بندر"
    page.rtl = True
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.scroll = ft.ScrollMode.AUTO

    drivers_list_column = ft.Column(spacing=10)

    def show_msg(text, color=ft.colors.GREEN_700):
        page.snack_bar = ft.SnackBar(ft.Text(text, color=ft.colors.WHITE), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def register_barbarg_utcms(driver_id, name, plate, km_input):
        if not km_input.value.isdigit() or int(km_input.value) <= 0:
            show_msg("لطفاً کیلومتر پیمایش را به درستی وارد کنید!", ft.colors.RED_700)
            return
        
        km = int(km_input.value)
        update_km_db(driver_id, km)
        added_fuel = round(km * FUEL_COEFFICIENT, 1)
        show_msg(f"باربرگ {name} ثبت شد! (+{km} کیلومتر | +{added_fuel} لیتر سوخت)")
        load_drivers_ui()

    def build_driver_card(row):
        d_id, name, n_code, plate, d_exp, v_exp, total_km = row
        estimated_fuel = int(total_km * FUEL_COEFFICIENT)
        km_field = ft.TextField(label="کیلومتر جدید", value="25", width=130, height=45, text_size=13, keyboard_type=ft.KeyboardType.NUMBER)

        return ft.Card(
            content=ft.Container(
                padding=12,
                content=ft.Column([
                    ft.Row([
                        ft.Row([
                            ft.Icon(ft.icons.LOCAL_SHIPPING, color=ft.colors.CYAN_300),
                            ft.Text(f"{name}", size=16, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            bgcolor=ft.colors.BLUE_GREY_800,
                            border_radius=6,
                            content=ft.Text(f"پلاک: {plate}", size=13, color=ft.colors.YELLOW_400, weight=ft.FontWeight.BOLD)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Divider(height=8),
                    
                    ft.Row([
                        ft.Text(f"اعتبار اشتغال: {d_exp}", size=12, color=ft.colors.GREEN_300),
                        ft.Text(f"اعتبار فعالیت: {v_exp}", size=12, color=ft.colors.GREEN_300),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    ft.Container(
                        padding=8,
                        bgcolor=ft.colors.BLACK26,
                        border_radius=8,
                        content=ft.Row([
                            ft.Row([
                                ft.Icon(ft.icons.SPEED, color=ft.colors.BLUE_400, size=18),
                                ft.Text(f"پیمایش: {total_km} Km", size=13, weight=ft.FontWeight.BOLD),
                            ]),
                            ft.Row([
                                ft.Icon(ft.icons.LOCAL_GAS_STATION, color=ft.colors.ORANGE_400, size=18),
                                ft.Text(f"سوخت: {estimated_fuel} لیتر", size=13, color=ft.colors.ORANGE_300, weight=ft.FontWeight.BOLD),
                            ]),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    ),

                    ft.Row([
                        km_field,
                        ft.ElevatedButton(
                            "ثبت در utcms",
                            icon=ft.icons.SEND_AND_ARCHIVE,
                            bgcolor=ft.colors.GREEN_700,
                            color=ft.colors.WHITE,
                            on_click=lambda e: register_barbarg_utcms(d_id, name, plate, km_field)
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ])
            )
        )

    def load_drivers_ui():
        drivers_list_column.controls.clear()
        rows = get_drivers()
        if not rows:
            add_driver_to_db("ناخدا احمد بندری", "3391234567", "۸۴ ع ۳۶۵", "1405/09/15", "1405/11/20", 1200)
            rows = get_drivers()
            
        for r in rows:
            drivers_list_column.controls.append(build_driver_card(r))
        page.update()

    name_in = ft.TextField(label="نام و نام خانوادگی راننده")
    ncode_in = ft.TextField(label="کد ملی راننده", keyboard_type=ft.KeyboardType.NUMBER)
    plate_in = ft.TextField(label="شماره پلاک (مثال: ۸۴ ع ۳۶۵)")
    d_exp_in = ft.TextField(label="تاریخ انقضای پروانه اشتغال (از utcms)", value="1405/12/29")
    v_exp_in = ft.TextField(label="تاریخ انقضای پروانه فعالیت خودرو", value="1405/10/15")
    km_init_in = ft.TextField(label="کیلومتر پیمایش فعلی در ماه جاری", value="0", keyboard_type=ft.KeyboardType.NUMBER)

    def save_new_driver(e):
        if name_in.value and plate_in.value:
            add_driver_to_db(name_in.value, ncode_in.value, plate_in.value, d_exp_in.value, v_exp_in.value, km_init_in.value or "0")
            dlg_modal.open = False
            name_in.value = ""
            plate_in.value = ""
            load_drivers_ui()
            show_msg("راننده جدید اضافه شد!")

    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("افزودن ناوگان جدید"),
        content=ft.Column([name_in, ncode_in, plate_in, d_exp_in, v_exp_in, km_init_in], tight=True, scroll=ft.ScrollMode.AUTO),
        actions=[
            ft.TextButton("ثبت و ذخیره", on_click=save_new_driver),
            ft.TextButton("انصراف", on_click=lambda e: setattr(dlg_modal, 'open', False) or page.update()),
        ],
    )

    def open_add_dialog(e):
        page.dialog = dlg_modal
        dlg_modal.open = True
        page.update()

    page.appbar = ft.AppBar(
        title=ft.Text("سامانه هوشمند باربرگ و سوخت"),
        bgcolor=ft.colors.BLUE_GREY_900,
        actions=[
            ft.IconButton(ft.icons.REFRESH, on_click=lambda e: show_msg("استعلام اعتبار پروانه‌ها از پنل utcms بروزرسانی شد."))
        ]
    )

    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.icons.PERSON_ADD,
        text="افزودن راننده",
        bgcolor=ft.colors.BLUE_600,
        on_click=open_add_dialog
    )

    page.add(
        ft.Container(
            padding=12,
            bgcolor=ft.colors.INDIGO_900,
            border_radius=10,
            content=ft.Row([
                ft.Column([
                    ft.Text("متصل به هسته utcms.ir", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_300),
                    ft.Text(f"ضریب محاسبه سوخت: {FUEL_COEFFICIENT} لیتر بر کیلومتر", size=11, color=ft.colors.WHITE70),
                ]),
                ft.ElevatedButton("استارت صف", icon=ft.icons.PLAY_CIRCLE_FILL, bgcolor=ft.colors.AMBER_700, color=ft.colors.WHITE)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ),
        ft.Divider(height=10),
        drivers_list_column
    )

    load_drivers_ui()

ft.app(target=main)
