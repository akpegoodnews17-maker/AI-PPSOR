import pandas as pd
import numpy as np
import os

BODY_TYPE_STYLE_MAP = {
    'hourglass': ['high-waisted', 'wrap', 'fit and flare', 'bodycon', 'belted', 'structured', 'tailored'],
    'rectangle': ['layered', 'ruffle', 'peplum', 'asymmetric', 'volume', 'textured', 'statement sleeves', 'blazer'],
    'apple': ['empire waist', 'tunic', 'v-neck', 'draped', 'flowy', 'shift', 'wrap', 'soft fabric'],
    'pear': ['a-line', 'wide-leg', 'high-waisted', 'fit and flare', 'balance', 'structured top', 'printed top'],
    'inverted triangle': ['wide-leg', 'a-line', 'simple top', 'v-neck', 'soft shoulder', 'lightweight top'],
    'triangle': ['structured top', 'boat neck', 'statement sleeves', 'tailored top', 'straight-leg']
}

SKIN_TONE_COLOR_MAP = {
    'warm': ['beige', 'brown', 'olive', 'mustard', 'rust', 'cream', 'gold', 'peach', 'copper', 'bronze'],
    'cool': ['navy', 'black', 'grey', 'plum', 'berry', 'emerald', 'silver', 'ice', 'lavender'],
    'neutral': ['white', 'black', 'beige', 'navy', 'olive', 'grey', 'burgundy', 'cream']
}

SEASON_BOOST_KEYWORDS = {
    'winter': ['jacket', 'coat', 'wool', 'knit', 'turtleneck', 'layer', 'sweater', 'flannel', 'fleece'],
    'summer': ['linen', 'shorts', 'sleeveless', 'tank', 'sun', 'breathable', 'lightweight', 'cotton', 'crochet'],
    'spring': ['light jacket', 'cardigan', 'floral', 'pastel', 'rain', 'breeze', 'chiffon', 'lace'],
    'fall': ['leather', 'suede', 'plaid', 'sweater', 'scarf', 'boot', 'denim', 'layer', 'corduroy']
}

DEFAULT_VISUAL_K = 20

