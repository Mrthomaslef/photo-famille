#!/usr/bin/env python3
"""
Extrait toutes les photos et vidéos de la conversation WhatsApp 'Famille fontenay'
(33660819918-1631347490@g.us) depuis l'archive iCloud WhatsApp (Media.tar, Thumbnail.tar)
et le dossier local WhatsApp, et croise avec ChatStorage.sqlite pour associer :
- Date et heure exactes
- Expéditeur (Membre de la famille)
- Légende / message associé et contexte de conversation autour de la photo
"""
import datetime
import hashlib
import json
import os
import shutil
import sqlite3
import tarfile
from pathlib import Path
from PIL import Image

PROJECT_DIR = Path("/Users/thomaslefevre/.t3/projects/photo-famille")
PHOTOS_DIR = PROJECT_DIR / "photos"
THUMBS_DIR = PROJECT_DIR / "thumbs"
VIDEOS_DIR = PROJECT_DIR / "videos"
DATA_DIR = PROJECT_DIR / "data"

for d in (PHOTOS_DIR, THUMBS_DIR, VIDEOS_DIR, DATA_DIR):
    d.mkdir(parents=True, exist_ok=True)

BACKUP_DIR = Path("/Users/thomaslefevre/Library/Mobile Documents/57T9237FN3~net~whatsapp~WhatsApp/Accounts/33658552152/backup")
WHATSAPP_SHARED = Path("/Users/thomaslefevre/Library/Group Containers/group.net.whatsapp.WhatsApp.shared")
CHAT_DB = WHATSAPP_SHARED / "ChatStorage.sqlite"
GROUP_JID = "33660819918-1631347490@g.us"
APPLE_EPOCH_OFFSET = 978307200

SENDER_MAP = {
    "73469777735808@lid": "MamieSo (Sophie)",
    "33662373645@s.whatsapp.net": "MamieSo (Sophie)",
    "185834795970737@lid": "Papini (Nicolas)",
    "33660819918@s.whatsapp.net": "Papini (Nicolas)",
    "25804280955093@lid": "Lucie",
    "194261421129894@lid": "Marie",
    "33607688499@s.whatsapp.net": "Marie",
    "193454067953692@lid": "Matthieu",
    "33661072947@s.whatsapp.net": "Matthieu",
    "274070620872750@lid": "Arthur",
    "33782147755@s.whatsapp.net": "Arthur",
    "756048511140@lid": "Étienne",
}

def load_db_context():
    if not CHAT_DB.exists():
        return [], {}
    conn = sqlite3.connect(f"file:{CHAT_DB}?mode=ro", uri=True)
    cur = conn.cursor()

    # Load all messages in session 363
    cur.execute("""
        SELECT
            m.Z_PK,
            m.ZMESSAGETYPE,
            m.ZMESSAGEDATE + 978307200 as ts,
            m.ZTEXT,
            mi.ZTITLE,
            mi.ZFILESIZE,
            m.ZISFROMME,
            gm.ZMEMBERJID,
            gm.ZCONTACTNAME,
            mi.ZMEDIALOCALPATH,
            mi.ZXMPPTHUMBPATH
        FROM ZWAMESSAGE m
        LEFT JOIN ZWAMEDIAITEM mi ON m.ZMEDIAITEM = mi.Z_PK
        LEFT JOIN ZWAGROUPMEMBER gm ON m.ZGROUPMEMBER = gm.Z_PK
        WHERE m.ZCHATSESSION = (SELECT Z_PK FROM ZWACHATSESSION WHERE ZCONTACTJID = ?)
        ORDER BY m.ZMESSAGEDATE ASC
    """, (GROUP_JID,))
    rows = cur.fetchall()
    conn.close()

    all_msgs = []
    media_by_size = {}
    for r in rows:
        pk, mtype, ts, text, title, fsize, is_me, mjid, cname, lpath, tpath = r
        if is_me:
            sender = "Thomas"
        else:
            sender = SENDER_MAP.get(mjid) or cname or "Famille"
        msg = {
            "pk": pk,
            "type": mtype,
            "ts": ts,
            "date_iso": datetime.datetime.fromtimestamp(ts).isoformat(),
            "text": (text or "").strip(),
            "caption": (title or "").strip(),
            "filesize": fsize or 0,
            "sender": sender,
            "local_path": lpath,
            "thumb_path": tpath,
        }
        # Clean hex-like reaction/system titles
        if len(msg["caption"]) == 20 and all(c in "0123456789ABCDEF" for c in msg["caption"]):
            msg["caption"] = ""
        all_msgs.append(msg)
        if mtype == 1 and fsize:
            media_by_size.setdefault(fsize, []).append(msg)

    return all_msgs, media_by_size

def find_nearby_context(ts, all_msgs, window_sec=7200):
    """Trouve les messages texte ou légendes proches temporellement (dans les 2h)."""
    nearby = []
    for m in all_msgs:
        if abs(m["ts"] - ts) <= window_sec:
            txt = m["caption"] or m["text"]
            if txt and not txt.startswith("http") and len(txt) > 2:
                nearby.append({
                    "sender": m["sender"],
                    "text": txt,
                    "delta_min": round((m["ts"] - ts) / 60, 1)
                })
    return nearby[:8]

