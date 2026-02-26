"""
Selenium ile Parfüm Scraper
Gerçek browser kullanarak bot korumasını atlatır
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import json
import re
import os
import requests
import html as html_module
from typing import List, Dict, Any, Optional


class SeleniumPerfumeScraper:
    """Selenium ile parfüm scraper"""
    
    def __init__(self, headless: bool = True):
        """
        Args:
            headless: Browser'ı görünmez modda çalıştır (True önerilir)
        """
        self.headless = headless
        self.driver = None
    
    def _init_driver(self):
        """Chrome driver'ı başlat - stealth modu ile bot tespitini atlatır"""
        if self.driver:
            return
        
        print("🌐 Starting Chrome driver...")
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
        chrome_options.page_load_strategy = 'eager'
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception:
            # Fallback: let selenium-manager handle driver automatically
            self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(60)
        
        # Patch navigator.webdriver to undefined
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            '''
        })
        print("✅ Driver ready")
    
    def extract_perfume_details(self, url: str, retry: int = 2) -> Optional[Dict[str, Any]]:
        """Extract perfume details using page_source (raw HTML) for reliability"""
        self._init_driver()
        
        try:
            print(f"📡 Scraping: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
                )
            except Exception:
                print("  ⚠️ Page loading slowly, waiting...")
            
            time.sleep(3)

            # Scroll slowly to trigger Vue lazy renders
            try:
                for step in range(1, 21):
                    self.driver.execute_script(
                        f"window.scrollTo(0, document.body.scrollHeight * {step / 20});"
                    )
                    time.sleep(0.35)
                time.sleep(1.5)
                # Scroll to each vote section to ensure lazy load triggers
                for section_id in ['#voting', '#demographics', '#pyramid']:
                    self.driver.execute_script(f"""
                        var el = document.querySelector('{section_id}');
                        if (!el) el = document.getElementById('{section_id.lstrip("#")}');
                        if (el) el.scrollIntoView({{behavior: 'instant', block: 'center'}});
                    """)
                    time.sleep(1.2)
                # Final scroll back to top then bottom to ensure full render
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(0.5)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
            except Exception:
                pass

            # Get raw HTML - this is always reliable
            page_source = self.driver.page_source
            
            # Check for Cloudflare / 429 block page
            if len(page_source) < 5000 or '429 Too Many Requests' in page_source or 'you\'ve opened more pages' in page_source:
                raise Exception("Page source too short, page may not have loaded")
            
            perfume_data = {
                'url': url,
                'name': None,
                'brand': None,
                'release_year': None,
                'gender': None,
                'top_notes': [],
                'middle_notes': [],
                'base_notes': [],
                'rating': None,
                'votes': None,
                'description': None,
                'image_url': None,
                'main_accords': [],
                'note_images': {},
                'longevity': None,
                'sillage': None,
                'price_value': None,
                'season': None,
            }
            
            # === ALL EXTRACTION FROM page_source (raw HTML) ===
            
            # Name + Gender from img alt="perfume Aventus Creed for men"
            # This is the most reliable source
            img_alt_match = re.search(r'alt="perfume\s+([^"]+)"', page_source, re.IGNORECASE)
            if img_alt_match:
                full_title = html_module.unescape(img_alt_match.group(1).strip())
            else:
                # Fallback: h1 tag (strip inner HTML tags)
                h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', page_source, re.DOTALL | re.IGNORECASE)
                if h1_match:
                    full_title = re.sub(r'<[^>]+>', ' ', h1_match.group(1)).strip()
                    full_title = re.sub(r'\s+', ' ', full_title)
                else:
                    full_title = None
            
            if full_title:
                if 'for women and men' in full_title.lower():
                    perfume_data['gender'] = 'Unisex'
                    clean_name = re.sub(r'\s*for women and men\s*', '', full_title, flags=re.IGNORECASE)
                elif 'for women' in full_title.lower():
                    perfume_data['gender'] = 'Women'
                    clean_name = re.sub(r'\s*for women\s*', '', full_title, flags=re.IGNORECASE)
                elif 'for men' in full_title.lower():
                    perfume_data['gender'] = 'Men'
                    clean_name = re.sub(r'\s*for men\s*', '', full_title, flags=re.IGNORECASE)
                else:
                    clean_name = full_title
                
                perfume_data['name'] = html_module.unescape(clean_name.strip())
            
            # Brand from <span itemprop="name">
            brand_match = re.search(r'itemprop="name"[^>]*>\s*([^<]+?)\s*</span>', page_source, re.IGNORECASE)
            if brand_match:
                perfume_data['brand'] = html_module.unescape(brand_match.group(1).strip())
            
            # Description from itemprop="description" - via JS for full text
            desc_text = ''
            try:
                desc_text = self.driver.execute_script("""
                    var el = document.querySelector('[itemprop="description"]');
                    return el ? el.innerText.trim() : '';
                """)
            except Exception:
                pass
            if not desc_text:
                # Fallback: regex but greedy, strip all tags, no char limit
                desc_match = re.search(r'itemprop="description"[^>]*>(.*?)</(?:div|section|article)>', page_source, re.DOTALL | re.IGNORECASE)
                if desc_match:
                    desc_text = html_module.unescape(re.sub(r'<[^>]+>', ' ', desc_match.group(1))).strip()
                    desc_text = re.sub(r'\s+', ' ', desc_text).strip()
            if desc_text and len(desc_text) > 30:
                perfume_data['description'] = html_module.unescape(desc_text)

                # Release year from description
                year_match = re.search(r'launched in (\d{4})', desc_text, re.IGNORECASE)
                if not year_match:
                    year_match = re.search(r'released in (\d{4})', desc_text, re.IGNORECASE)
                if year_match:
                    year = int(year_match.group(1))
                    if 1900 <= year <= 2030:
                        perfume_data['release_year'] = year

                # Notes from description text
                top_match = re.search(r'Top notes?\s+(?:are|is)\s+([^;.]+?)(?:;|\.)', desc_text, re.IGNORECASE)
                if top_match:
                    notes_text = top_match.group(1)
                    notes = re.split(r',\s*(?:and\s+)?|\s+and\s+', notes_text)
                    perfume_data['top_notes'] = [n.strip() for n in notes if n.strip() and len(n.strip()) > 1]

                middle_match = re.search(r'middle notes?\s+(?:are|is)\s+([^;.]+?)(?:;|\.)', desc_text, re.IGNORECASE)
                if middle_match:
                    notes_text = middle_match.group(1)
                    notes = re.split(r',\s*(?:and\s+)?|\s+and\s+', notes_text)
                    perfume_data['middle_notes'] = [n.strip() for n in notes if n.strip() and len(n.strip()) > 1]

                base_match = re.search(r'base notes?\s+(?:are|is)\s+([^;.]+?)(?:\.|$)', desc_text, re.IGNORECASE)
                if base_match:
                    notes_text = base_match.group(1)
                    notes = re.split(r',\s*(?:and\s+)?|\s+and\s+', notes_text)
                    perfume_data['base_notes'] = [n.strip() for n in notes if n.strip() and len(n.strip()) > 1]
            
            # Fallback notes + note_images: extract from pyramid via JS
            try:
                js_notes = self.driver.execute_script("""
                    var pyramid = document.getElementById('pyramid');
                    if (!pyramid) return {top: [], middle: [], base: [], all: [], images: {}};
                    var output = {top: [], middle: [], base: [], all: [], images: {}};
                    pyramid.querySelectorAll('img').forEach(function(img) {
                        if (img.alt && img.alt.trim()) output.all.push(img.alt.trim());
                    });
                    var currentSection = null;
                    pyramid.querySelectorAll('*').forEach(function(el) {
                        if (el.children.length === 0) {
                            var txt = (el.textContent || '').trim().toUpperCase();
                            if (txt === 'TOP NOTES' || txt === 'TOP NOTE') currentSection = 'top';
                            else if (txt === 'MIDDLE NOTES' || txt === 'MIDDLE NOTE' || txt === 'HEART NOTES') currentSection = 'middle';
                            else if (txt === 'BASE NOTES' || txt === 'BASE NOTE') currentSection = 'base';
                        }
                        if (el.tagName === 'IMG' && el.alt && currentSection) {
                            output[currentSection].push(el.alt.trim());
                        }
                        if (el.tagName === 'IMG' && el.alt && el.src && el.src.indexOf('fimgs.net') !== -1) {
                            output.images[el.alt.trim()] = el.src;
                        }
                    });
                    return output;
                """)
                if js_notes:
                    if not perfume_data['top_notes'] and not perfume_data['middle_notes'] and not perfume_data['base_notes']:
                        if js_notes.get('top') or js_notes.get('middle') or js_notes.get('base'):
                            perfume_data['top_notes'] = list(dict.fromkeys(js_notes['top']))
                            perfume_data['middle_notes'] = list(dict.fromkeys(js_notes['middle']))
                            perfume_data['base_notes'] = list(dict.fromkeys(js_notes['base']))
                        elif js_notes.get('all'):
                            perfume_data['top_notes'] = list(dict.fromkeys(js_notes['all']))
                    if js_notes.get('images'):
                        perfume_data['note_images'] = js_notes['images']
            except Exception:
                pass

            # Main accords: find 'main accords' heading then extract truncate spans
            try:
                idx = page_source.lower().find('main accords')
                if idx > 0:
                    chunk = page_source[idx:idx+4000]
                    accords = re.findall(
                        r'<span[^>]*class="[^"]*truncate[^"]*"[^>]*>([^<]{2,40})</span>',
                        chunk
                    )
                    if accords:
                        perfume_data['main_accords'] = list(dict.fromkeys(a.strip() for a in accords if a.strip()))[:12]
            except Exception:
                pass
            
            # Vote data via JS DOM - scroll to each section first
            def _parse_vote_count(s):
                s = str(s).strip().lower().replace(',', '').replace(' ', '')
                if s.endswith('k') and len(s) > 1:
                    try:
                        return int(float(s[:-1]) * 1000)
                    except (ValueError, TypeError):
                        return None
                if s.endswith('m') and len(s) > 1:
                    try:
                        return int(float(s[:-1]) * 1000000)
                    except (ValueError, TypeError):
                        return None
                try:
                    return int(float(s))
                except (ValueError, TypeError):
                    return None

            def _extract_section_by_heading(heading_text):
                """Find heading span (UPPERCASE), scroll to it, get box innerText, parse label/count pairs."""
                try:
                    ht_upper = heading_text.upper()
                    # Target spans with 'uppercase' or 'tw-rating-card-label' CSS class
                    # to avoid matching review text that also contains the same word
                    self.driver.execute_script(f"""
                        var els = document.querySelectorAll('span,div,p');
                        for (var i=0; i<els.length; i++) {{
                            var cl = (els[i].className||'').toLowerCase();
                            var isVoteHeading = cl.indexOf('uppercase') >= 0 || cl.indexOf('tw-rating-card-label') >= 0;
                            if (els[i].children.length === 0 &&
                                els[i].textContent.trim().toUpperCase() === '{ht_upper}' &&
                                isVoteHeading) {{
                                els[i].scrollIntoView({{behavior:'instant',block:'center'}});
                                break;
                            }}
                        }}
                    """)
                    time.sleep(2.5)
                    inner = self.driver.execute_script(f"""
                        var heading = null;
                        var els = document.querySelectorAll('span,div,p');
                        for (var i=0; i<els.length; i++) {{
                            var cl = (els[i].className||'').toLowerCase();
                            var isVoteHeading = cl.indexOf('uppercase') >= 0 || cl.indexOf('tw-rating-card-label') >= 0;
                            if (els[i].children.length === 0 &&
                                els[i].textContent.trim().toUpperCase() === '{ht_upper}' &&
                                isVoteHeading) {{
                                heading = els[i];
                                break;
                            }}
                        }}
                        if (!heading) return null;
                        var box = heading;
                        for (var j=0; j<8; j++) {{
                            box = box.parentElement;
                            if (!box) break;
                            var t = (box.innerText||'');
                            if (t.split('\\n').length > 2) return t;
                        }}
                        return null;
                    """)
                    if not inner:
                        return None
                    # Known section headings - stop parsing when we hit a different one
                    section_headings = {'LONGEVITY', 'SILLAGE', 'PRICE VALUE', 'SEASON',
                                        'WHEN TO WEAR', 'GENDER', 'AGE'}
                    lines = [l.strip() for l in inner.split('\n') if l.strip()]
                    # Find the start of our heading, then stop at the next different heading
                    ht_upper = heading_text.upper()
                    started = False
                    filtered = []
                    for line in lines:
                        lu = line.upper()
                        if lu == ht_upper:
                            started = True
                            continue  # skip the heading itself
                        if started and lu in section_headings and lu != ht_upper:
                            break  # stop at next section
                        if started:
                            filtered.append(line)
                    skip_vals = {'NO VOTE', 'SHOW VOTES', 'HIDE LABELS', 'SHOW ALL'}
                    result = {}
                    prev_label = None
                    for line in filtered:
                        if line.upper() in skip_vals:
                            continue
                        val = _parse_vote_count(line)
                        if val and val > 0 and prev_label:
                            result[prev_label.lower().replace(' ', '_')] = val
                            prev_label = None
                        elif not (line[0].isdigit() or line[0] in '.'):
                            prev_label = line
                    return result if result else None
                except Exception:
                    return None

            for section, field in [('LONGEVITY', 'longevity'), ('SILLAGE', 'sillage'), ('PRICE VALUE', 'price_value')]:
                parsed = _extract_section_by_heading(section)
                if parsed:
                    perfume_data[field] = parsed

            # Season / When to Wear - same approach
            try:
                season_raw = _extract_section_by_heading('WHEN TO WEAR')
                if not season_raw:
                    season_raw = _extract_section_by_heading('SEASON')
                if season_raw:
                    seasons_valid = {'winter', 'spring', 'summer', 'fall', 'day', 'night'}
                    filtered = {k: v for k, v in season_raw.items() if k in seasons_valid}
                    if filtered:
                        perfume_data['season'] = filtered
            except Exception:
                pass


            # Rating
            rating_match = re.search(r'itemprop="ratingValue"[^>]*>([^<]+)<', page_source, re.IGNORECASE)
            if rating_match:
                try:
                    perfume_data['rating'] = float(rating_match.group(1).strip())
                except ValueError:
                    pass
            
            # Votes
            votes_match = re.search(r'itemprop="ratingCount"[^>]*>([^<]+)<', page_source, re.IGNORECASE)
            if votes_match:
                try:
                    perfume_data['votes'] = int(votes_match.group(1).strip().replace(',', '').replace('.', ''))
                except ValueError:
                    pass
            
            
            # Image
            img_match = re.search(r'itemprop="image"[^>]*src="([^"]+)"', page_source, re.IGNORECASE)
            if not img_match:
                img_match = re.search(r'src="([^"]*fimgs\.net[^"]*perfume[^"]*)"', page_source, re.IGNORECASE)
            if img_match:
                perfume_data['image_url'] = img_match.group(1)
            
            # Completeness check
            missing_fields = []
            if not perfume_data.get('name'):
                missing_fields.append('name')
            if not perfume_data.get('brand'):
                missing_fields.append('brand')
            if not perfume_data.get('top_notes') and not perfume_data.get('middle_notes') and not perfume_data.get('base_notes'):
                missing_fields.append('notes')
            if not perfume_data.get('description'):
                missing_fields.append('description')
            if not perfume_data.get('rating'):
                missing_fields.append('rating')
            
            # Clean brand name from perfume name
            brand = perfume_data.get('brand', '')
            name = perfume_data.get('name', '')
            if brand and name and name.endswith(' ' + brand):
                perfume_data['name'] = name[:-(len(brand) + 1)].strip()
            elif brand and name and name.startswith(brand + ' '):
                # e.g. "Dior Homme Intense 2011 Dior" -> already handled above
                # but "Dior Homme Parfum" starts with brand - don't strip if it's part of product line
                pass
            
            if missing_fields:
                print(f"⚠️ {perfume_data.get('name', 'Unknown')} - Missing: {', '.join(missing_fields)}")
            else:
                print(f"✅ {perfume_data.get('name', 'N/A')} - {perfume_data.get('brand', 'N/A')} [Complete]")
            
            return perfume_data
            
        except Exception as e:
            error_msg = str(e)
            if retry > 0:
                # Longer wait on retry - likely rate limited
                wait_time = 30 if 'too short' in error_msg else 5
                print(f"⚠️ Error, retrying ({retry} left, waiting {wait_time}s): {error_msg[:100]}")
                time.sleep(wait_time)
                # Restart driver on retry
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
                return self.extract_perfume_details(url, retry - 1)
            
            print(f"❌ Error: {error_msg[:200]}")
            return None
    
    def get_brand_perfume_urls(self, brand_name: str, limit: int = 10) -> List[str]:
        """
        Marka sayfasından EN POPÜLER parfüm URL'lerini çek
        
        Args:
            brand_name: Marka adı (örn: "Dior", "Versace")
            limit: Kaç parfüm URL'i çekileceği
        
        Returns:
            Parfüm URL'leri listesi (popülerlik sırasına göre)
        """
        self._init_driver()
        
        # Marka adını URL formatına çevir
        brand_url_overrides = {
            'Bath & Body Works': 'Bath-Body-Works',
            'Dolce&Gabbana': 'Dolce-Gabbana',
            'PARIS CORNER': 'Paris-Corner',
        }
        formatted_brand = brand_url_overrides.get(brand_name, brand_name.replace(' ', '-').replace('&', ''))
        brand_url = f"https://www.fragrantica.com/designers/{formatted_brand}.html#popular"
        
        print(f"🔍 Searching for MOST POPULAR perfumes from {brand_name}...")
        print(f"📡 Brand page: {brand_url}")
        
        try:
            self.driver.get(brand_url)
            
            # Popüler parfümler yüklensin
            time.sleep(5)
            
            # Popüler parfüm kartlarını bul - daha spesifik selector
            # Önce popüler bölümü bekle
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.cell"))
                )
            except Exception:
                print("  ⚠️ Loading popular section...")
            
            # Parfüm linklerini bul - sadece geçerli parfüm sayfaları
            all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/perfume/']")
            
            perfume_urls = []
            seen_names = set()  # Duplicate kontrolü için
            
            for link in all_links:
                href = link.get_attribute('href')
                
                # Geçerli parfüm URL'i kontrolü
                if href and '/perfume/' in href and href.endswith('.html'):
                    # Aynı parfümün farklı linklerini atla
                    perfume_name = href.split('/')[-1]
                    if perfume_name not in seen_names:
                        seen_names.add(perfume_name)
                        perfume_urls.append(href)
                        print(f"  ✓ Bulundu ({len(perfume_urls)}): {perfume_name}")
                        
                        if len(perfume_urls) >= limit:
                            break
            
            print(f"✅ Found {len(perfume_urls)} popular perfume URLs")
            return perfume_urls[:limit]
            
        except Exception as e:
            print(f"❌ Brand page error: {str(e)[:200]}")
            return []
    
    def scrape_brand(self, brand_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Bir markanın parfümlerini çek
        
        Args:
            brand_name: Marka adı
            limit: Kaç parfüm çekileceği
        
        Returns:
            Parfüm verileri listesi
        """
        print(f"\n{'='*60}")
        print(f"🏷️  {brand_name.upper()} BRAND")
        print(f"{'='*60}")
        
        # Marka sayfasından URL'leri al
        urls = self.get_brand_perfume_urls(brand_name, limit)
        
        if not urls:
            print(f"⚠️ No perfumes found for {brand_name}")
            return []
        
        # URL'lerden verileri çek
        return self.scrape_multiple(urls)
    
    def scrape_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Birden fazla URL'den veri çek"""
        perfumes = []
        consecutive_failures = 0
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}]")
            
            # If we hit too many consecutive failures, we're likely rate-limited
            if consecutive_failures >= 3:
                print(f"⏳ Rate limit detected, cooling down 120s...")
                time.sleep(120)
                # Restart driver after cooldown
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
                consecutive_failures = 0
            
            perfume_data = self.extract_perfume_details(url)
            if perfume_data:
                perfumes.append(perfume_data)
                consecutive_failures = 0
            else:
                consecutive_failures += 1
            
            # Random delay between pages - mimics human behaviour
            if i < len(urls):
                time.sleep(random.uniform(8, 15))
        
        return perfumes
    
    def save_to_json(self, perfumes: List[Dict[str, Any]], filename: str = "parfumler_selenium.json"):
        """JSON'a kaydet"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(perfumes, f, ensure_ascii=False, indent=2)
            print(f"\n💾 {len(perfumes)} perfumes saved to '{filename}'")
        except Exception as e:
            print(f"❌ Save error: {str(e)}")
    
    def download_image(self, image_url: str, save_path: str) -> bool:
        """Download perfume image and save as .png"""
        try:
            if not image_url:
                return False
            response = requests.get(image_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
            })
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception:
            pass
        return False
    
    def close(self):
        """Driver'ı kapat"""
        if self.driver:
            self.driver.quit()
            print("\n🔒 Browser closed")


def main():
    """Marka bazlı parfüm scraping"""
    
    # Popüler markalar ve her birinden kaç parfüm çekileceği
    brands = {
        "Dior": 10,
        "Versace": 10,
        "Montblanc": 10,
        "Jean Paul Gaultier": 10,
        "Yves Saint Laurent": 10,
        "Hugo Boss": 10,
    }
    
    print("🚀 Marka Bazlı Parfüm Scraper")
    print("="*60)
    print(f"📋 {len(brands)} marka, toplam ~{sum(brands.values())} parfüm çekilecek")
    print("⚠️  Headless modda çalışıyor (arka planda)")
    print("="*60)
    
    scraper = SeleniumPerfumeScraper(headless=True)
    all_perfumes = []
    
    try:
        for brand_name, limit in brands.items():
            # Her marka için parfümleri çek
            brand_perfumes = scraper.scrape_brand(brand_name, limit)
            all_perfumes.extend(brand_perfumes)
            
            print(f"\n✅ {brand_name}: {len(brand_perfumes)} parfüm çekildi")
            print(f"📊 Toplam: {len(all_perfumes)} parfüm\n")
        
        # Genel özet
        print("\n" + "="*60)
        print(f"📊 GENEL ÖZET")
        print("="*60)
        print(f"Toplam Parfüm: {len(all_perfumes)}")
        
        # Marka bazlı istatistik
        brand_counts = {}
        for perfume in all_perfumes:
            brand = perfume.get('marka', 'Bilinmeyen')
            brand_counts[brand] = brand_counts.get(brand, 0) + 1
        
        print("\nMarka Bazlı Dağılım:")
        for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {brand}: {count} parfüm")
        
        # En yüksek puanlı parfümler
        rated_perfumes = [p for p in all_perfumes if p.get('puan')]
        if rated_perfumes:
            top_rated = sorted(rated_perfumes, key=lambda x: x.get('puan', 0), reverse=True)[:5]
            print("\n🏆 En Yüksek Puanlı 5 Parfüm:")
            for i, perfume in enumerate(top_rated, 1):
                print(f"  {i}. {perfume.get('isim', 'N/A')} - {perfume.get('puan', 'N/A')}/5")
        
        # JSON'a kaydet
        if all_perfumes:
            filename = "markalar_parfumler.json"
            scraper.save_to_json(all_perfumes, filename)
        
        print("\n✅ İşlem tamamlandı!")
        
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
