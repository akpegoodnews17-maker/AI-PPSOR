# Development of a Fashion-Based AI Wardrobe Assistant

## Project Title & Overview

**Development of a Fashion-Based AI Wardrobe Assistant** is a Python-based fashion recommendation system designed to help users manage their wardrobe and receive personalized outfit suggestions. The application ingests user profile data, wardrobe image metadata, season and occasion preferences, and generates recommendations using a mix of attribute filtering, content-based similarity, and occasion-aware outfit construction.

## System Architecture

The system is structured as a Flask web application with three main layers:

- **Frontend**: HTML templates located in `app/templates`, with static assets served from `app/static`.
- **Backend**: The Flask server in `app/main.py` handles routing, session management, profile creation, login/signup workflows, and coordination of recommendation services.
- **Data/Model Layer**: The application uses a local database and dataset files stored under `data/`, plus ML helper modules in `ai_engine/` and recommendation modules in `app/weather_based/`, `app/occasion/`, and `app/image_based/`.

The backend orchestrates interactions between stored user data, wardrobe metadata, and recommendation logic. When a user accesses their profile, the backend reads profile attributes and invokes specialized recommendation modules to generate outfit suggestions.

## Database Schema

The app stores user and wardrobe data in a relational schema that includes:

- `login`
  - `id` (Primary Key)
  - `name`
  - `username` (Unique)
  - `phone`
  - `email` (Unique)
  - `password`

- `user_information`
  - `id` (Primary Key)
  - `username` (Unique, Foreign Key → `login.username`)
  - `profile_pic`
  - `gender`
  - `date_of_birth`
  - `body_type`
  - `height`
  - `weight`
  - `preferred_color`
  - `preferred_fabrics`
  - `preferred_styles`
  - `occasion_types`
  - `style_goals`
  - `budget`
  - `skin_color`
  - `wardrobe_img`
  - `user_title`
  - `user_about_1`
  - `user_about_2`
  - `virtual_try_on_image`

### Wardrobe Item Storage

Wardrobe recommendation inputs are also sourced from dataset files and metadata files rather than a dedicated wardrobe table:

- `data/fashion-dataset/fashion.csv` and `data/fashion-dataset/styles.csv` provide item attributes like color, category, article type, brand, and price.
- `app/image_based/embeddings.pkl` and `app/image_based/filenames.pkl` store precomputed image embeddings for content-based similarity.
- `app/occasion/metadata.pkl` stores occasion-specific item metadata used to build multi-piece outfits.

These datasets represent wardrobe items with attributes such as category, subcategory, color, season, usage, and price.

## Recommendation Engine Logic

### 1. User Preferences and Profile-Based Filtering

The application reads a user’s profile from `user_information`, including:

- gender
- body type
- preferred colors
- preferred fabrics
- preferred styles
- occasion types
- style goals
- wardrobe image

Using this metadata, the app applies content-based filtering by matching item attributes to user preferences.

### 2. Weather-Based Recommendation

Weather-based recommendations are handled via `app/weather_based/recommend_cli.py` and `app/weather_based/models/recommender.py`.

The logic is:

1. Accept a `season` value and a `gender` label.
2. Normalize both values and construct an `age_group` tag such as `Adults-Men` or `Adults-Women`.
3. Load a pre-trained weather-aware model and metadata from pickled storage.
4. Filter the item dataset for: 
   - matching `season`
   - matching `gender`
   - matching `age_group`
5. Return a prioritized list of seasonally appropriate items.

> Note: The code uses season-based weather logic rather than real-time temperature or detailed conditions.

### 3. Occasion-Based Recommendation

Occasion recommendations are produced through `app/occasion/outfit_builder.py` and `app/occasion/recommend.py`.

The workflow is:

1. Load occasion metadata from `app/occasion/metadata.pkl`.
2. Filter items by `usage` (occasion) and optionally by `gender`.
3. If strict matching yields too few results, relax the gender filter or return all available items.
4. Categorize filtered items into `topwear`, `bottomwear`, `footwear`, and `accessories`.
5. Assemble outfits by selecting one item from each category and ensuring a minimum top+bottom combination.

