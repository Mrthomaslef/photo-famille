#!/usr/bin/env python3
"""
Génère les miniatures optimisées (480px WebP/JPEG), fusionne l'analyse Apple Vision
et le contexte WhatsApp (messages, légendes, dates, membres de la famille),
et classe chaque photo de 'Famille fontenay' dans des thèmes riches et intuitifs.
"""
import collections
import concurrent.futures
import datetime
import json
import os
import shutil
from pathlib import Path
from PIL import Image

PROJECT_DIR = Path("/Users/thomaslefevre/.t3/projects/photo-famille")
PHOTOS_DIR = PROJECT_DIR / "photos"
THUMBS_DIR = PROJECT_DIR / "thumbs"
DATA_DIR = PROJECT_DIR / "data"
THEMES_DIR = PROJECT_DIR / "themes_organises"

RAW_JSON = DATA_DIR / "extracted_raw.json"
VISION_JSON = DATA_DIR / "vision_analysis.json"

THEMES_META = {
    "emile": {
        "id": "emile",
        "title": "Émile — Grandir & Quotidien",
        "subtitle": "Premiers mois, sourires, jeux, siestes chez MamieSo, parc & découvertes",
        "icon": "👶",
        "color": "#f59e0b",
        "folder": "01_Emile_Grandir_et_Quotidien"
    },
    "mer_vacances": {
        "id": "mer_vacances",
        "title": "Mer, Étretat, Yport & Corse",
        "subtitle": "Plage, falaises, pêche aux crabes et crevettes, baignades & vacances d'été",
        "icon": "🌊",
        "color": "#0ea5e9",
        "folder": "02_Mer_Etretat_Yport_et_Corse"
    },
    "famille_fetes": {
        "id": "famille_fetes",
        "title": "Réunions de Famille & Fêtes",
        "subtitle": "Portraits de groupe, Noël, anniversaires, mariages & générations réunies",
        "icon": "👨‍👩‍👧‍👦",
        "color": "#ec4899",
        "folder": "03_Reunions_Famille_et_Fetes"
    },
    "nature_balades": {
        "id": "nature_balades",
        "title": "Jardin, Parc, Ferme & Animaux",
        "subtitle": "Balades au vert, jardin de Fontenay, ferme, chiens (Pianou) & plein air",
        "icon": "🌿",
        "color": "#10b981",
        "folder": "04_Jardin_Parc_Ferme_et_Animaux"
    },
    "repas_gastronomie": {
        "id": "repas_gastronomie",
        "title": "À Table & Moments Gourmands",
        "subtitle": "Repas de famille, restaurants, gâteaux d'anniversaire, gaufres & apéros",
        "icon": "🍽️",
        "color": "#f97316",
        "folder": "05_A_Table_et_Gastronomie"
    },
    "montagne_sport": {
        "id": "montagne_sport",
        "title": "Ski, Valloire, Golf & Sport",
        "subtitle": "Pistes de ski à Valloire, neige, golf / mini-golf, course à pied & marathon",
        "icon": "⛷️",
        "color": "#6366f1",
        "folder": "06_Ski_Valloire_Golf_et_Sport"
    },
    "maison_cocooning": {
        "id": "maison_cocooning",
        "title": "Maison & Cocooning en Famille",
        "subtitle": "Moments doux au salon, lectures, canapé, jeux d'intérieur & vie à la maison",
        "icon": "🏡",
        "color": "#8b5cf6",
        "folder": "07_Maison_et_Cocooning"
    },
    "souvenirs_docs": {
        "id": "souvenirs_docs",
        "title": "Archives, Projets & Clins d'œil",
        "subtitle": "Photos souvenirs d'époque, plans d'appartement, créations & captures",
        "icon": "🗂️",
        "color": "#64748b",
        "folder": "08_Archives_Projets_et_Captures"
    }
}

