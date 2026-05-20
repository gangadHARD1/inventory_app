import sys
import os
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


print("Done.")