from . import fernet


def format_media_list(medias):
    lst = []
    count = 0
    for m in medias:
        count += 1
        lst.append({
            "sl": count,
            "name": m.name,
            "area": m.area.name,
            "path": m.path,
            "created_by": m.user.email,
            "created_at": m.time_created,
            "updated_at": m.time_updated,
            "lat": m.lat,
            "lng": m.long
        })
    return lst


def format_area_list(areas):
    lst = []
    count = 0
    for a, u in areas:
        count += 1
        lst.append({
            "sl": count,
            "name": a.name,
            "description": a.description,
            "id": fernet.encrypt(str(a.id).encode()).decode(),
            "created_by": u.email,
            "created_at": a.time_created,
            "updated_at": a.time_updated,
            "lat": a.lat,
            "lng": a.long
        })
    return lst