FRENCH_TAG_LABELS = {
    "baby": "Bébé",
    "child": "Enfant",
    "people": "Personnes",
    "adult": "Adulte",
    "outdoor": "Extérieur",
    "ocean": "Mer / Océan",
    "beach": "Plage",
    "water": "Eau",
    "water_body": "Plan d'eau",
    "lake": "Lac / Mer",
    "cliff": "Falaises",
    "rocks": "Rochers",
    "snow": "Neige",
    "frozen": "Hiver / Neige",
    "winter_sport": "Ski / Hiver",
    "golf": "Golf",
    "golf_course": "Terrain de golf",
    "golf_club": "Club de golf",
    "sport": "Sport",
    "athletics": "Course / Sport",
    "bicycle": "Vélo",
    "stroller": "Poussette",
    "toy": "Jouets",
    "stuffed_animals": "Peluches",
    "pacifier": "Tétine",
    "high_chair": "Chaise haute",
    "playground": "Parc de jeux",
    "swing_playground": "Balançoire",
    "carousel": "Manège",
    "amusement_park": "Fête / Manège",
    "animal": "Animaux",
    "dog": "Chien",
    "canine": "Chien",
    "terrier": "Chien",
    "adult_cat": "Chat",
    "goat": "Chèvre / Ferme",
    "ungulates": "Animaux de ferme",
    "mammal": "Animaux",
    "food": "Repas",
    "dessert": "Dessert",
    "plate": "Assiette",
    "tableware": "À table",
    "drinking_glass": "Verre / Trinquer",
    "restaurant": "Restaurant",
    "kitchen": "Cuisine",
    "sofa": "Canapé",
    "living_room": "Salon",
    "bedroom": "Chambre",
    "bed": "Lit / Sieste",
    "bedding": "Sieste / Dodo",
    "pillow": "Coussin / Cocooning",
    "bath": "Bain",
    "pool": "Piscine",
    "swimsuit": "Baignade",
    "swimming": "Baignade",
    "grass": "Jardin / Pelouse",
    "plant": "Plantes",
    "foliage": "Verdure",
    "forest": "Forêt",
    "park": "Parc",
    "hill": "Colline / Paysage",
    "sunset_sunrise": "Coucher de soleil",
    "blue_sky": "Grand beau temps",
    "christmas_tree": "Sapin de Noël",
    "celebration": "Fête",
    "balloon": "Ballons / Fête",
    "document": "Document",
    "screenshot": "Capture d'écran",
    "printed_page": "Page imprimée",
    "painting": "Peinture / Dessin",
    "art": "Création / Art",
    "car_seat": "En voiture",
    "automobile": "Voiture",
}

def make_thumb(filename: str):
    src = PHOTOS_DIR / filename
    dst = THUMBS_DIR / filename
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((520, 520), Image.Resampling.LANCZOS)
            im.save(dst, "JPEG", quality=82, optimize=True)
    except Exception:
        shutil.copy2(src, dst)

