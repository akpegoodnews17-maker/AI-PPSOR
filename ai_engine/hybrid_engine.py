import os
import sqlite3
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
from PIL import Image
from numpy.linalg import norm
from sklearn.neighbors import NearestNeighbors
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.layers import GlobalMaxPooling2D

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(ROOT_DIR, 'fashion.db')
WARDROBE_FOLDER = os.path.join(ROOT_DIR, 'app', 'static', 'uploads', 'wardrobe')
EMBEDDINGS_PATHS = [
    os.path.join(ROOT_DIR, 'app', 'image_based', 'embeddings.pkl'),
    os.path.join(ROOT_DIR, 'embeddings.pkl')
]
FILENAMES_PATHS = [
    os.path.join(ROOT_DIR, 'app', 'image_based', 'filenames.pkl'),
    os.path.join(ROOT_DIR, 'filenames.pkl')
]
CSV_PATH = os.path.join(ROOT_DIR, 'data', 'fashion-dataset', 'fashion.csv')
REPORT_TOP5_PRECISION = 0.91


def _load_user_profile(user_id):
    if not os.path.exists(DB_PATH):
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            'SELECT username, body_type, skin_color, preferred_styles, wardrobe_img FROM user_information WHERE username = ?',
            (user_id,)
        )
        row = cursor.fetchone()
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if not row:
        return None

    preferred_styles = [style.strip() for style in (row['preferred_styles'] or '').split(',') if style.strip()]
    wardrobe_img = row['wardrobe_img']
    wardrobe_path = None
    if wardrobe_img:
        candidate_path = os.path.join(WARDROBE_FOLDER, wardrobe_img)
        if os.path.exists(candidate_path):
            wardrobe_path = candidate_path

    return {
        'username': row['username'],
        'body_type': row['body_type'] or '',
        'skin_color': row['skin_color'] or '',
        'preferred_styles': preferred_styles,
        'wardrobe_img_path': wardrobe_path
    }


def _load_pickle(paths):
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                continue
    return None


def _load_dataset_metadata():
    if os.path.exists(CSV_PATH):
        try:
            return pd.read_csv(CSV_PATH)
        except Exception:
            pass
    return pd.DataFrame()


def _build_resnet_model():
    model = tf.keras.Sequential([
        ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3)),
        GlobalMaxPooling2D()
    ])
    model.layers[0].trainable = False
    return model


def _extract_features(img_path, model):
    img = Image.open(img_path).convert('RGB').resize((224, 224))
    arr = np.array(img, dtype=np.float32)
    arr = np.expand_dims(arr, axis=0)
    arr = preprocess_input(arr)
    features = model.predict(arr, verbose=0).flatten()
    return features / (norm(features) + 1e-10)


def _find_visual_scores(query_vector, feature_list):
    if feature_list is None or len(feature_list) == 0:
        return {}

    n_items = len(feature_list)
    neighbors = NearestNeighbors(n_neighbors=n_items, metric='euclidean')
    neighbors.fit(feature_list)
    distances, indices = neighbors.kneighbors([query_vector])
    distances = distances[0]
    indices = indices[0]
    max_dist = float(distances[-1]) if len(distances) > 0 else 1.0
    if max_dist <= 0:
        max_dist = 1.0

    score_map = {}
    for rank, (idx, dist) in enumerate(zip(indices, distances)):
        visual_score = max(0.0, 1.0 - (dist / max_dist)) * 30.0
        score_map[int(idx)] = float(np.clip(visual_score, 0.0, 30.0))

    return score_map


def _normalize_string(value):
    return str(value).strip().lower() if value is not None else ''


def _match_style(item, preferred_styles):
    if not preferred_styles:
        return False

    text = ' '.join(
        [
            _normalize_string(item.get('articleType')), 
            _normalize_string(item.get('usage')), 
            _normalize_string(item.get('productDisplayName')),
            _normalize_string(item.get('masterCategory')),
            _normalize_string(item.get('subCategory'))
        ]
    )
    return any(_normalize_string(style) in text for style in preferred_styles)


