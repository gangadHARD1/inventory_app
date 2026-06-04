import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inventory_app import db

db.init_db()  # uses the same config/path as the app

units = [
    "BAG", "BOTTLE", "BOX", "Cub. metre", "CUB.FT.", "EACH",
    "Feet", "inch", "KG", "Kilos (kg)", "Liter (L)", "Litres",
    "METER", "NOS", "PCS", "Packet", "Pair", "ROLL", "SET", "bundle"
]
item_groups = [
    "Welding",
    "cutting",
    "factory expenses",
    "Maintenance of plant",
    "Grinding",
    "painting",
    "Electrical",
    "drilling",
    "Surface Cleaning",
    "power",
    "Other",
    "packing",
    "inspection",
    "fitting",
    "Printing and Stationary",
    "Office Expenses",
    "Capital",
    "Despatch"
]

item_class_map = {
    'Capital': ['Capital', 'Surface Cleaning'],
    'Despatch': ['Despatch'],
    'Fitting Consumable': ['factory expenses', 'fitting'],
    'Other Items': ['Office Expenses', 'Other', 'Surface Cleaning'],
    'Welding Accessories': ['Welding'],
    'cutting': ['cutting', 'factory expenses'],
    'cutting acessories': ['Surface Cleaning', 'cutting'],
    'drilling consumable': ['Grinding', 'drilling', 'inspection'],
    'electrical consumable': ['Electrical', 'Grinding'],
    'factory expenses': ['Office Expenses', 'factory expenses'],
    'fitting': ['Electrical', 'Office Expenses', 'fitting'],
    'grinding consumable': ['Electrical', 'Grinding', 'drilling'],
    'inspection': ['drilling', 'inspection'],
    'maintenance spare': ['Electrical', 'Maintenance of plant', 'drilling', 'factory expenses'],
    'packing': ['fitting', 'packing'],
    'paint consumable': ['Maintenance of plant', 'Printing and Stationary', 'painting'],
    'power': ['Electrical', 'Other', 'power'],
    'stationary & printing consumables': [
        'Office Expenses',
        'Printing and Stationary',
        'Welding',
        'factory expenses',
        'painting'
    ],
    'surface preparation consumable': ['Surface Cleaning', 'packing', 'painting'],
    'welding consumable': ['Welding']
}
suppliers = [
    "A.B.Enterprises",
    "ABM Marketing",
    "Asian Paints PPG Pvt Ltd",
    "Ask Indane NDNE Retailer",
    "Associated Suppliers And Kontractors",
    "Atul Cryogenic Gases",
    "Balaji Traders",
    "Bulwark Maintenance Engineers",
    "Computech Associates",
    "Essjay Traders",
    "Friends Agencies",
    "Jain industrial Traders",
    "Maa Shanti Enterprises",
    "Mahaveer Engineering & Trading Co.",
    "Maheshwari Enterprises",
    "Modi Hitech India Ltd.",
    "Nahata Metals & Air Products P Ltd.",
    "New Shankar Glass & Plywood",
    "OmShri Sai Ram Industries",
    "Praxair India Pvt. Ltd.",
    "Reliance Corporation",
    "Siddharth Enterprises",
    "Synorganic Paints Pvt. Ltd.",
    "Technoweld Appliances & Services",
    "UNNATI ENTERPRISES",
    "VFL GROUP INDIA",
    "Welmet Technologies Pvt.Ltd"
]
work_orders = [
    "CFPPL/WO/2022-23-00012",
    "CFPPL/WO/2025-26-00016",
    "CFPPL/WO/2025-26-00014",
    "CFPPL/WO/2024-25-00004",
    "CFPPL/WO/2022-23-00007",
    "CFPPL/WO/2025-26-00015"
]
customers = [
    "COREFAB/INTERNAL",
    "Larsen & Toubro Limited,Nabina",
    "Vijaya Infra project Pvt Ltd.",
    "Thyssenkrupp Industries",
    "BGR GHATAMPUR/ 40MT",
    "Vijaya Infra Projects Pvt 18mt"
]

