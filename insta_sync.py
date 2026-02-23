import os
import requests
from dotenv import load_dotenv
import logging
import time
from datetime import datetime
from requests.auth import HTTPBasicAuth

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
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    
    if not all([wp_url, wp_username, wp_app_password, rapidapi_key]):
        logging.error("Missing credentials in .env file (WordPress credentials or RAPIDAPI_KEY).")
        exit(1)
        
    return target_account, wp_url, wp_username, wp_app_password, rapidapi_key

def fetch_instagram_posts(target_account, rapidapi_key, limit=12):
    logging.info(f"Fetching posts from {target_account} using Instagram Scraper Stable API...")
    
    url = "https://instagram-scraper-stable-api.p.rapidapi.com/get_ig_user_posts.php"
    querystring = {"user_name": target_account}
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": "instagram-scraper-stable-api.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code != 200:
            logging.error(f"RapidAPI request failed: {response.status_code} - {response.text}")
            return []
            
        data = response.json()
        
        # Structure for instagram-scraper-stable-api
        items = data.get('data', {}).get('items', [])
        
        posts_data = []
        for item in items:
            if len(posts_data) >= limit:
                break
                
            code = item.get('code')
            # Extract highest quality image URL
            image_url = ''
            if item.get('image_versions2'):
                candidates = item['image_versions2'].get('candidates', [])
                if candidates:
                    image_url = candidates[0].get('url')
            if not image_url and item.get('thumbnail_url'):
                image_url = item.get('thumbnail_url')
                
            # Extract caption
            caption = ''
            caption_dict = item.get('caption')
            if caption_dict and isinstance(caption_dict, dict):
                caption = caption_dict.get('text', '')
                
            # Extract timestamp
            taken_at = item.get('taken_at')
            if taken_at:
                dt = datetime.fromtimestamp(taken_at)
                timestamp = dt.isoformat()
            else:
                dt = datetime.now()
                timestamp = dt.isoformat()
                
            if code and image_url:
                posts_data.append({
                    'shortcode': code,
                    'image_url': image_url,
                    'caption': caption,
                    'timestamp': timestamp,
                    'datetime': dt
                })
                
        if posts_data:
            logging.info(f"Successfully fetched {len(posts_data)} posts via RapidAPI")
        else:
            logging.warning("No posts found in the RapidAPI response.")
            
        return posts_data
        
    except Exception as e:
        logging.error(f"Error fetching from RapidAPI: {e}")
        return []

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
    target_account, wp_url, wp_username, wp_app_password, rapidapi_key = load_environment()
    auth = HTTPBasicAuth(wp_username, wp_app_password)
    
    # 1. Fetch from Instagram
    posts = fetch_instagram_posts(target_account, rapidapi_key, limit=12)
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
