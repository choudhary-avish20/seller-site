"""
Seed dummy clothing products (underwear, socks, shirts, etc.) for local dev/demo.

Safe to re-run: categories are matched by slug and skipped if they already
exist; products are matched by slug and their content is upserted (so
re-running after editing this file refreshes images/description/badges
without creating duplicates).

Usage:
    cd backend && source venv/bin/activate && python3 seed_products.py
"""
import sys
import os
import json
from urllib.parse import quote

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.category import Category
from app.models.product import Product, StockStatus
from app.schemas.category import slugify as cat_slugify
from app.schemas.product import slugify as prod_slugify


# ---- Category tree: (name, [child names]) ----
CATEGORY_TREE = {
    "Women's Clothing": ["Women's Underwear", "Women's Socks", "Dresses", "Blouses"],
    "Men's Clothing": ["Men's Underwear", "Men's Socks", "T-Shirts", "Shirts"],
    "Kids' Clothing": ["Kids' Underwear", "Kids' Socks"],
}

# Placeholder image theme (bg/fg hex, no '#') per top-level group, used only
# for demo product photography stand-ins until real photos are uploaded.
THEME = {
    "women": ("f6d9e3", "8a2b4c"),
    "men": ("d6e6f5", "1c4e80"),
    "kids": ("fff2c2", "9a7b00"),
}


def _theme_for(name: str):
    n = name.lower()
    if n.startswith("women"):
        return THEME["women"]
    if n.startswith("men"):
        return THEME["men"]
    return THEME["kids"]


def _placeholder_images(name: str, angle_labels=("Front", "Back")):
    bg, fg = _theme_for(name)
    imgs = []
    for label in angle_labels:
        text = quote(f"{name} — {label}")
        imgs.append(f"https://placehold.co/600x450/{bg}/{fg}?text={text}&font=roboto")
    return imgs


# ---- Products ----
# fields: name, category, price_net, pack_size, pack_increment,
#         badges=(is_bestseller, is_popular, is_on_sale, sale_price_net),
#         material, sizes, care
PRODUCTS = [
    ("Women's Cotton Briefs 5-Pack", "Women's Underwear", 18.50, 5, 12, (True, True, False, None),
     "95% cotton, 5% elastane", "S / M / L / XL", "Machine wash 40°C, do not bleach"),
    ("Women's Seamless Thong 3-Pack", "Women's Underwear", 14.00, 3, 12, (False, True, False, None),
     "Microfiber blend", "S / M / L", "Hand wash recommended, line dry"),
    ("Women's Lace Bralette", "Women's Underwear", 22.00, 1, 6, (False, False, True, 16.50),
     "Nylon lace, cotton lining", "S / M / L / XL", "Hand wash cold, do not tumble dry"),
    ("Women's Cotton Ankle Socks 10-Pack", "Women's Socks", 12.00, 10, 12, (True, False, False, None),
     "80% cotton, 15% polyester, 5% elastane", "35-38 / 39-42", "Machine wash 40°C"),
    ("Women's Knee-High Socks 3-Pack", "Women's Socks", 15.00, 3, 12, (False, False, False, None),
     "Cotton blend with reinforced heel", "One size (36-41)", "Machine wash 30°C"),
    ("Women's Summer Floral Dress", "Dresses", 65.00, 1, 6, (True, False, False, None),
     "100% viscose", "S / M / L / XL", "Machine wash 30°C, iron on low heat"),
    ("Women's Casual Midi Dress", "Dresses", 58.00, 1, 6, (False, True, False, None),
     "95% cotton, 5% elastane", "S / M / L / XL", "Machine wash 30°C"),
    ("Women's Elegant Evening Dress", "Dresses", 89.00, 1, 4, (False, False, True, 69.00),
     "Polyester with satin finish", "S / M / L", "Dry clean only"),
    ("Women's Silk Blouse", "Blouses", 45.00, 1, 6, (False, False, False, None),
     "100% silk", "S / M / L / XL", "Dry clean or hand wash cold"),
    ("Women's Office Blouse", "Blouses", 38.00, 1, 6, (False, True, False, None),
     "65% cotton, 35% polyester", "S / M / L / XL", "Machine wash 30°C, iron on medium"),
    ("Men's Cotton Boxer Briefs 5-Pack", "Men's Underwear", 20.00, 5, 12, (True, True, False, None),
     "95% cotton, 5% elastane", "M / L / XL / XXL", "Machine wash 40°C"),
    ("Men's Classic Boxer Shorts 3-Pack", "Men's Underwear", 16.50, 3, 12, (False, False, False, None),
     "100% cotton poplin", "M / L / XL / XXL", "Machine wash 40°C"),
    ("Men's Thermal Long Johns", "Men's Underwear", 25.00, 1, 6, (False, False, True, 19.90),
     "Cotton-fleece blend", "M / L / XL", "Machine wash 30°C, no tumble dry"),
    ("Men's Sport Ankle Socks 10-Pack", "Men's Socks", 13.00, 10, 12, (True, True, False, None),
     "75% cotton, 20% polyester, 5% elastane", "40-43 / 44-46", "Machine wash 40°C"),
    ("Men's Business Dress Socks 5-Pack", "Men's Socks", 17.00, 5, 12, (False, False, False, None),
     "Combed cotton with reinforced toe", "40-43 / 44-46", "Machine wash 30°C"),
    ("Men's Basic Crew T-Shirt 3-Pack", "T-Shirts", 28.00, 3, 12, (True, False, False, None),
     "100% combed cotton, 180gsm", "S / M / L / XL / XXL", "Machine wash 40°C"),
    ("Men's Graphic Print T-Shirt", "T-Shirts", 19.90, 1, 12, (False, True, False, None),
     "100% cotton, 190gsm", "S / M / L / XL", "Machine wash 30°C, print side inward"),
    ("Men's V-Neck T-Shirt 2-Pack", "T-Shirts", 22.00, 2, 12, (False, False, True, 17.50),
     "95% cotton, 5% elastane", "S / M / L / XL / XXL", "Machine wash 40°C"),
    ("Men's Cotton Dress Shirt", "Shirts", 42.00, 1, 6, (False, False, False, None),
     "100% cotton poplin", "S / M / L / XL / XXL", "Machine wash 30°C, iron on medium"),
    ("Men's Flannel Check Shirt", "Shirts", 39.00, 1, 6, (True, False, False, None),
     "100% brushed cotton flannel", "M / L / XL / XXL", "Machine wash 30°C"),
    ("Kids' Cotton Briefs 5-Pack", "Kids' Underwear", 15.00, 5, 12, (False, True, False, None),
     "100% cotton", "3-4y / 5-6y / 7-8y / 9-10y", "Machine wash 40°C"),
    ("Kids' Vest & Brief Set", "Kids' Underwear", 18.00, 1, 12, (False, False, False, None),
     "100% cotton", "2-3y / 4-5y / 6-7y", "Machine wash 40°C"),
    ("Kids' Cartoon Print Socks 6-Pack", "Kids' Socks", 10.00, 6, 12, (True, True, False, None),
     "80% cotton, 15% polyester, 5% elastane", "23-26 / 27-30 / 31-34", "Machine wash 40°C"),
    ("Kids' School Socks 5-Pack", "Kids' Socks", 9.50, 5, 12, (False, False, True, 7.50),
     "75% cotton, 23% polyester, 2% elastane", "27-30 / 31-34 / 35-38", "Machine wash 40°C"),
]