column_map = {
    1: "Item Code",
    2: "Item",
    3: "Measurement Unit",
    4: "Grade",
    5: "Supplier",
    6: "In Hand",
    7: "Over Issued",
    8: "Unit Price",
    9: "Section Size",
    10: "Length",
    11: "Scrap Length",
    12: "Width",
    13: "Weight In Tonne",
    14: "Available Weight",
    15: "Required Weight",
    16: "Surface Area",
    17: "Cross Section Area",
    18: "Depth",
    19: "Density",
    20: "Item Group",
    21: "Section Type",
    22: "Item Class",
    23: "Remark",
    24: "Thickness",
    25: "Height",
    26: "Section Code",
    27: "Weight",
    28: "Area",
    29: "PO Receipt Date",
    30: "Location",
    31: "Last Date",
    32: "Last Update By"
}
for unit in units:
    with db.get_session() as s:
        exists = s.query(db.MeasurementUnit).filter_by(name=unit).first()
        if not exists:
            s.add(db.MeasurementUnit(name=unit))
            s.commit()
            print(f"Added: {unit}")
        else:
            print(f"Skipped (exists): {unit}")

for itemgrp in item_groups:
    with db.get_session() as s:
        exists = s.query(db.ItemGroup).filter_by(name=itemgrp).first()
        if not exists:
            s.add(db.ItemGroup(name=itemgrp))
            s.commit()
            print(f"Added: {itemgrp}")
        else:
            print(f"Skipped (exists): {itemgrp}")

for item_class, groups in item_class_map.items():
    with db.get_session() as s:

        exists = s.query(db.ItemClass).filter_by(name=item_class).first()

        if not exists:

            group_objects = (
                s.query(db.ItemGroup)
                .filter(db.ItemGroup.name.in_(groups))
                .all()
            )

            s.add(
                db.ItemClass(
                    name=item_class,
                    item_groups=group_objects
                )
            )

            s.commit()
            print(f"Added: {item_class}")

        else:
            print(f"Skipped (exists): {item_class}")


for suppl in suppliers:
    with db.get_session() as s:
        exists = s.query(db.Supplier).filter_by(name=suppl).first()
        if not exists:
            s.add(db.Supplier(name=suppl))
            s.commit()
            print(f"Added: {suppl}")
        else:
            print(f"Skipped (exists): {suppl}")

for wo in work_orders:
    with db.get_session() as s:
        exists = s.query(db.WorkOrder).filter_by(name=wo).first()
        if not exists:
            s.add(db.WorkOrder(name=wo))
            s.commit()
            print(f"Added: {wo}")
        else:
            print(f"Skipped (exists): {wo}")

for cus in customers:
    with db.get_session() as s:
        exists = s.query(db.Customer).filter_by(name=cus).first()
        if not exists:
            s.add(db.Customer(name=cus))
            s.commit()
            print(f"Added: {cus}")
        else:
            print(f"Skipped (exists): {cus}")

import pandas as pd

EXCEL_FILE = "Inventory_Record.xls"


def clean_value(v):

    if pd.isna(v):
        return None

    return str(v).strip()


def clean_float(v):

    if pd.isna(v):
        return None

    try:
        return float(v)
    except:
        return None


df = pd.read_html(EXCEL_FILE)[0]

df = df.iloc[:, :33]