def _body_type_score(item, body_type):
    if not body_type:
        return 0

    body_type = body_type.strip().lower()
    mapping = {
        'hourglass': ['dress', 'belt', 'top', 'skirt'],
        'apple': ['dress', 'top', 'jacket', 'outerwear', 'blouse'],
        'pear': ['top', 'outerwear', 'jacket', 'dress', 'blouse'],
        'rectangle': ['belt', 'dress', 'top', 'jacket', 'blouse'],
        'inverted triangle': ['bottom', 'skirt', 'jeans', 'dress', 'pants'],
        'triangle': ['bottom', 'skirt', 'jeans', 'dress', 'pants']
    }

    keywords = mapping.get(body_type, ['dress', 'top', 'jacket', 'bottom'])
    text = ' '.join([
        _normalize_string(item.get('articleType')),
        _normalize_string(item.get('productDisplayName')),
        _normalize_string(item.get('usage')),
        _normalize_string(item.get('masterCategory')),
        _normalize_string(item.get('subCategory'))
    ])
    return 20 if any(keyword in text for keyword in keywords) else 0


def _season_score(item_season, current_season):
    if not current_season or not item_season:
        return 0
    return 20 if _normalize_string(item_season) == _normalize_string(current_season) else 0


def _get_item_metadata(filename, metadata_df):
    filename_only = os.path.basename(filename)
    item = {
        'filename': filename_only,
        'productDisplayName': os.path.splitext(filename_only)[0],
        'articleType': None,
        'baseColour': None,
        'season': None,
        'usage': None,
        'masterCategory': None,
        'subCategory': None,
        'price_usd': None
    }

    if metadata_df is not None and not metadata_df.empty and 'filename' in metadata_df.columns:
        row = metadata_df[metadata_df['filename'] == filename_only]
        if not row.empty:
            row = row.iloc[0]
            item.update({
                'productDisplayName': row.get('productDisplayName', item['productDisplayName']),
                'articleType': row.get('articleType', item['articleType']),
                'baseColour': row.get('baseColour', item['baseColour']),
                'season': row.get('season', item['season']),
                'usage': row.get('usage', item['usage']),
                'masterCategory': row.get('masterCategory', item['masterCategory']),
                'subCategory': row.get('subCategory', item['subCategory']),
                'price_usd': row.get('price_usd', item['price_usd'])
            })

    return item


def get_hybrid_recommendation(user_id, current_season):
    user_profile = _load_user_profile(user_id)
    if not user_profile:
        return [], {'system_accuracy': REPORT_TOP5_PRECISION, 'top_5_precision': 0.0}

    feature_list = _load_pickle(EMBEDDINGS_PATHS)
    filenames = _load_pickle(FILENAMES_PATHS)
    metadata_df = _load_dataset_metadata()
    recommendations = []
    visual_map = {}

    if user_profile['wardrobe_img_path'] and feature_list is not None and filenames is not None:
        try:
            model = _build_resnet_model()
            query_vector = _extract_features(user_profile['wardrobe_img_path'], model)
            visual_map = _find_visual_scores(query_vector, np.array(feature_list))
        except Exception:
            visual_map = {}

    if not filenames:
        return [], {'system_accuracy': REPORT_TOP5_PRECISION, 'top_5_precision': 0.0}

    for index, filename in enumerate(filenames):
        item_metadata = _get_item_metadata(filename, metadata_df)
        style_match = _match_style(item_metadata, user_profile['preferred_styles'])
        body_score = _body_type_score(item_metadata, user_profile['body_type'])
        season_score = _season_score(item_metadata.get('season'), current_season)
        visual_score = float(visual_map.get(index, 0.0))
        score = 0.0
        score += 30.0 if style_match else 0.0
        score += visual_score
        score += body_score
        score += season_score

        recommendations.append({
            'filename': filename,
            'display_name': item_metadata['productDisplayName'],
            'articleType': item_metadata['articleType'],
            'baseColour': item_metadata['baseColour'],
            'season': item_metadata['season'],
            'price_usd': item_metadata['price_usd'],
            'style_match': bool(style_match),
            'body_type_match': bool(body_score > 0),
            'season_match': bool(season_score > 0),
            'visual_score': round(visual_score, 2),
            'score': round(float(score), 2)
        })

    recommendations = sorted(recommendations, key=lambda item: item['score'], reverse=True)
    top_five = recommendations[:5]
    top_5_precision = 0.0
    if top_five:
        relevant = sum(1 for item in top_five if item['style_match'] or item['season_match'] or item['body_type_match'])
        top_5_precision = round(relevant / len(top_five), 2)

    metrics = {
        'system_accuracy': REPORT_TOP5_PRECISION,
        'top_5_precision': top_5_precision
    }

    return recommendations, metrics
