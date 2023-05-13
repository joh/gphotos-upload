import os
import argparse
import json

import upload

filetypes = set(['jpg', 'png', 'jpeg'])

def get_album_mediaItems(session, album_id, pageToken=None):
    create_body = {"albumId": album_id, "pageSize": 100}
    if pageToken:
        create_body['pageToken'] = pageToken

    resp = session.post('https://photoslibrary.googleapis.com/v1/mediaItems:search', json.dumps(create_body)).json()
    return resp

def get_album_filenames(session, album_id):
    filenames = []

    resp = get_album_mediaItems(session, album_id)
    for item in resp['mediaItems']:
        #print(item['filename'])
        filenames.append(item['filename'])

    while resp.get('nextPageToken'):
        #print('pageToken', resp['nextPageToken'])
        resp = get_album_mediaItems(session, album_id, resp['nextPageToken'])
        for item in resp['mediaItems']:
            #print(item['filename'])
            filenames.append(item['filename'])

    return filenames

def sync(path, auth_file, album, dry_run=False):
    session = upload.get_authorized_session(auth_file)

    print(f"Fetching list of files in album {album}...")
    album_id = upload.create_or_retrieve_album(session, album)
    album_filenames = get_album_filenames(session, album_id)
    print(f"Found {len(album_filenames)} files in album {album}")
    #print(album_filenames)

    upload_queue = []
    for f in sorted(os.listdir(path)):
        if f.startswith('.'):
            continue
        base, ext = os.path.splitext(f)
        ext = ext[1:].lower()
        if ext not in filetypes:
            continue

        fpath = os.path.join(path, f)
        if f in album_filenames:
            #print(f"{f} already found in album, skipping.")
            continue

        upload_queue.append(fpath)

    #print("upload_queue", upload_queue)
    if not upload_queue:
        print(f"Album already up to date :)")
        return

    print(f"Uploading {len(upload_queue)} new files to album {album}...")

    for f in upload_queue:
        print("Uploading", f)
        if not dry_run:
            upload.upload_photos(session, [f], album)

def main():
    parser = argparse.ArgumentParser(description='Sync photos to Google Photos')
    parser.add_argument('--album', default='Nikon')
    parser.add_argument('--auth-file', default='auth.json')
    parser.add_argument('--dry-run', action='store_true', default=False)
    parser.add_argument('directory')

    args = parser.parse_args()

    sync(args.directory, args.auth_file, args.album, args.dry_run)

if __name__ == '__main__':
    main()
