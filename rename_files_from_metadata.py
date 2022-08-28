from unittest.mock import PropertyMock
from PIL import Image, ExifTags
from ffmpeg import probe
from pathlib import Path
import datetime as dt 
from shutil import copyfile, rmtree
from tqdm import tqdm
from hashlib import sha1
import click
import logging

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)

IMG_FILE_TYPES = {".JPG", ".jpg", ".bmp"}
VID_FILE_TYPES = {".MP4", ".mp4"}
FILE_NAME_TS_FORMAT = "%Y-%m-%d|%H-%M-%S"

@click.command()
@click.argument("src_dir", type=Path)
@click.argument("dest_dir", type=Path)
@click.argument("src_name", type=str)
def copy_and_reorganise(src_dir, dest_dir, src_name):
    all_files = list(src_dir.iterdir())

    if dest_dir.exists() and not delete_directory_with_prompt(dest_dir):
        raise FileExistsError("The destination directory already exists!")

    for path in tqdm(all_files, total=len(all_files)):
        copy_file_using_timestamp(path, dest_dir, src_name)
    
    check_files(dest_dir, src_dir)


def delete_directory_with_prompt(directory):
    delete_dir = prompt_user_to_delete(directory)
    if delete_dir:
        rmtree(directory)
    return delete_dir


def prompt_user_to_delete(directory):
    valid_answer = False
    while not valid_answer:
        ans = input(f"{directory.name} already exists. Do you want to delete it? [y/n]")
        valid_answer = (ans.lower() in {"y", "n"})
    return ans.lower() == "y"


def positive_ints():
    num = 0
    while True:
        num += 1
        yield num


def copy_file_using_timestamp(src_file, dest_dir, src_name):
    new_sub_path = get_new_path_for_file(src_file, src_name)
    copy_to_destination(src_file, dest_dir / new_sub_path)


def get_new_path_for_file(src_file, src_name):
    file_type, file_timestamp = get_file_details(src_file)

    timestamp_str = file_timestamp.strftime(FILE_NAME_TS_FORMAT)
    new_name = f"{timestamp_str}_{file_type}_from_{src_name}{src_file.suffix}"
    new_path = file_timestamp.strftime("%Y-%m") + f"_{file_type}"
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


def get_timestamp_from_vid_path(src_file):
    orig_timestamp_str = probe(src_file)["format"]["tags"]["creation_time"]
    return dt.datetime.fromisoformat(orig_timestamp_str.rstrip("Z"))
    

def get_exif_dict(img):
    return {ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS}


def copy_to_destination(src_file, new_file):
    dest_dir = new_file.parent
    dest_dir.mkdir(parents=True, exist_ok=True)

    name, ext = new_file.stem, new_file.suffix
    numbers = positive_ints()
    while new_file.exists():
        copy_num = next(numbers)
        new_file = dest_dir / f"{name}_{copy_num + 1}{ext}"

    copyfile(src_file, new_file)


def hash_file(path):
    with open(path, "rb") as f:
        contents = f.read()
    return sha1(contents).hexdigest()


def check_files(dest_dir, src_dir):
    logging.info("Validating copy...")
    src_hash_dict = get_hashes(src_dir)
    dest_hash_dict = get_hashes(dest_dir)

    src_hashes = set(src_hash_dict.keys())
    dest_hashes = set(dest_hash_dict.keys())

    if src_hashes == dest_hashes:
        logging.info(f"{len(dest_hashes)}/{len(src_hashes)} reorganised successfully")        
        return True
    
    logging.info("Files missing!!")
    missing_from_dest = {src_hash_dict[hash] for hash in src_hashes.difference(dest_hashes)}
    if missing_from_dest:
        logging.info("Missing from destination: ")
        logging.info("\n\t".join([str(path) for path in missing_from_dest]))
    
    missing_from_src = {dest_hash_dict[hash] for hash in dest_hashes.difference(src_hashes)}
    if missing_from_src:
        logging.info("Missing from source: ")
        logging.info("\n\t".join([str(path) for path in missing_from_src]))


def get_hashes(dir):
    files = [path for path in dir.glob("**/*") if path.is_file()]
    hashes = {hash_file(path): path for path in files}
    assert len(hashes.keys()) == len(files), (
        f"Number of files and hashes are different: "
        f"num files: {len(files)}, num hashes: {len(hashes.keys())}"
    )
    return hashes


if __name__ == "__main__":
    copy_and_reorganise()
