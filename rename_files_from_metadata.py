from PIL import Image, ExifTags
from pathlib import Path
import datetime as dt 
from shutil import copyfile

IMG_FILE_TYPES = {".JPG", ".jpg", ".bmp"}
VID_FILE_TYPES = {".MP4", ".mp4"}
FILE_NAME_TS_FORMAT = "%Y-%m-%d|%H-%M-%S"

def copy_file_using_timestamp(src_file, dest_dir):
    new_sub_path = get_new_path_for_file(src_file)
    copy_to_destination(src_file, dest_dir / new_sub_path)


def get_new_path_for_file(src_file):
    file_type, file_timestamp = get_file_details(src_file)

    timestamp_str = file_timestamp.strftime(FILE_NAME_TS_FORMAT)
    new_name = f"{timestamp_str}_{file_type}_from_camera{src_file.suffix}"
    new_path = file_timestamp.strftime("%Y-%m")
    return Path(new_path) / new_name


def get_file_details(src_file):
    src_extension = src_file.suffix
    if src_extension in IMG_FILE_TYPES:
        return "img", get_timestamp_from_img_path(src_file)
    elif src_extension in VID_FILE_TYPES:
        return "vid", get_timestamp_from_vid_path(src_file)
    else:
        raise TypeError(f"\"{src_extension}\" is not an accepted file extension")


def get_timestamp_from_img_path(path):
    img = Image.open(path)
    return get_timestamp_from_img(img)


def get_timestamp_from_img(img):
    img_exif = get_exif_dict(img)
    timestamp_str = img_exif["DateTime"]
    return dt.datetime.strptime(timestamp_str, "%Y:%m:%d %H:%M:%S")


def get_exif_dict(img):
    return {ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS}


def get_timestamp_from_vid_path(path):
    pass


def copy_to_destination(src_file, new_file):
    dest_dir = new_file.parent
    dest_dir.mkdir(parents=True)
    copyfile(src_file, new_file)


if __name__ == "__main__":
    root = Path(__file__).parent
    test_file = root / "temp_src" / "IMG_0001.JPG"
    test_out = root / "temp_dest"
    print(test_file)
    print(test_file.exists())
    copy_file_using_timestamp(test_file, test_out)