def classify_photo(photo: dict, v_info: dict) -> tuple[str, list[str], list[str], str]:
    """
    Retourne (primary_theme_id, all_theme_ids, french_tags, auto_title).
    Combine l'analyse visuelle Apple Vision, la date, la légende et les messages proches.
    """
    tags_dict = {t["label"]: t["confidence"] for t in v_info.get("tags", [])}
    face_count = v_info.get("faceCount", 0)
    caption = (photo.get("caption") or "").lower()
    nearby_text = " ".join(m["text"].lower() for m in photo.get("nearby_messages", []))
    combined_text = f"{caption} {nearby_text}"
    month = photo.get("month", "")
    date_str = photo.get("date", "")
    dt_month_num = int(month.split("-")[1]) if "-" in month else 0

    scores = collections.defaultdict(float)

    # 1. Souvenirs / Documents / Captures
    if any(k in tags_dict for k in ("document", "screenshot", "printed_page", "handwriting", "map", "diagram")):
        doc_conf = max(tags_dict.get(k, 0) for k in ("document", "screenshot", "printed_page", "handwriting", "map", "diagram"))
        if doc_conf >= 0.25 and face_count == 0:
            scores["souvenirs_docs"] += 6.0
        else:
            scores["souvenirs_docs"] += 2.5
    if any(w in caption for w in ("2009", "2013", "20 ans", "dimension", "miltcg", "chat gpt", "chatgpt")):
        scores["souvenirs_docs"] += 5.0

    # 2. Montagne, Ski, Golf & Sport
    if any(k in tags_dict for k in ("snow", "frozen", "winter_sport", "ski", "sled", "ice")):
        scores["montagne_sport"] += 6.0
    if any(k in tags_dict for k in ("golf", "golf_course", "golf_club")):
        scores["montagne_sport"] += 6.0
    if any(k in tags_dict for k in ("sport", "athletics", "podium", "bicycle", "helmet")):
        scores["montagne_sport"] += 3.5
    if any(w in combined_text for w in ("ski", "piste", "setaz", "crey", "neige", "valloire", "golf", "trou en 1", "semi", "foulée")):
        scores["montagne_sport"] += 4.5
    if date_str in ("2025-12-06", "2025-12-30", "2025-12-31", "2026-01-10", "2026-04-12", "2026-07-21"):
        scores["montagne_sport"] += 2.5

    # 3. Mer, Plage, Étretat, Yport & Corse
    if any(k in tags_dict for k in ("ocean", "beach", "cliff", "coast", "sand", "seashell", "watersport", "boat", "porthole")):
        scores["mer_vacances"] += 5.5
    if any(k in tags_dict for k in ("water", "water_body", "lake", "rocks", "swimsuit", "swimming", "pool", "sunglasses", "sunhat")):
        scores["mer_vacances"] += 3.0
    if any(w in combined_text for w in ("crabe", "crevette", "yport", "iport", "etretat", "étretat", "corse", "plage", "mer", "casino", "éclipse", "eclipse")):
        scores["mer_vacances"] += 4.5
    if dt_month_num in (7, 8) and any(k in tags_dict for k in ("outdoor", "sky", "blue_sky", "water", "rocks", "hill", "land")):
        scores["mer_vacances"] += 2.2

    # 4. Repas & Gastronomie
    if any(k in tags_dict for k in ("food", "dessert", "plate", "restaurant", "fork", "spoon", "bakery", "antipasti", "pizza", "wine")):
        scores["repas_gastronomie"] += 5.0
    if any(k in tags_dict for k in ("tableware", "utensil", "drinking_glass", "bowl", "cup", "bottle", "kitchen")):
        scores["repas_gastronomie"] += 3.0
    if "table" in tags_dict and ("tableware" in tags_dict or "utensil" in tags_dict or "drinking_glass" in tags_dict or "plate" in tags_dict):
        scores["repas_gastronomie"] += 2.5
    if any(w in combined_text for w in ("gauffre", "gaufre", "œuf à la coque", "poulet frite", "coquiflette", "mousse", "resto", "pomme", "saucisse")):
        scores["repas_gastronomie"] += 3.5

    # 5. Jardin, Parc, Ferme & Animaux
    if any(k in tags_dict for k in ("animal", "dog", "canine", "terrier", "adult_cat", "goat", "ungulates", "mammal", "straw_hay", "agriculture")):
        scores["nature_balades"] += 5.5
    if any(k in tags_dict for k in ("playground", "swing_playground", "park", "forest", "carousel", "amusement_park")):
        scores["nature_balades"] += 4.5
    if any(k in tags_dict for k in ("grass", "plant", "foliage", "decorative_plant", "tree", "shrub", "branch", "wood_natural", "fence", "path", "trail")):
        scores["nature_balades"] += 2.8
    if any(w in combined_text for w in ("ferme", "traite", "chien", "pianou", "poule", "parc", "jardin", "promenade", "manège", "ponpon", "cailloux", "niche")):
        scores["nature_balades"] += 4.0

    # 6. Réunions de Famille & Fêtes
    if face_count >= 3:
        scores["famille_fetes"] += 5.5
    elif face_count == 2 and "adult" in tags_dict and "child" not in tags_dict and "baby" not in tags_dict:
        scores["famille_fetes"] += 4.5
    elif face_count == 2 and "adult" in tags_dict:
        scores["famille_fetes"] += 2.5
    if any(k in tags_dict for k in ("christmas_tree", "celebration", "balloon", "crowd", "suit", "banner")):
        scores["famille_fetes"] += 5.0
    if dt_month_num == 12 and photo.get("date", "")[-2:] in ("24", "25", "26", "31"):
        scores["famille_fetes"] += 4.5
    if date_str in ("2026-07-10", "2025-07-10", "2024-07-10", "2026-10-02"):
        scores["famille_fetes"] += 4.0
    if any(w in combined_text for w in ("anniversaire", "noël", "noel", "père noel", "marier", "félicitations", "bravo", "générations", "13 ans pour un papier")):
        scores["famille_fetes"] += 3.5

    # 7. Émile — Grandir & Quotidien
    if any(k in tags_dict for k in ("baby", "pacifier", "stroller", "high_chair", "diaper", "bib", "toy", "stuffed_animals", "car_seat")):
        scores["emile"] += 5.0
    if "child" in tags_dict:
        scores["emile"] += 3.2
    if any(w in combined_text for w in ("emile", "émile", "titi", "mamieso", "sieste", "varicelle", "tétine", "crocs", "dinosaure")):
        scores["emile"] += 3.0

    # 8. Maison & Cocooning
    if any(k in tags_dict for k in ("interior_room", "sofa", "living_room", "bedroom", "bed", "bedding", "pillow", "cabinet", "armchair", "fireplace", "bath", "bathroom")):
        scores["maison_cocooning"] += 3.2
    if "outdoor" not in tags_dict and ("furniture" in tags_dict or "wood_processed" in tags_dict or "textile" in tags_dict):
        scores["maison_cocooning"] += 1.8

    # Fallback if no score
    if not scores:
        if "child" in tags_dict or "baby" in tags_dict:
            scores["emile"] = 2.0
        elif "outdoor" in tags_dict:
            scores["nature_balades"] = 2.0
        elif face_count >= 2:
            scores["famille_fetes"] = 2.0
        else:
            scores["maison_cocooning"] = 1.5

    sorted_themes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary_theme = sorted_themes[0][0]
    all_themes = [t for t, s in sorted_themes if s >= 2.5][:3]
    if primary_theme not in all_themes:
        all_themes.insert(0, primary_theme)

    # French tags
    fr_tags = []
    for t in v_info.get("tags", []):
        lbl = t["label"]
        if lbl in FRENCH_TAG_LABELS and FRENCH_TAG_LABELS[lbl] not in fr_tags:
            fr_tags.append(FRENCH_TAG_LABELS[lbl])
        if len(fr_tags) >= 5:
            break
    if face_count >= 3 and "Groupe / Famille" not in fr_tags:
        fr_tags.insert(0, f"Groupe ({face_count} visages)")
    elif face_count == 2 and "Duo" not in fr_tags:
        fr_tags.insert(0, "Duo")

    # Auto title / description
    if photo.get("caption"):
        auto_title = photo["caption"]
    else:
        # Check if there is an exact nearby caption within 5 mins
        close_msgs = [m["text"] for m in photo.get("nearby_messages", []) if abs(m["delta_min"]) <= 5 and len(m["text"]) < 90]
        if close_msgs:
            auto_title = close_msgs[0]
        else:
            theme_title = THEMES_META[primary_theme]["title"].split("—")[0].strip()
            dt_obj = datetime.datetime.strptime(photo["date"], "%Y-%m-%d")
            months_fr = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
            auto_title = f"{theme_title} • {dt_obj.day} {months_fr[dt_obj.month]} {dt_obj.year}"

    return primary_theme, all_themes, fr_tags, auto_title

