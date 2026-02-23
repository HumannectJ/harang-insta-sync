import os
import requests
import instaloader
from dotenv import load_dotenv
import logging
import tempfile
import time
from datetime import datetime
from requests.auth import HTTPBasicAuth
from fp.fp import FreeProxy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_environment():
    load_dotenv()
    target_account = os.getenv("TARGET_IG_ACCOUNT", "harang_clinic")
    
    # If the value is a URL like 'https://www.instagram.com/drharang/', extract just 'drharang'
    if target_account and target_account.startswith("http"):
        target_account = target_account.rstrip("/").split("/")[-1]
        
    wp_url = os.getenv("WP_URL", "").rstrip("/")
    wp_username = os.getenv("WP_USERNAME")
    wp_app_password = os.getenv("WP_APP_PASSWORD")
    
    if not all([wp_url, wp_username, wp_app_password]):
        logging.error("Missing WordPress credentials in .env file.")
        exit(1)
        
    return target_account, wp_url, wp_username, wp_app_password

def fetch_instagram_posts(target_account, limit=12):
    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False
    )
    
    ig_sessionid = os.getenv("IG_SESSIONID")
    if ig_sessionid:
        try:
            # Inject session id cookie
            L.context._session.cookies.set("sessionid", ig_sessionid, domain=".instagram.com")
            # Try to fetch current user to verify session is working
            L.context.username = "studiourang.crawler" # Give it a dummy username for internal context 
            L.test_login()
            logging.info("Successfully logged in using session ID")
        except Exception as e:
            logging.warning(f"Failed to login with session ID: {e}")
            
    logging.info(f"Fetching posts from {target_account}...")
    
    posts_data = []
    
    # Try fetching up to 5 times using different proxies
    for attempt in range(5):
        try:
            proxy = FreeProxy(rand=True, timeout=3).get()
            logging.info(f"Attempt {attempt+1}: Using proxy {proxy}")
            L.context._session.proxies = {"http": proxy, "https": proxy}
            
            profile = instaloader.Profile.from_username(L.context, target_account)
            
            for post in profile.get_posts():
                if len(posts_data) >= limit:
                    break
                # Skip video or take the thumbnail. Instaloader provides 'url' which is an image.
                # Even for videos, 'url' points to the thumbnail.
                posts_data.append({
                    'shortcode': post.shortcode,
                    'image_url': post.url,
                    'caption': post.caption if post.caption else '',
                    'timestamp': post.date_utc.isoformat(),
                    'datetime': post.date_utc
                })
            
            if posts_data:
                logging.info(f"Successfully fetched {len(posts_data)} posts via proxy {proxy}")
                break  # Break out of attempts loop if successful
                
        except Exception as e:
            logging.warning(f"Attempt {attempt+1} failed with proxy {proxy if 'proxy' in locals() else 'None'}: {e}")
            time.sleep(2)
            
    if not posts_data:
        logging.error("Failed to fetch posts after all proxy attempts.")
         
    return posts_data

def get_existing_wp_media(wp_url, auth):
    api_url = f"{wp_url}/wp-json/wp/v2/media"
    existing_media = []
    page = 1
    
    logging.info("Fetching existing Instagram media from WordPress...")
    while True:
        try:
            # We fetch all media and filter by caption containing 'haranginsta'
            res = requests.get(api_url, auth=auth, params={'per_page': 100, 'page': page})
            if res.status_code != 200:
                break
                
            media_items = res.json()
            if not media_items:
                break
            
            for item in media_items:
                caption_text = item.get('caption', {}).get('rendered', '')
                if 'haranginsta' in caption_text:
                    existing_media.append(item)
                    
            page += 1
        except Exception as e:
            logging.error(f"Error fetching media: {e}")
            break
            
    return existing_media

def upload_to_wp(post_data, wp_url, auth):
    try:
        # 1. Download image
        img_res = requests.get(post_data['image_url'])
        if img_res.status_code != 200:
            logging.error(f"Failed to download image for {post_data['shortcode']}")
            return False
            
        # 2. Upload to WP Media
        filename = f"{post_data['shortcode']}.jpg"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'image/jpeg'
        }
        api_url = f"{wp_url}/wp-json/wp/v2/media"
        
        upload_res = requests.post(
            api_url, 
            headers=headers, 
            data=img_res.content, 
            auth=auth
        )
        
        if upload_res.status_code not in (200, 201):
            logging.error(f"Failed to upload {filename} to WP: {upload_res.text}")
            return False
            
        media_id = upload_res.json()['id']
        
        # 3. Update Media Metadata (Caption & Title)
        update_data = {
            'title': post_data['shortcode'], # Use shortcode as title for easy matching
            'caption': 'haranginsta',       # Use haranginsta as caption flag
            'description': post_data['caption']
        }
        update_res = requests.post(f"{api_url}/{media_id}", json=update_data, auth=auth)
        
        if update_res.status_code == 200:
            logging.info(f"Successfully uploaded and cataloged {post_data['shortcode']}")
            return True
        else:
            logging.error(f"Failed to update metadata for {media_id}: {update_res.text}")
            return False
            
    except Exception as e:
        logging.error(f"Exception during upload of {post_data['shortcode']}: {e}")
        return False

def cleanup_wp_media(existing_media, wp_url, auth, keep_limit=12):
    if len(existing_media) <= keep_limit:
        logging.info(f"Total synced media is {len(existing_media)}. No cleanup needed.")
        return
        
    # Sort existing media by date (newest first)
    existing_media.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    to_delete = existing_media[keep_limit:]
    logging.info(f"Cleaning up {len(to_delete)} old media items...")
    
    for item in to_delete:
        media_id = item['id']
        try:
            res = requests.delete(f"{wp_url}/wp-json/wp/v2/media/{media_id}", params={'force': True}, auth=auth)
            if res.status_code == 200:
                logging.info(f"Deleted old media ID: {media_id}")
            else:
                logging.error(f"Failed to delete media ID {media_id}: {res.text}")
        except Exception as e:
            logging.error(f"Error deleting media ID {media_id}: {e}")

def main():
    target_account, wp_url, wp_username, wp_app_password = load_environment()
    auth = HTTPBasicAuth(wp_username, wp_app_password)
    
    # 1. Fetch from Instagram
    posts = fetch_instagram_posts(target_account, limit=12)
    if not posts:
        logging.info("No posts found or failed to fetch.")
        return
        
    logging.info(f"Fetched {len(posts)} posts from Instagram.")
    
    # 2. Fetch existing media to avoid duplicate
    existing_media = get_existing_wp_media(wp_url, auth)
    existing_shortcodes = [item['title']['rendered'] for item in existing_media]
    
    # 3. Upload new media
    for post in posts:
        if post['shortcode'] not in existing_shortcodes:
            logging.info(f"New post found: {post['shortcode']}, uploading...")
            upload_to_wp(post, wp_url, auth)
        else:
            logging.info(f"Post {post['shortcode']} already exists. Skipping.")
            
    # 4. Refetch and cleanup old media
    final_media = get_existing_wp_media(wp_url, auth)
    cleanup_wp_media(final_media, wp_url, auth, keep_limit=12)

if __name__ == "__main__":
    main()