class FashionRecommender:
    def __init__(self, styles_file, images_file):
        self.styles_file = styles_file
        self.images_file = images_file
        self.df_styles = pd.read_csv(styles_file, on_bad_lines='skip')
        self.df_images = pd.read_csv(images_file, on_bad_lines='skip')
        self.visual_recommender = None
        self.visual_scores = {}
        self._preprocess_data()

    def _preprocess_data(self):
        self.df_images[['id', 'image_format']] = self.df_images['filename'].str.extract(r'(\d+)\.(\w+)', expand=True)
        self.df_images = self.df_images[['id', 'link']]
        self.df_styles['id'] = self.df_styles['id'].astype(str)
        self.df_images['id'] = self.df_images['id'].astype(str)
        self.df_merged = pd.merge(self.df_styles, self.df_images, on='id', how='left')

        for col in ['productDisplayName', 'articleType', 'baseColour', 'season', 'gender', 'usage', 'description']:
            if col in self.df_merged.columns:
                self.df_merged[col] = self.df_merged[col].fillna('').astype(str)
            else:
                self.df_merged[col] = ''

        self.df_merged['productDisplayName_lower'] = self.df_merged['productDisplayName'].str.lower()
        self.df_merged['articleType_lower'] = self.df_merged['articleType'].str.lower()
        self.df_merged['baseColour_lower'] = self.df_merged['baseColour'].str.lower()
        self.df_merged['season_lower'] = self.df_merged['season'].str.lower()
        self.df_merged['gender_lower'] = self.df_merged['gender'].str.lower()
        self.df_merged['usage_lower'] = self.df_merged['usage'].str.lower()
        self.df_merged['description_lower'] = self.df_merged['description'].str.lower()

    def _lazy_load_visual_recommender(self):
        if self.visual_recommender is None:
            try:
                from app.image_based.cli_recommender import FashionRecommenderCLI
                self.visual_recommender = FashionRecommenderCLI()
            except Exception as e:
                self.visual_recommender = None
                print(f"Visual recommender unavailable: {e}")

    def _get_visual_similarity_scores(self, wardrobe_img_path, top_k=DEFAULT_VISUAL_K):
        self._lazy_load_visual_recommender()
        if not self.visual_recommender or not wardrobe_img_path or not os.path.exists(wardrobe_img_path):
            return {}

        try:
            features = self.visual_recommender.extract_features(wardrobe_img_path)
            distances, indices = self.visual_recommender.find_similar_items(features, k=top_k + 1)
            scores = {}
            for dist, idx in zip(distances[0][1:], indices[0][1:]):
                filename = os.path.basename(self.visual_recommender.filenames[idx])
                info = self.visual_recommender.get_product_info(filename)
                item_id = str(info.get('id', ''))
                if item_id:
                    scores[item_id] = 1.0 / (1.0 + float(dist))
            return scores
        except Exception as e:
            print(f"Visual similarity scoring failed: {e}")
            return {}

    def _score_body_type(self, row, body_type):
        if not body_type:
            return 0.0
        body_type = body_type.strip().lower()
        keywords = BODY_TYPE_STYLE_MAP.get(body_type, [])
        if not keywords:
            return 0.0

        text = ' '.join([
            row['articleType_lower'],
            row['productDisplayName_lower'],
            row['usage_lower'],
            row['description_lower']
        ])
        matches = sum(1 for keyword in keywords if keyword in text)
        return min(1.0, matches / max(1, len(keywords)))

    def _score_skin_tone(self, row, skin_color):
        if not skin_color:
            return 0.0
        tone = skin_color.strip().lower()
        palette = SKIN_TONE_COLOR_MAP.get(tone)
        if palette is None:
            return 0.0
        text = ' '.join([row['baseColour_lower'], row['productDisplayName_lower'], row['articleType_lower']])
        matches = sum(1 for color in palette if color in text)
        return min(1.0, matches / max(1, len(palette)))

    def _score_season(self, row, season):
        if not season:
            return 0.0
        season_key = season.strip().lower()
        score = 0.0
        if row['season_lower'] == season_key:
            score += 0.6
        text = ' '.join([
            row['productDisplayName_lower'],
            row['articleType_lower'],
            row['description_lower'],
            row['usage_lower']
        ])
        keywords = SEASON_BOOST_KEYWORDS.get(season_key, [])
        if keywords:
            keyword_matches = sum(1 for keyword in keywords if keyword in text)
            score += min(0.4, keyword_matches / max(1, len(keywords)))
        return min(1.0, score)

    def _score_visual(self, row):
        item_id = str(row['id'])
        return float(self.visual_scores.get(item_id, 0.0))

    def _compute_scores(self, filters):
        df = self.df_merged.copy()

        if filters.get('gender'):
            df = df[df['gender_lower'] == filters['gender'].strip().lower()]

        self.visual_scores = self._get_visual_similarity_scores(filters.get('wardrobe_img'))

        df['body_score'] = df.apply(lambda r: self._score_body_type(r, filters.get('bodyType')), axis=1)
        df['season_score'] = df.apply(lambda r: self._score_season(r, filters.get('season')), axis=1)
        df['visual_score'] = df.apply(self._score_visual, axis=1)
        df['skin_score'] = df.apply(lambda r: self._score_skin_tone(r, filters.get('skin_color')), axis=1)

        df['final_score'] = (
            df['body_score'] * 0.30 +
            df['season_score'] * 0.30 +
            df['visual_score'] * 0.20 +
            df['skin_score'] * 0.20
        )

        if filters.get('preferredFabrics'):
            fabric_keywords = [fabric.strip().lower() for fabric in filters['preferredFabrics']]
            df['fabric_bonus'] = df['productDisplayName_lower'].apply(
                lambda txt: sum(1 for kw in fabric_keywords if kw in txt) / max(1, len(fabric_keywords))
            ) * 0.05
            df['final_score'] += df['fabric_bonus']

        if filters.get('preferredStyles'):
            style_keywords = [style.strip().lower() for style in filters['preferredStyles']]
            df['style_bonus'] = df[['productDisplayName_lower', 'articleType_lower', 'usage_lower']].apply(
                lambda row: sum(1 for kw in style_keywords if kw in ' '.join(row)) / max(1, len(style_keywords)), axis=1
            ) * 0.05
            df['final_score'] += df['style_bonus']

        if filters.get('baseColour'):
            preferred_colors = [c.strip().lower() for c in filters['baseColour'] if c.strip()]
            df['color_bonus'] = df['baseColour_lower'].apply(
                lambda col: 0.5 if col in preferred_colors else 0.0
            )
            df['final_score'] += df['color_bonus']

        df = df.sort_values(by='final_score', ascending=False).reset_index(drop=True)
        return df

    def get_filtered_data(self, filters):
        return self._compute_scores(filters)

    def create_category_dict(self, filtered_data):
        category_order = ["Apparel", "Accessories", "Footwear", "Personal Care", "Free Items", "Sporting Goods", "Home"]
        category_dict = {category: [] for category in category_order}

        for _, row in filtered_data.iterrows():
            category = row.get('masterCategory', 'Home')
            if category in category_dict:
                product_details = {
                    'articleType': row.get('articleType', ''),
                    'productDisplayName': row.get('productDisplayName', ''),
                    'imageLink': row.get('link', ''),
                    'price': row.get('price_usd', 0),
                    'price_del': row.get('discounted_price_usd', 0),
                    'prediction_score': round(float(row.get('final_score', 0.0)), 4)
                }
                category_dict[category].append(product_details)
        return category_dict

    def display_products(self, category_dict):
        count = 0
        for category in ["Apparel", "Accessories", "Footwear", "Personal Care", "Free Items", "Sporting Goods", "Home"]:
            if category in category_dict and category_dict[category]:
                print(f"\nCategory: {category}")
                for product in category_dict[category]:
                    print(f"Article Type: {product['articleType']}")
                    print(f"Product Display Name: {product['productDisplayName']}")
                    print(f"Prediction Score: {product.get('prediction_score', 0.0)}")
                    print(f"Image Link: {product['imageLink']}")
                    print("-" * 50)
                    count += 1
                print(f"Displayed {len(category_dict[category])} products for category: {category}")
        print(f"Total products displayed: {count}")


def recommend_fashion(gender=None, baseColour=None, preferredFabrics=None, preferredStyles=None,
                      occasionTypes=None, styleGoals=None, bodyType=None, skin_color=None,
                      season=None, wardrobe_img=None):
    filters = {
        'gender': gender if gender else None,
        'baseColour': baseColour if baseColour and baseColour != [''] else None,
        'preferredFabrics': preferredFabrics if preferredFabrics and preferredFabrics != [''] else None,
        'preferredStyles': preferredStyles if preferredStyles and preferredStyles != [''] else None,
        'occasionTypes': occasionTypes if occasionTypes and occasionTypes != [''] else None,
        'styleGoals': styleGoals if styleGoals and styleGoals != [''] else None,
        'bodyType': bodyType if bodyType else None,
        'skin_color': skin_color if skin_color else None,
        'season': season if season else None,
        'wardrobe_img': wardrobe_img if wardrobe_img else None
    }

    recommender = FashionRecommender('data/fashion-dataset/styles.csv', 'data/fashion-dataset/images.csv')
    filtered_data = recommender.get_filtered_data(filters)
    category_dict = recommender.create_category_dict(filtered_data)
    recommender.display_products(category_dict)
    return category_dict
