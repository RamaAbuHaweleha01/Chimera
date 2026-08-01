// ============================================
// CineVerse - Movie Database
// Complete movie listing with categories
// ============================================

/*
 * This file contains the complete movie database
 * and all display/filtering functionality.
 * Movies are organized by category for easy browsing.
 */

// ============================================
// MOVIE DATABASE
// ============================================

const moviesData = [
    // ============================================
    // ACTION MOVIES
    // ============================================
    {
        id: 1,
        title: "Troy",
        year: 2004,
        rating: 4.5,
        category: "action",
        poster: "https://m.media-amazon.com/images/M/MV5BYTI0NGJlNjQtODUyNS00OTA5LWI0ZTUtYzkwNTY3NzA3YmQwXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg",
        description: "The legendary Trojan War between Greeks and Trojans. Starring Brad Pitt as Achilles."
    },
    {
        id: 2,
        title: "The Dark Knight",
        year: 2008,
        rating: 4.8,
        category: "action",
        poster: "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_.jpg",
        description: "Batman faces the Joker in the most iconic film of the trilogy. Directed by Christopher Nolan."
    },

    // ============================================
    // ADVENTURE MOVIES
    // ============================================
    {
        id: 3,
        title: "The Odyssey",
        year: 2026,
        rating: 4.2,
        category: "adventure",
        poster: "https://snworksceo.imgix.net/cds/9339dfb5-cfed-4df4-8920-a314b499522d.sized-1000x1000.jpg?w=1000&dpr=2",
        description: "Odysseus's legendary journey back home after the Trojan War. An epic adventure."
    },
    {
        id: 4,
        title: "Pirates of the Caribbean: Black Pearl",
        year: 2003,
        rating: 4.5,
        category: "adventure",
        poster: "https://resizing.flixster.com/-XZAfHZM39UwaGJIFWKAE8fS0ak=/v3/t/assets/p32093_p_v11_ak.jpg",
        description: "Captain Jack Sparrow's quest to find the legendary Black Pearl. The first Pirates film."
    },
    {
        id: 5,
        title: "Pirates of the Caribbean: Dead Men Tell No Tales",
        year: 2017,
        rating: 4.1,
        category: "adventure",
        poster: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSlekmKPITceTzRtmPixU70yR0EZrWDPksbjh2M8RjYFw&s=10",
        description: "Jack Sparrow faces his most dangerous enemy yet. The fifth installment."
    },
    {
        id: 6,
        title: "Pirates of the Caribbean: On Stranger Tides",
        year: 2011,
        rating: 4.0,
        category: "adventure",
        poster: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRM403jqsaVVBLG7KzvXcMdlusk9Ydt5ium7i9N94BLtA&s=10",
        description: "Jack Sparrow searches for the Fountain of Youth. The fourth Pirates film."
    },

    // ============================================
    // CRIME MOVIES
    // ============================================
    {
        id: 7,
        title: "The Godfather",
        year: 1972,
        rating: 4.9,
        category: "crime",
        poster: "https://m.media-amazon.com/images/M/MV5BNGEwYjgwOGQtYjg5ZS00Njc1LTk2ZGEtM2QwZWQ2NjdhZTE5XkEyXkFqcGc@._V1_.jpg",
        description: "The story of the Corleone Italian mafia family. Considered one of the greatest films ever."
    },
    {
        id: 8,
        title: "Scarface",
        year: 1983,
        rating: 4.6,
        category: "crime",
        poster: "https://www.originalfilmart.com/cdn/shop/products/scarface_1983_original_film_art_a_600x.jpg?v=1640131245",
        description: "The rise and fall of Tony Montana in the Miami drug cartel world. An iconic crime classic."
    },
    {
        id: 9,
        title: "The Godfather Part II",
        year: 1974,
        rating: 4.8,
        category: "crime",
        poster: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTKFkeCM6syhstRusD3nT-M_95Xm6o8xYbSCnlj8xyPZw&s=10",
        description: "The continuation of the Corleone family story and Michael's rise to power. A sequel masterpiece."
    },

    // ============================================
    // DRAMA MOVIES
    // ============================================
    {
        id: 10,
        title: "Oppenheimer",
        year: 2023,
        rating: 4.7,
        category: "drama",
        poster: "https://upload.wikimedia.org/wikipedia/en/thumb/4/4a/Oppenheimer_%28film%29.jpg/250px-Oppenheimer_%28film%29.jpg",
        description: "The story of scientist J. Robert Oppenheimer and the creation of the atomic bomb."
    },
    {
        id: 11,
        title: "Scent of a Woman",
        year: 1992,
        rating: 4.4,
        category: "drama",
        poster: "https://upload.wikimedia.org/wikipedia/en/9/91/Scent_of_a_Woman.jpg",
        description: "A young student and a blind retired lieutenant colonel form an unlikely bond."
    },
    {
        id: 12,
        title: "And Justice for All",
        year: 1979,
        rating: 4.0,
        category: "drama",
        poster: "https://m.media-amazon.com/images/M/MV5BMTc2Mjc0MzU5N15BMl5BanBnXkFtZTYwODMxNzE5._V1_.jpg",
        description: "A lawyer fights against corruption in the American justice system. Starring Al Pacino."
    },

    // ============================================
    // THRILLER MOVIES
    // ============================================
    {
        id: 13,
        title: "The Devil's Advocate",
        year: 1997,
        rating: 4.3,
        category: "thriller",
        poster: "https://m.media-amazon.com/images/M/MV5BNGIxZmU2ZjEtYjc3OC00Y2FiLWE2ZTQtZGI3NzE0YmRhOTMxXkEyXkFqcGc@._V1_.jpg",
        description: "A young lawyer discovers that his boss is the Devil himself. A psychological thriller."
    },
    {
        id: 19,
        title: "House of Cards",
        year: 2013,
        rating: 4.6,
        category: "thriller",
        poster: "https://myhotposters.com/cdn/shop/products/mL0924_0f93fb5a-ff35-42da-b935-51068540eff8_1024x1024.jpg?v=1748536546",
        description: "A Congressman works with his conniving wife to exact revenge on the people who betrayed him."
    },

    // ============================================
    // TV SERIES
    // ============================================
    {
        id: 14,
        title: "White Collar",
        year: 2009,
        rating: 4.3,
        category: "series",
        poster: "https://m.media-amazon.com/images/I/81f8epuklCL.jpg",
        description: "A con artist collaborates with the FBI in this crime drama series. 6 seasons."
    },
    {
        id: 15,
        title: "The Recruit: Season 1",
        year: 2022,
        rating: 4.2,
        category: "series",
        poster: "https://resizing.flixster.com/0yVKB0rTrMitXx-_bAvT-MiFJRk=/ems.cHJkLWVtcy1hc3NldHMvdHZzZWFzb24vNDBlODBlOTktOGRmYS00MDkwLWI5NTUtODBmZTYxZDI1NmE2LmpwZw==",
        description: "A CIA lawyer becomes involved in international conflicts when an asset tries to expose her relationship to the agency."
    },
    {
        id: 16,
        title: "The Recruit: Season 2",
        year: 2025,
        rating: 4.3,
        category: "series",
        poster: "https://m.media-amazon.com/images/M/MV5BOTgyOGQ3ZTEtMGQ0Ni00YjI1LTgxYjItOTJjMjhiZWE1YWZkXkEyXkFqcGc@._V1_.jpg",
        description: "Owen Hendricks faces massive international conflicts with dangerous parties."
    },
    {
        id: 17,
        title: "The Gentlemen",
        year: 2020,
        rating: 4.3,
        category: "series",
        poster: "https://m.media-amazon.com/images/M/MV5BMzM0YzFhMTYtYjZkNS00MWRmLTg2ZDgtY2MzYjQ5ODVmOTI1XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg",
        description: "When aristocratic Eddie inherits the family estate, he discovers it's home to a huge weed empire."
    },
    {
        id: 18,
        title: "Five Feet Apart",
        year: 2019,
        rating: 4.3,
        category: "drama",
        poster: "https://m.media-amazon.com/images/M/MV5BZDE5NTFmODMtZDUyZi00MTdkLTlmMmItMThjZmViMjIzOTcxXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg",
        description: "Two cystic fibrosis patients fall in love but must maintain distance due to their condition."
    },
    {
        id: 20,
        title: "The Witcher",
        year: 2019,
        rating: 4.6,
        category: "adventure",
        poster: "https://i.ebayimg.com/images/g/IWsAAOSwNbZd6TXv/s-l400.jpg",
        description: "Geralt of Rivia, a solitary monster hunter, struggles to find his place in a world where people often prove more wicked than beasts."
    }
];