df.columns = [str(col).strip() for col in df.columns]
i=0
for _, row in df.iterrows():
    print("here",row,"here222",row.get(1),type(row))
    i+=1
    if i==2:
        break

    item_code = clean_value(row.get(column_map["Item Code"]))

    if not item_code:
        continue

    with db.get_session() as s:

        exists = s.query(db.Item).filter_by(item_code=item_code).first()

        if exists:
            print(f"Skipped existing item: {item_code}")
            continue

        # measurement unit
        mu_name = clean_value(row.get(column_map["Measurement Unit"]))

        measurement_unit = None

        if mu_name:

            measurement_unit = (
                s.query(db.MeasurementUnit)
                .filter_by(name=mu_name)
                .first()
            )

            if not measurement_unit:

                measurement_unit = db.MeasurementUnit(name=mu_name)

                s.add(measurement_unit)
                s.commit()
        igrade=lean_value(row.get(column_map["Grade"]))
        if igrade ==None:
            item = db.Item(

                item_code=item_code,

                item_name=clean_value(row.get(column_map["Item"])),

                unit_price=clean_float(row.get(column_map["Unit Price"])),

                quantity_in_store=clean_float(row.get(column_map["In Hand"])),

                section_type=clean_value(row.get(column_map["Section Type"])),

                section_code=clean_value(row.get(column_map["Section Code"])),

                section_size=clean_float(row.get(column_map["Section Size"])),

                length=clean_float(row.get(column_map["Length"])),

                scrap_length=clean_float(row.get(column_map["Scrap Length"])),

                width=clean_float(row.get(column_map["Width"])),

                height=clean_float(row.get(column_map["Height"])),

                depth=clean_float(row.get(column_map["Depth"])),

                thickness=clean_float(row.get(column_map["Thickness"])),

                weight=clean_float(row.get(column_map["Weight"])),

                weight_in_tonne=clean_float(row.get(column_map["Weight In Tonne"])),

                available_weight=clean_float(row.get(column_map["Available Weight"])),

                required_weight=clean_float(row.get(column_map["Required Weight"])),

                surface_area=clean_float(row.get(column_map["Surface Area"])),

                cross_section_area=clean_float(row.get(column_map["Cross Section Area"])),

                area=clean_float(row.get(column_map["Area"])),

                density=clean_float(row.get(column_map["Density"])),

                location=clean_value(row.get(column_map["Location"])),

                remark=clean_value(row.get(column_map["Remark"])),

                po_receipt_date=(
                    pd.to_datetime(
                        row.get(column_map["PO Receipt Date"]),
                        errors="coerce"
                    ).date()
                    if not pd.isna(row.get(column_map["PO Receipt Date"]))
                    else None
                ),

                last_date=(
                    pd.to_datetime(
                        row.get(column_map["Last Date"]),
                        errors="coerce"
                    ).date()
                    if not pd.isna(row.get(column_map["Last Date"]))
                    else None
                ),

                measurement_unit=measurement_unit
            )
        else:
            grayde = (
                s.query(db.ItemGrade)
                .filter_by(name=igrade,item_code=item_code)
                .first()
            )

            if not grayde:

                grayde = db.ItemGrade(name=igrade,item_code=item_code,unit_price=clean_float(row.get(column_map["Unit Price"])),quantity=clean_float(row.get(column_map["In Hand"])))

                s.add(grayde)
                s.commit()
            
            item = db.Item(

                item_code=item_code,

                item_name=clean_value(row.get(column_map["Item"])),

                section_type=clean_value(row.get(column_map["Section Type"])),

                section_code=clean_value(row.get(column_map["Section Code"])),

                section_size=clean_float(row.get(column_map["Section Size"])),

                length=clean_float(row.get(column_map["Length"])),

                scrap_length=clean_float(row.get(column_map["Scrap Length"])),

                width=clean_float(row.get(column_map["Width"])),

                height=clean_float(row.get(column_map["Height"])),

                depth=clean_float(row.get(column_map["Depth"])),

                thickness=clean_float(row.get(column_map["Thickness"])),

                weight=clean_float(row.get(column_map["Weight"])),

                weight_in_tonne=clean_float(row.get(column_map["Weight In Tonne"])),

                available_weight=clean_float(row.get(column_map["Available Weight"])),

                required_weight=clean_float(row.get(column_map["Required Weight"])),

                surface_area=clean_float(row.get(column_map["Surface Area"])),

                cross_section_area=clean_float(row.get(column_map["Cross Section Area"])),

                area=clean_float(row.get(column_map["Area"])),

                density=clean_float(row.get(column_map["Density"])),

                location=clean_value(row.get(column_map["Location"])),

                remark=clean_value(row.get(column_map["Remark"])),

                po_receipt_date=(
                    pd.to_datetime(
                        row.get(column_map["PO Receipt Date"]),
                        errors="coerce"
                    ).date()
                    if not pd.isna(row.get(column_map["PO Receipt Date"]))
                    else None
                ),

                last_date=(
                    pd.to_datetime(
                        row.get(column_map["Last Date"]),
                        errors="coerce"
                    ).date()
                    if not pd.isna(row.get(column_map["Last Date"]))
                    else None
                ),

                measurement_unit=measurement_unit
            )
            


        s.add(item)
        s.commit()

        print(f"Added item: {item_code}")