This produces multi-piece outfit suggestions appropriate for formal, casual, or event-based occasions.

### 4. Content-Based Image Similarity

The wardrobe assistant also supports image-based recommendations via `app/image_based/cli_recommender.py`.

The process is:

1. Save a wardrobe or fashion item image upload.
2. Extract visual features using a ResNet50-based embedding model.
3. Normalize the embedding vector.
4. Run K-Nearest Neighbors search against precomputed item embeddings stored in `app/image_based/embeddings.pkl`.
5. Return similar product metadata from `data/fashion-dataset/fashion.csv`.

This is a classic content-based filtering approach that recommends visually similar items.

### 5. Attribute and Preference Relaxation Logic

The core item filtering logic in `ai_engine/fashion_recommender.py` follows a stepwise relaxation strategy:

1. Start by filtering on all provided attributes: gender, color, fabrics, styles, occasions, and style goals.
2. If no results are found, relax filters gradually:
   - first drop some preference filters and keep gender/color/style
   - then drop all but gender/color
   - finally fallback to gender-only recommendations
3. If still empty, return a small random sample of available items.

This ensures the assistant still returns useful wardrobe suggestions even when the profile is sparse.

## Feature Mapping

The project implements the following recommendation and wardrobe management features:

- **Content-Based Filtering**
  - Visual similarity matching with ResNet50 embeddings in `app/image_based/cli_recommender.py`.
  - Attribute-based filtering on gender, color, fabric, style, occasion, and body type in `ai_engine/fashion_recommender.py`.

- **Seasonal Recommendation**
  - Weather/season-specific suggestions using `app/weather_based/recommend_cli.py` and the `FashionRecommender` model.

- **Occasion-Aware Outfit Assembly**
  - Occasion-driven outfit building with category-aware selection in `app/occasion/outfit_builder.py`.

- **User Profile and Wardrobe Metadata**
  - Persistent user preferences stored in relational tables via SQLAlchemy.
  - Wardrobe images and uploaded profile pictures saved under `app/static/uploads/`.

- **Fallback Strategy**
  - Progressive filter relaxation in the preference recommender.
  - Safe handling of missing recommendation modules to keep the app running.

## Tech Stack

- Language: Python
- Web Framework: Flask
- Database ORM: SQLAlchemy
- Storage: SQLite (local fallback) / MySQL-compatible schema
- Data Processing: Pandas, NumPy
- Machine Learning:
  - scikit-learn (Nearest Neighbors, OneHotEncoder, TF-IDF)
  - TensorFlow / Keras (ResNet50 embeddings)
- Image Processing: PIL, OpenCV
- External APIs / integrations:
  - Optional Gemini-based natural language/AI generation via `google-generativeai`
  - Optional Google Custom Search integration in `app/finder.py`
  - OpenWeatherMap-style geocoding placeholder in `app/main.py`

## Project Scope

This repository is focused on recommendation logic and wardrobe management. The core value is in:

- deriving outfit suggestions from user preferences,
- matching wardrobe items to seasons and occasions,
- recommending visually similar fashion items,
- storing and managing user profile and wardrobe metadata.

It intentionally does not rely on a complete virtual try-on experience for the primary evaluation of the project. While the code includes references to virtual try-on utilities, the README scope is limited to the recommendation engine and wardrobe assistant features.

## Running the App

1. Install Python dependencies from `requirements.txt`.
2. Ensure dataset files exist under `data/fashion-dataset/` and pickled metadata exists for the weather and occasion modules.
3. Run the Flask server with:

```bash
python run.py
```

4. Access the app at `http://127.0.0.1:5000`.

---

**Note:** A technical reviewer should evaluate this system as a hybrid recommendation prototype that combines profile-based filtering, seasonal/occasion logic, and content-based image similarity for fashion wardrobe assistance.