// ============================================
// DISPLAY FUNCTIONS
// ============================================

/**
 * Display movies in the grid.
 * Creates a card for each movie with poster, title, rating, and category.
 * @param {Array} movies - Array of movie objects to display.
 */
function displayMovies(movies) {
    const grid = document.getElementById('moviesGrid');
    grid.innerHTML = '';
    
    // Check if no movies match the filter
    if (movies.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 50px; color: #666;">
                <i class="fas fa-search" style="font-size: 50px; display: block; margin-bottom: 20px;"></i>
                <h3>No movies match your search</h3>
                <p style="color: #888; margin-top: 10px;">Try different keywords or categories</p>
            </div>
        `;
        return;
    }
    
    // Create each movie card
    movies.forEach(movie => {
        const card = document.createElement('div');
        card.className = 'movie-card';
        card.setAttribute('data-id', movie.id);
        
        // Generate star rating (filled ★ and empty ☆)
        const fullStars = Math.floor(movie.rating);
        const emptyStars = 5 - fullStars;
        const stars = '★'.repeat(fullStars) + '☆'.repeat(emptyStars);
        
        card.innerHTML = `
            <img src="${movie.poster}" alt="${movie.title}" class="movie-poster" 
                 onerror="this.src='images/placeholder.jpg'">
            <div class="movie-info">
                <div class="movie-title">${movie.title}</div>
                <div class="movie-meta">
                    <span class="movie-rating">${stars} ${movie.rating}</span>
                    <span class="movie-category">${movie.category}</span>
                </div>
                <div class="movie-year">${movie.year}</div>
            </div>
        `;
        
        // Click event to open movie popup
        card.addEventListener('click', function() {
            openMoviePopup(movie.id);
        });
        
        grid.appendChild(card);
    });
}

// ============================================
// FILTER FUNCTIONS
// ============================================

/**
 * Filter movies by category.
 * Updates the active state in the category list.
 * @param {string} category - Category name or 'all' for all movies.
 */
function filterMovies(category) {
    // Update active state in category list
    document.querySelectorAll('.category-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.category === category) {
            item.classList.add('active');
        }
    });
    
    // Filter movies based on category
    let filtered = moviesData;
    if (category !== 'all') {
        filtered = moviesData.filter(movie => movie.category === category);
    }
    
    displayMovies(filtered);
}

/**
 * Search movies by title, category, year, or description.
 */
function searchMovies() {
    const query = document.getElementById('searchInput').value.toLowerCase().trim();
    
    // If search is empty, show current category
    if (query === '') {
        const activeCategory = document.querySelector('.category-item.active');
        if (activeCategory) {
            filterMovies(activeCategory.dataset.category);
        } else {
            displayMovies(moviesData);
        }
        return;
    }
    
    // Filter by search query
    const filtered = moviesData.filter(movie => 
        movie.title.toLowerCase().includes(query) ||
        movie.category.toLowerCase().includes(query) ||
        movie.year.toString().includes(query) ||
        movie.description.toLowerCase().includes(query)
    );
    
    displayMovies(filtered);
}

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize the page when DOM is loaded.
 * Displays all movies and adds keyboard shortcuts.
 */
document.addEventListener('DOMContentLoaded', function() {
    displayMovies(moviesData);
    
    // Add keyboard shortcut for search (Ctrl+F)
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            document.getElementById('searchInput').focus();
        }
    });
});
