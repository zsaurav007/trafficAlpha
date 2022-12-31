from . import fernet
from .models import StreamType


def format_media_list(medias):
    lst = []
    count = 0
    for m in medias:
        count += 1
        lst.append(format_media(m, count))
    return lst


def format_media(media, sl=0, area_name=None):
    return {
        "sl": sl,
        "name": media.name,
        "id": fernet.encrypt(str(media.id).encode()).decode(),
        "area": area_name if area_name is not None else media.area.name,
        "path": media.path,
        "created_by": media.user.email,
        "created_at": media.time_created,
        "updated_at": media.time_updated,
        "lat": media.lat,
        "lng": media.long
    }


def format_area_list(areas, current_area=None):
    lst = []
    count = 0
    selected_area = None
    for a, u in areas:
        count += 1
        clips = [format_media(x, area_name=a.name) for x in a.medias if x.media_type == StreamType.clip]
        clip_count = len(clips)
        videos = [format_media(x, area_name=a.name) for x in a.medias if x.media_type == StreamType.video]
        video_count = len(videos)
        rtsp_links = [format_media(x, area_name=a.name) for x in a.medias if x.media_type == StreamType.rtsp]
        rtsp_count = len(rtsp_links)

        temp_area = {
            "sl": count,
            "name": a.name,
            "description": a.description,
            "id": fernet.encrypt(str(a.id).encode()).decode(),
            "clips": clips,
            "videos": videos,
            "rtsp_links": rtsp_links,
            "clip_count": clip_count,
            "video_count": video_count,
            "rtsp_count": rtsp_count,
            "created_by": u.email,
            "created_at": a.time_created,
            "updated_at": a.time_updated,
            "lat": a.lat,
            "lng": a.long
        }

        if current_area == a.id:
            selected_area = temp_area
        lst.append(temp_area)
    if not selected_area:
        print(lst)
        selected_area = lst[0] if len(lst) > 0 else None
    return lst, selected_area
