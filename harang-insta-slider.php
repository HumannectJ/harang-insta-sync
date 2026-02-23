<?php
/**
 * Plugin Name: Harang Instagram Slider
 * Description: A shortcode plugin to display Instagram media synced via Python script.
 * Version: 1.0.0
 * Author: Studio Yoorang
 */

if (!defined('ABSPATH')) {
    exit; // Exit if accessed directly.
}

// Enqueue styles and scripts for Swiper
function harang_insta_slider_enqueue_assets() {
    global $post;
    if (is_a($post, 'WP_Post') && has_shortcode($post->post_content, 'harang_insta_slider')) {
        wp_enqueue_style('swiper-bundle-css', 'https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css', array(), '11.0.0');
        wp_enqueue_script('swiper-bundle-js', 'https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js', array(), '11.0.0', true);
    }
}
add_action('wp_enqueue_scripts', 'harang_insta_slider_enqueue_assets');

// Shortcode function
function harang_insta_slider_shortcode($atts) {
    $atts = shortcode_atts(array(
        'limit' => 12
    ), $atts, 'harang_insta_slider');

    // Query media items. The Python script sets 'caption' (which maps to post_excerpt in WP media)
    // as 'haranginsta'. We can query attachments and filter them.
    $args = array(
        'post_type'      => 'attachment',
        'post_mime_type' => 'image',
        'post_status'    => 'inherit',
        'posts_per_page' => 50, // Fetch up to 50 recently uploaded images to filter
        'orderby'        => 'date',
        'order'          => 'DESC',
    );
    
    $query = new WP_Query($args);
    $valid_images = array();
    
    if ($query->have_posts()) {
        foreach ($query->posts as $attachment) {
            // Check if caption contains 'haranginsta'
            if (strpos($attachment->post_excerpt, 'haranginsta') !== false) {
                $valid_images[] = $attachment;
                if (count($valid_images) >= intval($atts['limit'])) {
                    break;
                }
            }
        }
    }
    
    if (empty($valid_images)) {
        return '<p style="text-align:center;">인스타그램 이미지가 없습니다.</p>';
    }

    ob_start();
    ?>
    <style>
        .harang-insta-container {
            width: 100%;
            overflow: hidden;
            margin: 20px 0;
            position: relative;
        }
        .swiper-slide.insta-slide {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px;
            box-sizing: border-box;
        }
        .insta-slide a {
            display: block;
            width: 100%;
            position: relative;
            overflow: hidden;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .insta-slide img {
            width: 100%;
            height: auto;
            object-fit: cover;
            aspect-ratio: 1/1;
            transition: transform 0.4s ease;
            display: block;
        }
        .insta-slide a:hover img {
            transform: scale(1.05);
        }
        /* Instagram icon overlay */
        .insta-slide .overlay {
            position: absolute;
            top:0; left:0; width:100%; height:100%;
            background: rgba(0,0,0,0.3);
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .insta-slide a:hover .overlay {
            opacity: 1;
        }
        .insta-slide .overlay svg {
            width: 40px; height: 40px; fill: white;
        }
        .harang-insta-container .swiper-pagination {
            position: relative;
            margin-top: 15px;
        }
        /* Make nav buttons smaller and more elegant */
        .harang-insta-container .swiper-button-next,
        .harang-insta-container .swiper-button-prev {
            color: #fff;
            background: rgba(0,0,0,0.5);
            width: 36px;
            height: 36px;
            border-radius: 50%;
            transform: scale(0.7);
        }
        .harang-insta-container .swiper-button-next::after,
        .harang-insta-container .swiper-button-prev::after {
            font-size: 16px;
            font-weight: bold;
        }
    </style>

    <div class="harang-insta-container swiper mySwiperInsta">
        <div class="swiper-wrapper">
            <?php foreach ($valid_images as $img): 
                $img_url = wp_get_attachment_image_url($img->ID, 'large');
                $shortcode = $img->post_title; // Python script sets 'title' to the shortcode
                $orig_caption = $img->post_content; // Python script sets 'description' which maps to post_content in WP Attachment
                $link = "https://www.instagram.com/p/" . esc_attr($shortcode) . "/";
            ?>
                <div class="swiper-slide insta-slide">
                    <a href="<?php echo esc_url($link); ?>" target="_blank" rel="noopener noreferrer">
                        <img src="<?php echo esc_url($img_url); ?>" alt="<?php echo esc_attr($orig_caption); ?>" loading="lazy" />
                        <div class="overlay">
                            <svg viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.07zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
                        </div>
                    </a>
                </div>
            <?php endforeach; ?>
        </div>
        <div class="swiper-pagination"></div>
        <div class="swiper-button-next"></div>
        <div class="swiper-button-prev"></div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            if (typeof Swiper !== 'undefined') {
                new Swiper('.mySwiperInsta', {
                    slidesPerView: 1,
                    spaceBetween: 10,
                    loop: false,
                    pagination: {
                        el: ".swiper-pagination",
                        clickable: true,
                    },
                    navigation: {
                        nextEl: '.swiper-button-next',
                        prevEl: '.swiper-button-prev',
                    },
                    breakpoints: {
                        480: { slidesPerView: 2, spaceBetween: 15 },
                        768: { slidesPerView: 3, spaceBetween: 20 },
                        1024: { slidesPerView: 4, spaceBetween: 20 },
                    }
                });
            }
        });
    </script>
    <?php
    return ob_get_clean();
}
add_shortcode('harang_insta_slider', 'harang_insta_slider_shortcode');