def main():
    print("Chargement du contexte SQLite ChatStorage...")
    all_msgs, media_by_size = load_db_context()
    print(f"  {len(all_msgs)} messages chargés.")

    extracted = []
    seen_uuids = set()

    # 1. Extract from Media.tar
    media_tar_path = BACKUP_DIR / "Media.tar"
    thumb_tar_path = BACKUP_DIR / "Thumbnail.tar"

    thumbs_in_tar = {}
    if thumb_tar_path.exists():
        print("Indexation de Thumbnail.tar...")
        tf_t = tarfile.open(thumb_tar_path)
        for m in tf_t.getmembers():
            if GROUP_JID in m.name and m.size > 0 and m.name.endswith(".thumb"):
                uuid = Path(m.name).stem
                thumbs_in_tar[uuid] = m

    print("Extraction des photos depuis Media.tar...")
    tf_m = tarfile.open(media_tar_path)
    members = [m for m in tf_m.getmembers() if GROUP_JID in m.name and m.name.endswith(".jpg")]
    print(f"  {len(members)} entrées JPG trouvées dans Media.tar.")

    used_db_pks = set()

    for idx, m in enumerate(sorted(members, key=lambda x: x.mtime)):
        uuid = Path(m.name).stem
        if uuid in seen_uuids:
            continue
        seen_uuids.add(uuid)

        is_thumb_fallback = False
        raw_bytes = b""
        if m.size > 0:
            raw_bytes = tf_m.extractfile(m).read()
        elif uuid in thumbs_in_tar:
            tm = thumbs_in_tar[uuid]
            raw_bytes = tf_t.extractfile(tm).read()
            is_thumb_fallback = True
        else:
            continue

        if not raw_bytes:
            continue

        dt = datetime.datetime.fromtimestamp(m.mtime)
        date_prefix = dt.strftime("%Y-%m-%d_%H%M%S")
        filename = f"{date_prefix}_{uuid[:8]}.jpg"
        out_path = PHOTOS_DIR / filename
        out_path.write_bytes(raw_bytes)
        os.utime(out_path, (m.mtime, m.mtime))

        # Get image dimensions
        width, height = 0, 0
        try:
            with Image.open(out_path) as im:
                width, height = im.size
        except Exception:
            pass

        # Match with DB message if available
        matched_msg = None
        if m.size in media_by_size:
            cands = [c for c in media_by_size[m.size] if c["pk"] not in used_db_pks]
            if not cands:
                cands = media_by_size[m.size]
            # Pick closest in time
            cands.sort(key=lambda c: abs(c["ts"] - m.mtime))
            matched_msg = cands[0]
            used_db_pks.add(matched_msg["pk"])

        msg_ts = matched_msg["ts"] if matched_msg else m.mtime
        msg_dt = datetime.datetime.fromtimestamp(msg_ts)
        sender = matched_msg["sender"] if matched_msg else "Famille Fontenay"
        caption = matched_msg["caption"] if matched_msg else ""
        nearby = find_nearby_context(msg_ts, all_msgs) if all_msgs else []

        extracted.append({
            "id": uuid,
            "filename": filename,
            "path": f"photos/{filename}",
            "timestamp": msg_ts,
            "mtime": m.mtime,
            "date": msg_dt.strftime("%Y-%m-%d"),
            "year": msg_dt.strftime("%Y"),
            "month": msg_dt.strftime("%Y-%m"),
            "time": msg_dt.strftime("%H:%M"),
            "size": len(raw_bytes),
            "width": width,
            "height": height,
            "is_thumb_fallback": is_thumb_fallback,
            "sender": sender,
            "caption": caption,
            "nearby_messages": nearby,
            "db_pk": matched_msg["pk"] if matched_msg else None,
        })

    # Also copy the 2 local videos if present
    local_media_dir = WHATSAPP_SHARED / "Message" / "Media" / GROUP_JID
    videos = []
    if local_media_dir.exists():
        for mp4 in local_media_dir.rglob("*.mp4"):
            uuid = mp4.stem
            mtime = mp4.stat().st_mtime
            dt = datetime.datetime.fromtimestamp(mtime)
            vname = f"{dt.strftime('%Y-%m-%d_%H%M%S')}_{uuid[:8]}.mp4"
            vout = VIDEOS_DIR / vname
            shutil.copy2(mp4, vout)
            videos.append({
                "id": uuid,
                "filename": vname,
                "path": f"videos/{vname}",
                "timestamp": mtime,
                "date": dt.strftime("%Y-%m-%d"),
                "size": mp4.stat().st_size,
            })

    extracted.sort(key=lambda x: x["timestamp"])
    out_json = DATA_DIR / "extracted_raw.json"
    out_json.write_text(json.dumps({
        "group_name": "Famille fontenay",
        "group_jid": GROUP_JID,
        "extracted_at": datetime.datetime.now().isoformat(),
        "total_photos": len(extracted),
        "total_videos": len(videos),
        "photos": extracted,
        "videos": videos,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Terminé ! {len(extracted)} photos extraites dans {PHOTOS_DIR} et indexées dans {out_json}.")

if __name__ == "__main__":
    main()
