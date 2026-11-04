<img src="assets/icon.svg" width="64" height="64" alt="">

# Album Famille Fontenay — Mémoire WhatsApp (2023–2026)

Application et archive thématique des **1 432 photos** (et vidéos) extraites de la conversation WhatsApp **« Famille fontenay »** (`33660819918-1631347490@g.us`), croisées avec la base locale `ChatStorage.sqlite` et classées automatiquement par intelligence visuelle (**Apple Vision**) et par contexte des messages.

## 🚀 Consulter l'application

- **Ouverture directe (sans serveur)** : ouvrez [`index.html`](file:///Users/thomaslefevre/.t3/projects/photo-famille/index.html) dans n'importe quel navigateur.
- **Via le lanceur macOS** : double-cliquez sur [`Ouvrir_Album_Famille_Fontenay.command`](file:///Users/thomaslefevre/.t3/projects/photo-famille/Ouvrir_Album_Famille_Fontenay.command) ou lancez :
  ```bash
  python3 serve_app.py
  ```

## 🗂️ Organisation par thèmes (`themes_organises/`)

Les 1 432 photos sont également rangées sur le disque dans [`themes_organises/`](file:///Users/thomaslefevre/.t3/projects/photo-famille/themes_organises) :

1. **👶 Émile — Grandir & Quotidien** (`01_Emile_Grandir_et_Quotidien`) : 479 photos principales (727 associées)
2. **🌊 Mer, Étretat, Yport & Corse** (`02_Mer_Etretat_Yport_et_Corse`) : 240 photos principales (344 associées)
3. **🌿 Jardin, Parc, Ferme & Animaux** (`04_Jardin_Parc_Ferme_et_Animaux`) : 248 photos principales (614 associées)
4. **🏡 Maison & Cocooning en Famille** (`07_Maison_et_Cocooning`) : 164 photos principales (314 associées)
5. **👨‍👩‍👧‍👦 Réunions de Famille & Fêtes** (`03_Reunions_Famille_et_Fetes`) : 114 photos principales (313 associées)
6. **🍽️ À Table & Moments Gourmands** (`05_A_Table_et_Gastronomie`) : 78 photos principales (145 associées)
7. **⛷️ Ski, Valloire, Golf & Sport** (`06_Ski_Valloire_Golf_et_Sport`) : 65 photos principales (111 associées)
8. **🗂️ Archives, Projets & Clins d'œil** (`08_Archives_Projets_et_Captures`) : 44 photos principales (61 associées)

## 🔄 Mettre à jour avec les nouvelles photos WhatsApp

```bash
python3 extract_whatsapp_photos.py
swiftc -O analyze_vision.swift -o analyze_vision && ./analyze_vision && rm -f analyze_vision
python3 build_catalog_and_themes.py
```