def main():
    raw_data = json.loads(RAW_JSON.read_text(encoding="utf-8"))
    vision_data = json.loads(VISION_JSON.read_text(encoding="utf-8"))
    photos = raw_data["photos"]

    print(f"Génération des miniatures pour {len(photos)} photos...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(lambda p: make_thumb(p["filename"]), photos))

    print("Classification thématique et organisation des dossiers...")
    if THEMES_DIR.exists():
        shutil.rmtree(THEMES_DIR)
    THEMES_DIR.mkdir(parents=True, exist_ok=True)
    for tmeta in THEMES_META.values():
        (THEMES_DIR / tmeta["folder"]).mkdir(parents=True, exist_ok=True)

    theme_counts = collections.Counter()
    year_counts = collections.Counter()
    sender_counts = collections.Counter()

    enriched_photos = []
    for p in photos:
        fn = p["filename"]
        v_info = vision_data.get(fn, {"tags": [], "faceCount": 0, "hasText": False})
        primary_theme, all_themes, fr_tags, auto_title = classify_photo(p, v_info)

        p["theme"] = primary_theme
        p["themes"] = all_themes
        p["tags"] = fr_tags
        p["face_count"] = v_info.get("faceCount", 0)
        p["title"] = auto_title
        p["thumb"] = f"thumbs/{fn}"

        theme_counts[primary_theme] += 1
        year_counts[p["year"]] += 1
        sender_counts[p["sender"]] += 1

        # Create symlink in themes_organises/<ThemeFolder>/
        t_folder = THEMES_DIR / THEMES_META[primary_theme]["folder"]
        link_path = t_folder / fn
        rel_src = os.path.relpath(PHOTOS_DIR / fn, t_folder)
        try:
            os.symlink(rel_src, link_path)
        except OSError:
            pass

        enriched_photos.append(p)

    # Sort newest first for default display, or chronological
    enriched_photos.sort(key=lambda x: x["timestamp"], reverse=True)

    themes_summary = []
    for tid, tmeta in THEMES_META.items():
        theme_photos = [p for p in enriched_photos if p["theme"] == tid]
        all_tagged_photos = [p for p in enriched_photos if tid in p["themes"]]
        cover = theme_photos[0]["thumb"] if theme_photos else ""
        # Pick a nice high-res cover with faces if possible
        nice_covers = [p for p in theme_photos if not p.get("is_thumb_fallback") and p.get("width", 0) >= 800]
        if nice_covers:
            cover = nice_covers[0]["thumb"]
        themes_summary.append({
            **tmeta,
            "count": len(theme_photos),
            "total_associated": len(all_tagged_photos),
            "cover": cover,
        })

    catalog = {
        "group_name": "Famille fontenay",
        "group_jid": raw_data["group_jid"],
        "updated_at": datetime.datetime.now().isoformat(),
        "total_photos": len(enriched_photos),
        "total_videos": len(raw_data.get("videos", [])),
        "date_min": min(p["date"] for p in enriched_photos),
        "date_max": max(p["date"] for p in enriched_photos),
        "themes": themes_summary,
        "years": dict(sorted(year_counts.items())),
        "senders": dict(sender_counts.most_common()),
        "videos": raw_data.get("videos", []),
        "photos": enriched_photos,
    }

    (DATA_DIR / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    (DATA_DIR / "catalog.js").write_text(
        "window.FAMILLE_FONTENAY_CATALOG = " + json.dumps(catalog, ensure_ascii=False) + ";\n",
        encoding="utf-8"
    )

    print("Résumé par thème principal :")
    for t in themes_summary:
        print(f"  {t['icon']} {t['title']}: {t['count']} photos principales ({t['total_associated']} associées)")

if __name__ == "__main__":
    main()
