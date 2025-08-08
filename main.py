import streamlit as st
import pandas as pd
import pickle
import requests
import time
from datetime import datetime
import os       
import gdown

# Set page configuration
st.set_page_config(
    page_title="Movie Magic - Recommendation System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
def load_css():
    st.markdown("""
    <style>
        .movie-card {
            background-color: #1E1E1E;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s;
        }
        .movie-card:hover {
            transform: translateY(-5px);
        }
        .movie-title {
            color: #FFD700;
            font-size: 1.2rem;
            margin-bottom: 10px;
            font-weight: bold;
        }
        .movie-info {
            color: #CCCCCC;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }
        .rating {
            color: #FFD700;
            font-weight: bold;
        }
        .sidebar-header {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 20px;
            color: #FFD700;
        }
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 30px;
            color: #FFD700;
            text-align: center;
        }
        .subheader {
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: #CCCCCC;
            text-align: center;
        }
        .btn-recommend {
            background-color: #FFD700;
            color: #1E1E1E;
            font-weight: bold;
            width: 100%;
            padding: 10px;
            border-radius: 5px;
            margin-top: 20px;
        }
        .btn-recommend:hover {
            background-color: #E6C200;
        }
        .loading {
            text-align: center;
            color: #FFD700;
            margin: 20px 0;
        }
        .genre-tag {
            background-color: #444444;
            color: #FFFFFF;
            padding: 5px 10px;
            border-radius: 15px;
            margin-right: 5px;
            margin-bottom: 5px;
            display: inline-block;
            font-size: 0.8rem;
        }
        .overview {
            color: #CCCCCC;
            font-size: 0.9rem;
            margin-top: 10px;
            margin-bottom: 15px;
        }
        .details-btn {
            background-color: #444444;
            color: #FFFFFF;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8rem;
        }
        .details-btn:hover {
            background-color: #666666;
        }
    </style>
    """, unsafe_allow_html=True)

# Load CSS
load_css()
#
SIMILARITY_FILE_ID = "1aGXEf5Fto0Fz3v2wgnG7yvPLkOxpVUZ1"
SIMILARITY_FILE_NAME = "similarity.pkl"

# ==============================
# Helper to download file if missing
# ==============================
def download_similarity():
    if not os.path.exists(SIMILARITY_FILE_NAME):
        url = f"https://drive.google.com/file/d/1aGXEf5Fto0Fz3v2wgnG7yvPLkOxpVUZ1/view?usp=sharing"
        st.write("📥 Downloading similarity.pkl from Google Drive...")
        gdown.download(url, SIMILARITY_FILE_NAME, quiet=False)

# Call before loading data
download_similarity()

# API functions
def fetch_movie_details(movie_id):
    """Fetch detailed movie information from TMDB API"""
    try:
        response = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=899f174a0b7bc487c1aff3f3b31db00f&language=en-US'
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def fetch_poster(movie_id):
    """Fetch movie poster from TMDB API"""
    try:
        data = fetch_movie_details(movie_id)
        if data and 'poster_path' in data and data['poster_path']:
            return "https://image.tmdb.org/t/p/w500/" + data['poster_path']
        else:
            return "https://via.placeholder.com/500x750?text=No+Image"
    except:
        return "https://via.placeholder.com/500x750?text=No+Image"

def get_movie_genres(movie_id):
    """Get genres for a movie"""
    details = fetch_movie_details(movie_id)
    if details and 'genres' in details:
        return [genre['name'] for genre in details['genres']]
    return []

def get_release_year(movie_id):
    """Get release year for a movie"""
    details = fetch_movie_details(movie_id)
    if details and 'release_date' in details and details['release_date']:
        try:
            return datetime.strptime(details['release_date'], '%Y-%m-%d').year
        except:
            return "Unknown"
    return "Unknown"

def get_movie_rating(movie_id):
    """Get movie rating"""
    details = fetch_movie_details(movie_id)
    if details and 'vote_average' in details:
        return details['vote_average']
    return "N/A"

def get_movie_overview(movie_id):
    """Get movie overview/description"""
    details = fetch_movie_details(movie_id)
    if details and 'overview' in details and details['overview']:
        return details['overview']
    return "No overview available."

def recommend(movie, num_recommendations=5, genre_filter=None):
    """Recommend movies based on similarity and optional genre filter"""
    # Find the movie in the DataFrame and get its index
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]

    # Get all movies sorted by similarity
    movies_sorted = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:20]

    recommended_movies = []
    recommended_posters = []
    recommended_years = []
    recommended_ratings = []
    recommended_genres = []
    recommended_overviews = []
    recommended_ids = []

    # Apply genre filter if specified
    count = 0
    for i in movies_sorted:
        if count >= num_recommendations:
            break

        tmdb_id = movies.iloc[i[0]].movie_id

        # If genre filter is active, check if movie has the genre
        if genre_filter:
            movie_genres = get_movie_genres(tmdb_id)
            if genre_filter not in movie_genres:
                continue

        # Get movie details
        title = movies.iloc[i[0]].title
        poster = fetch_poster(tmdb_id)
        year = get_release_year(tmdb_id)
        rating = get_movie_rating(tmdb_id)
        genres = get_movie_genres(tmdb_id)
        overview = get_movie_overview(tmdb_id)

        # Add to recommendation lists
        recommended_movies.append(title)
        recommended_posters.append(poster)
        recommended_years.append(year)
        recommended_ratings.append(rating)
        recommended_genres.append(genres)
        recommended_overviews.append(overview)
        recommended_ids.append(tmdb_id)

        count += 1

    return recommended_movies, recommended_posters, recommended_years, recommended_ratings, recommended_genres, recommended_overviews, recommended_ids