def get_or_create_category(db, name: str, parent_id=None) -> Category:
    slug = cat_slugify(name)
    existing = db.query(Category).filter(Category.slug == slug).first()
    if existing:
        return existing
    cat = Category(name=name, slug=slug, parent_id=parent_id, is_active=True)
    db.add(cat)
    db.flush()
    print(f"  + category: {name} ({slug})")
    return cat


def seed():
    db = SessionLocal()
    try:
        name_to_id = {}
        for parent_name, children in CATEGORY_TREE.items():
            parent = get_or_create_category(db, parent_name)
            name_to_id[parent_name] = parent.id
            for child_name in children:
                child = get_or_create_category(db, child_name, parent_id=parent.id)
                name_to_id[child_name] = child.id
        db.commit()

        created, updated = 0, 0
        for name, cat_name, price_net, pack_size, pack_increment, badges, material, sizes, care in PRODUCTS:
            slug = prod_slugify(name)
            is_bestseller, is_popular, is_on_sale, sale_price_net = badges
            price_gross = round(price_net * 1.23, 2)
            description = (
                f"{name} — wholesale pack of {pack_size}, quality wholesale clothing from WolkaGo.\n"
                f"Material: {material}\n"
                f"Available sizes: {sizes}\n"
                f"Care: {care}"
            )
            images = json.dumps(_placeholder_images(name))

            existing = db.query(Product).filter(Product.slug == slug).first()
            if existing:
                existing.description = description
                existing.images = images
                existing.is_bestseller = is_bestseller
                existing.is_popular = is_popular
                existing.is_on_sale = is_on_sale
                existing.sale_price_net = sale_price_net
                updated += 1
                print(f"  ~ updated: {name}")
                continue

            product = Product(
                category_id=name_to_id[cat_name],
                name=name,
                slug=slug,
                description=description,
                images=images,
                pack_size=pack_size,
                price_net=price_net,
                price_gross=price_gross,
                vat_rate=23.00,
                pack_increment=pack_increment,
                stock_quantity=200,
                stock_status=StockStatus.in_stock,
                is_active=True,
                is_bestseller=is_bestseller,
                is_popular=is_popular,
                is_on_sale=is_on_sale,
                sale_price_net=sale_price_net,
            )
            db.add(product)
            created += 1
            print(f"  + product: {name}")
        db.commit()
        print(f"\nDone. {created} new product(s) created, {updated} existing product(s) updated.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
