"""네이버 블로그용 개별인정원료 설명 그림을 인스타그램에 자동 업로드한다.

폴더 안의 이미지(jpg/png/webp)를 파일명 순으로 읽어
  1) 인스타그램 규격(1080x1350, 4:5)에 맞게 흰 여백을 넣어 변환하고
  2) 2장 이상이면 캐러셀(여러 장) 게시물 1개로, 1장이면 단일 사진으로 올린다.

사용법 (Windows PowerShell / cmd):
  python upload_blog_images.py "C:\\Users\\kimsi\\OneDrive\\바탕 화면\\네이버블로그"
  python upload_blog_images.py "<폴더>" --dry-run     # 변환만 하고 업로드는 안 함
  python upload_blog_images.py "<폴더>" --separate    # 이미지마다 게시물 따로 올리기

캡션: 폴더 안에 caption.txt 가 있으면 그 내용을 쓰고, 없으면 실행 중에 입력받는다.
로그인: 환경변수 IG_USERNAME / IG_PASSWORD 가 없으면 실행 중에 입력받는다.
        로그인 세션은 이 스크립트 옆 ig_session.json 에 저장되어 다음부터 재로그인하지 않는다.
"""

import argparse
import getpass
import os
import sys
from pathlib import Path

from PIL import Image, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
TARGET_SIZE = (1080, 1350)  # 인스타그램 세로형 4:5
BG_COLOR = (255, 255, 255)
SESSION_FILE = Path(__file__).with_name("ig_session.json")
OUTPUT_DIRNAME = "_instagram"


def find_images(folder: Path) -> list[Path]:
    return sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def fit_to_instagram(src: Path, dst: Path) -> Path:
    """비율을 유지한 채 1080x1350 캔버스 중앙에 배치하고 JPG로 저장한다."""
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            flat = Image.new("RGB", im.size, BG_COLOR)
            flat.paste(im, mask=im.split()[-1])
            im = flat
        else:
            im = im.convert("RGB")
        im.thumbnail(TARGET_SIZE, Image.LANCZOS)
        canvas = Image.new("RGB", TARGET_SIZE, BG_COLOR)
        canvas.paste(im, ((TARGET_SIZE[0] - im.width) // 2,
                          (TARGET_SIZE[1] - im.height) // 2))
        canvas.save(dst, "JPEG", quality=95)
    return dst


def read_caption(folder: Path) -> str:
    caption_file = folder / "caption.txt"
    if caption_file.exists():
        return caption_file.read_text(encoding="utf-8").strip()
    print("캡션을 입력하세요 (빈 줄 입력 시 종료):")
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    return "\n".join(lines)


def login():
    from instagrapi import Client
    from instagrapi.exceptions import LoginRequired

    username = os.environ.get("IG_USERNAME") or input("인스타그램 아이디: ").strip()
    password = os.environ.get("IG_PASSWORD") or getpass.getpass("비밀번호: ")

    cl = Client()
    cl.delay_range = [1, 3]
    cl.challenge_code_handler = lambda user, choice: input(
        f"인증 코드({choice})를 입력하세요: ").strip()

    if SESSION_FILE.exists():
        cl.load_settings(SESSION_FILE)
        try:
            cl.login(username, password)
            cl.get_timeline_feed()
        except LoginRequired:
            old = cl.get_settings()
            cl.set_settings({})
            cl.set_uuids(old["uuids"])
            cl.login(username, password)
    else:
        code = input("2단계 인증 코드(없으면 Enter): ").strip()
        cl.login(username, password, verification_code=code)
    cl.dump_settings(SESSION_FILE)
    return cl


def main() -> int:
    parser = argparse.ArgumentParser(description="블로그 그림 → 인스타그램 업로드")
    parser.add_argument("folder", help="이미지가 들어 있는 폴더 경로")
    parser.add_argument("--dry-run", action="store_true", help="변환만 하고 업로드하지 않음")
    parser.add_argument("--separate", action="store_true", help="이미지마다 게시물을 따로 올림")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"폴더를 찾을 수 없습니다: {folder}")
        return 1

    images = find_images(folder)
    if not images:
        print("업로드할 이미지(jpg/png/webp)가 없습니다.")
        return 1
    if len(images) > 10 and not args.separate:
        print(f"캐러셀은 최대 10장입니다. 앞의 10장만 사용합니다. (전체 {len(images)}장)")
        images = images[:10]

    out_dir = folder / OUTPUT_DIRNAME
    out_dir.mkdir(exist_ok=True)
    prepared = [fit_to_instagram(p, out_dir / f"{i:02d}_{p.stem}.jpg")
                for i, p in enumerate(images, 1)]
    print("변환 완료:")
    for src, dst in zip(images, prepared):
        print(f"  {src.name} -> {dst.name}")

    if args.dry_run:
        print(f"\n--dry-run: 업로드하지 않았습니다. 미리보기: {out_dir}")
        return 0

    caption = read_caption(folder)
    if input(f"\n{len(prepared)}장을 업로드할까요? (y/N): ").strip().lower() != "y":
        print("취소했습니다.")
        return 0

    cl = login()
    if args.separate or len(prepared) == 1:
        for p in prepared:
            media = cl.photo_upload(p, caption)
            print(f"업로드 완료: https://www.instagram.com/p/{media.code}/")
    else:
        media = cl.album_upload(prepared, caption)
        print(f"캐러셀 업로드 완료: https://www.instagram.com/p/{media.code}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