# Load data
@st.cache_data
def load_data():
    movies_df = pickle.load(open('movie.pkl', 'rb'))
    similarity_matrix = pickle.load(open('similarity.pkl', 'rb'))
    return movies_df, similarity_matrix

movies, similarity = load_data()
movies_list = movies['title'].values

# Sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-header">🎬 Movie Magic</div>', unsafe_allow_html=True)
    st.markdown("---")

    # App modes
    app_mode = st.radio(
        "Choose Mode",
        ["Movie Recommendations", "About"]
    )

    if app_mode == "Movie Recommendations":
        # Number of recommendations
        num_recommendations = st.slider(
            "Number of recommendations",
            min_value=3,
            max_value=10,
            value=5,
            step=1
        )

        # Genre filter
        genre_options = ["None", "Action", "Adventure", "Animation", "Comedy", "Crime",
                         "Documentary", "Drama", "Family", "Fantasy", "History",
                         "Horror", "Music", "Mystery", "Romance", "Science Fiction",
                         "Thriller", "War", "Western"]
        selected_genre = st.selectbox("Filter by genre", genre_options)

        # Apply genre filter only if not "None"
        genre_filter = None if selected_genre == "None" else selected_genre

        st.markdown("---")
        st.markdown("### How it works")
        st.markdown("""
        This app uses content-based filtering to recommend movies similar to your selection.

        1. Select a movie you like
        2. Adjust filters if needed
        3. Click 'Get Recommendations'
        4. Explore similar movies!
        """)

# Main content
if app_mode == "About":
    st.markdown('<div class="main-header">About Movie Magic</div>', unsafe_allow_html=True)
    st.markdown("""
    ## Welcome to Movie Magic! �

    Movie Magic is a recommendation system that helps you discover movies similar to ones you already enjoy.

    ### Features:
    - Get personalized movie recommendations
    - Filter recommendations by genre
    - View detailed information about each movie
    - Adjust the number of recommendations

    ### How it works:
    The system uses content-based filtering to find movies with similar themes, genres, and characteristics.

    ### Data Source:
    Movie data is sourced from The Movie Database (TMDB) API.

    ### Created by:
    Baihela Hussain
    """)

else:  # Movie Recommendations mode
    st.markdown('<div class="main-header">🎬 Movie Magic 🍿</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader">Discover movies you\'ll love</div>', unsafe_allow_html=True)

    # Movie selection
    selected_movie = st.selectbox("Search and select a movie you like", movies_list)

    # Get recommendations button
    if st.button('Get Recommendations', key='recommend_btn'):
        with st.spinner('Finding movies you might like...'):
            # Simulate loading for better UX
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)

            # Get recommendations
            names, posters, years, ratings, genres_list, overviews, movie_ids = recommend(
                selected_movie,
                num_recommendations=num_recommendations,
                genre_filter=genre_filter
            )

            # Remove progress bar after loading
            progress_bar.empty()

            # Display recommendations
            st.markdown(f"### Recommended movies based on '{selected_movie}'")

            # Create columns for movie cards
            cols = st.columns(3)

            for idx, (name, poster, year, rating, genres, overview, movie_id) in enumerate(
                zip(names, posters, years, ratings, genres_list, overviews, movie_ids)
            ):
                with cols[idx % 3]:
                    # Movie card with HTML/CSS for better styling
                    st.markdown(f"""
                    <div class="movie-card">
                        <div class="movie-title">{name} ({year})</div>
                        <div class="movie-info">Rating: <span class="rating">⭐ {rating}/10</span></div>
                        <div>
                            {''.join([f'<span class="genre-tag">{g}</span>' for g in genres[:3]])}
                        </div>
                        <div class="overview">{overview[:150]}{'...' if len(overview) > 150 else ''}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Display movie poster
                    st.image(poster, use_column_width=True)

                    # Movie details expander
                    with st.expander("See more details"):
                        st.markdown(f"**{name}** ({year})")
                        st.markdown(f"**Rating:** ⭐ {rating}/10")
                        st.markdown("**Genres:** " + ", ".join(genres))
                        st.markdown("**Overview:**")
                        st.markdown(overview)
                        st.markdown(f"**TMDB ID:** {movie_id}")

                        # Link to TMDB
                        st.markdown(f"[View on TMDB](https://www.themoviedb.org/movie/{movie_id})")

    # Display some popular movies if no recommendations yet
    else:
        st.markdown("### Select a movie and click 'Get Recommendations' to start")
        st.markdown("#### Some popular movies you might like:")

        # Display a few popular movies as examples
        popular_movies = ["Avatar", "Inception", "The Dark Knight", "Pulp Fiction", "The Shawshank Redemption", "Forrest Gump"]
        popular_cols = st.columns(3)

        for idx, movie_title in enumerate(popular_movies):
            if movie_title in movies_list:
                movie_index = movies[movies['title'] == movie_title].index[0]
                movie_id = movies.iloc[movie_index].movie_id
                poster = fetch_poster(movie_id)

                with popular_cols[idx % 3]:
                    st.image(poster, width=200)
                    st.markdown(f"**{movie_title}**")
                    st.button(f"Select {movie_title}", key=f"select_{idx}", on_click=lambda m=movie_title: st.session_state.update({"selected_movie": m}))



