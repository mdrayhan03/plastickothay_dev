document.addEventListener('DOMContentLoaded', function() {
    // message control
    const calerts = document.querySelectorAll('.calert');
    calerts.forEach(calert => {
        setTimeout(() => {
            calert.style.opacity = '0';
            setTimeout(() => calert.style.display = 'none', 500);
        }, 3000); // 3 seconds
    });

    // About modal functionality
    const aboutLink = document.querySelector('.nav-menu li:nth-child(3) a');
    const aboutModal = document.getElementById('aboutModal');
    const closeModal = document.querySelector('.close-modal');
    
    if (aboutLink && aboutModal) {
        aboutLink.addEventListener('click', function(e) {
            e.preventDefault();
            aboutModal.classList.add('active');
        });
    }
    
    if (closeModal && aboutModal) {
        closeModal.addEventListener('click', function() {
            aboutModal.classList.remove('active');
        });
        
        // Close modal when clicking outside the modal content
        aboutModal.addEventListener('click', function(e) {
            if (e.target === aboutModal) {
                aboutModal.classList.remove('active');
            }
        });
    }
    
    // Mobile menu toggle functionality
    const menuToggle = document.getElementById('menuToggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            // Check if the menu toggle is already active (X state)
            if (menuToggle.classList.contains('active')) {
                // If it's active (X showing), hide the menu
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
            } else {
                // If it's not active (hamburger showing), show the menu
                navMenu.classList.add('active');
                menuToggle.classList.add('active');
            }
        });
    }
    
    // Close menu when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('nav') && navMenu.classList.contains('active')) {
            navMenu.classList.remove('active');
            menuToggle.classList.remove('active');
        }
    });
    
    // Initialize OpenStreetMap
    const mapElement = document.getElementById('map');
    let map;
    let userMarker;
    let postMarkersLayer;

    if (mapElement) {
        // Initialize the map without default zoom controls
        map = L.map('map', {
            zoomControl: false
        });

        // Add OpenStreetMap tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 18
        }).addTo(map);

        connectLocation();
    }

    // Current location button functionality
    const locationBtn = document.getElementById('currentLocation');
    if (locationBtn) {
        locationBtn.addEventListener('click', function() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(position) {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;

                    // Center map on user's location
                    map.setView([lat, lng], 15);

                    // Add or update marker for user's location
                    if (userMarker) {
                        userMarker.setLatLng([lat, lng]);
                    } else {
                        userMarker = L.marker([lat, lng]).addTo(map)
                            .bindPopup('I am here');
                            // .openPopup();
                    }
                }, function(error) {
                    console.error('Error getting location:', error);
                    alert('Unable to get your location. Please check your permissions.');
                });
            } else {
                alert('Geolocation is not supported by your browser.');
            }
        });
    }

    // Connect location function on map load
    function connectLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                // Center map on user's location
                map.setView([lat, lng], 15);

                // Add or update marker for user's location
                if (userMarker) {
                    userMarker.setLatLng([lat, lng]);
                } else {
                    userMarker = L.marker([lat, lng]).addTo(map)
                        .bindPopup('I am here');
                        // .openPopup();
                }
            }, function(error) {
                console.error('Error getting location:', error);
                alert('Unable to get your location. Please check your permissions.');
            });
        } else {
            alert('Geolocation is not supported by your browser.');
        }
    }


    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function setMapStatus(state, message) {
        const loadingEl = document.getElementById('map-loading');
        const errorEl = document.getElementById('map-error');

        if (!loadingEl || !errorEl) {
            return;
        }

        loadingEl.style.display = 'none';
        errorEl.style.display = 'none';

        if (state === 'loading') {
            loadingEl.textContent = message || 'Loading posts…';
            loadingEl.style.display = 'flex';
        } else if (state === 'error') {
            errorEl.textContent = message || 'Unable to load posts right now.';
            errorEl.style.display = 'flex';
        } else if (state === 'empty') {
            loadingEl.textContent = message || 'No active posts with coordinates are available yet.';
            loadingEl.style.display = 'flex';
        }
    }

    function getSeverityColor(severity) {
        const value = Number(severity);
        if (value >= 4) return '#dc2626';
        if (value === 3) return '#f59e0b';
        return '#16a34a';
    }

    function renderPostsToMap(posts) {
        if (!map) {
            return;
        }

        if (!postMarkersLayer) {
            postMarkersLayer = L.layerGroup().addTo(map);
        } else {
            postMarkersLayer.clearLayers();
        }

        if (!Array.isArray(posts) || posts.length === 0) {
            setMapStatus('empty', 'No active posts with coordinates are available yet.');
            return;
        }

        posts.forEach(post => {
            if (post.lat === null || post.lon === null || post.lat === undefined || post.lon === undefined) {
                return;
            }

            const lat = Number(post.lat);
            const lon = Number(post.lon);

            if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
                return;
            }

            const severityValue = Number(post.severity ?? 3);
            const markerColor = getSeverityColor(severityValue);
            const title = escapeHtml(post.name || 'Untitled post');
            const severityLabel = escapeHtml(post.severity ? `Level ${post.severity}` : 'Unknown');
            const description = escapeHtml(post.description || 'No description provided.');
            const photoMarkup = post.imageID
                ? `<img src="https://drive.google.com/thumbnail?id=${encodeURIComponent(post.imageID)}" alt="${title}" />`
                : '<p class="post-map-popup-empty">Photo preview unavailable.</p>';
            const popupHtml = `
                <div class="post-map-popup">
                    <strong>${title}</strong>
                    <p><strong>Severity:</strong> ${severityLabel}</p>
                    <p>${description}</p>
                    ${photoMarkup}
                </div>
            `;

            L.circleMarker([lat, lon], {
                radius: 8,
                color: markerColor,
                fillColor: markerColor,
                fillOpacity: 0.85,
                weight: 1.5
            }).bindPopup(popupHtml).addTo(postMarkersLayer);
        });

        setMapStatus('idle', '');
    }

    function loadPostsToMap() {
        setMapStatus('loading', 'Loading posts…');

        fetch('/api/posts/', { credentials: 'same-origin' })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Request failed with status ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                const posts = Array.isArray(data.posts) ? data.posts : [];
                renderPostsToMap(posts);
            })
            .catch(error => {
                console.error('Error loading posts:', error);
                setMapStatus('error', 'Unable to load posts right now. Please try again later.');
            });
    }

    function set_post() {
        loadPostsToMap();
    }

    set_post();

    document.querySelector('.profile-btn').addEventListener('click', () => {
        document.querySelector('.profile-modal').classList.add('active');
    });
    
    // Profile modal close functionality
    const profileModal = document.querySelector('.profile-modal');
    const profileCloseModal = profileModal ? profileModal.querySelector('.close-modal') : null;
    
    if (profileCloseModal && profileModal) {
        profileCloseModal.addEventListener('click', function() {
            profileModal.classList.remove('active');
        });
        
        // Close modal when clicking outside the modal content
        profileModal.addEventListener('click', function(e) {
            if (e.target === profileModal) {
                profileModal.classList.remove('active');
            }
        });
    }
    
    // Tab switching
    const authTabs = document.querySelectorAll('.auth-tab');
    authTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            authTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            // Toggle form fields and button text based on active tab
        });
    });

    // Sign up and sign in functionality
    const signUpForm = document.getElementById('signUpForm');
    const signInForm = document.getElementById('signInForm');
    // Report button functionality
    const reportBtn = document.getElementById('reportBtn');
    const reportModal = document.getElementById('reportModal');
    const reportCloseModal = reportModal ? reportModal.querySelector('.close-modal') : null;
    const photoInput = document.getElementById('photo');
    const photoPreview = document.getElementById('photoPreview');
    const reportForm = document.getElementById('reportForm');
    const openphotoBtn = document.getElementById('openphotoBtn');
    const photoModal = document.getElementById('photoModal');
    const photoCloseModal = photoModal ? photoModal.querySelector('.close-modal') : null;
    // var image_flag = false ;
    
    if (reportBtn && reportModal) {
        reportBtn.addEventListener('click', function() {
            reportModal.classList.add('active');            
        });
    }
    
    if (reportCloseModal && reportModal) {
        reportCloseModal.addEventListener('click', function() {
            reportModal.classList.remove('active');
        });
        
        // Close modal when clicking outside the modal content
        reportModal.addEventListener('click', function(e) {
            if (e.target === reportModal) {
                reportModal.classList.remove('active');
            }
        });
    }
    
    // Photo preview functionality
    if (photoInput && photoPreview) {
        photoInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    photoPreview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
                }
                
                reader.readAsDataURL(this.files[0]);
            } else {
                photoPreview.innerHTML = '';
            }
        });
    }
    
    // Form submission
    // if (reportForm) {
    //     reportForm.addEventListener('submit', function(e) {
    //         e.preventDefault();
            
    //         // Get form data
    //         const formData = new FormData(this);
    //         const reportData = {
    //             name: formData.get('name'),
    //             severity: formData.get('severity'),
    //             phone: formData.get('phone'),
    //             email: formData.get('email'),
    //             photo: photoInput.files[0] ? photoInput.files[0].name : null
    //         };
            
    //         // For now, just log the data and show success message
    //         console.log('Report submitted:', reportData);
    //         alert('Thank you for your report! We will review it shortly.');
            
    //         // Reset form and close modal
    //         this.reset();
    //         photoPreview.innerHTML = '';
    //         reportModal.classList.remove('active');
            
    //         // In a real application, you would send this data to a server
    //         // using fetch or XMLHttpRequest
    //     });
    // }

    // photo modal control
    if (openphotoBtn && photoModal) {
        openphotoBtn.addEventListener('click', function() {
            photoModal.classList.add('active');
            photocontrol() ;
        });
    }

    if (photoCloseModal && photoModal) {
        photoCloseModal.addEventListener('click', function() {
            photoModal.classList.remove('active');
            stopCameraStream();
        });
        
        // Close modal when clicking outside the modal content
        // photoModal.addEventListener('click', function(e) {
        //     if (e.target === reportModal) {
        //         photoModal.classList.remove('active');
                
        //     }
        // });
    }    

    // let currentFacingMode = "environment";

    // function photocontrol() {
    //     const video = document.getElementById('video');
    //     const canvas = document.getElementById('canvas');
    //     const capture = document.getElementById('capture');
    //     const retake = document.getElementById('retake');
    //     const done = document.getElementById('done');
    //     const switchBtn = document.getElementById('switchCamera');
    //     const preview = document.getElementById('photoPreview');

    //     if (!window.photoStream) {
    //         navigator.mediaDevices.getUserMedia({ video: true })
    //             .then((stream) => {
    //                 window.photoStream = stream;
    //                 video.srcObject = stream;
    
    //                 video.addEventListener('loadedmetadata', () => {
    //                     video.play();
    //                     canvas.width = video.videoWidth;
    //                     canvas.height = video.videoHeight;
    //                     showVideo();
    //                 });
    //             })
    //             .catch((err) => {
    //                 console.error("Camera error:", err);
    //                 alert("Camera access denied or not available.");
    //             });
    //     } else {
    //         video.srcObject = window.photoStream;
    //         video.play();
    //         canvas.width = video.videoWidth;
    //         canvas.height = video.videoHeight;
    //         showVideo();
    //     }
    
    //     function showVideo() {
    //         image_flag = false ;
    //         video.style.display = 'block';
    //         canvas.style.display = 'none';
    //         capture.style.display = 'inline-block';
    //         retake.style.display = 'none';
    //         done.style.display = 'none';
    //         switchBtn.style.display = 'inline-block';
    //     }
    
    //     function showPhoto(dataURL) {
    //         // photo.src = dataURL;
    //         canvas.style.display = 'block';
    //         video.style.display = 'none';
    //         capture.style.display = 'none';
    //         retake.style.display = 'inline-block';
    //         done.style.display = 'inline-block';
    //         switchBtn.style.display = 'none';
    //     }

    //     switchBtn.onclick = () => {            
    //         currentFacingMode = currentFacingMode === "user" ? "environment" : "user";
    //         stopCameraStream();
    //         startCamera();
    //     };
    
    //     capture.onclick = () => {
    //         setTimeout(() => {                
    //             const context = canvas.getContext('2d');                
    //             context.drawImage(video, 0, 0, canvas.width, canvas.height);
    //             const ctx2 = preview.getContext('2d');
    //             preview.width = canvas.width;
    //             preview.height = canvas.height;
    //             ctx2.drawImage(canvas, 0, 0);
    //             const dataURL = canvas.toDataURL('image/png');
    //             showPhoto(dataURL);
    //         }, 100);
    //     };
    
    //     retake.onclick = showVideo;

    //     done.onclick = () => {
    //         document.getElementById('photoModal').classList.remove('active');
    //         image_flag = true ;
    //         stopCameraStream() ;
    //     }
    // }
    
    // function stopCameraStream() {
    //     const video = document.getElementById('video');
    //     const stream = video.srcObject;
    
    //     if (stream) {
    //         // Stop each media track
    //         stream.getTracks().forEach(track => {
    //             track.stop();
    //         });
    
    //         // Forcefully clear any references
    //         video.srcObject = null;
    //         video.removeAttribute('srcObject');
    //         video.removeAttribute('src');
    //         video.load();  // Force reload and detach
    //     }
    
    //     video.pause();
    //     window.photoStream = null;
    // }

    let currentFacingMode = "environment"; // try back camera first
    let image_flag = false;

    function startCamera() {
        const constraints = {
            video: {
                facingMode: { ideal: currentFacingMode }
            },
            audio: false
        };

        navigator.mediaDevices.getUserMedia(constraints)
            .then((stream) => {
                window.photoStream = stream;
                const video = document.getElementById('video');
                video.srcObject = stream;

                video.onloadedmetadata = () => {
                    video.play();
                    const canvas = document.getElementById('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                };
            })
            .catch((err) => {
                console.warn("Failed with mode:", currentFacingMode, err);
                // Fallback logic
                if (currentFacingMode === "environment") {
                    currentFacingMode = "user";
                    startCamera(); // try front camera
                } else {
                    alert("No camera available or permission denied.");
                }
            });
    }

    function stopCameraStream() {
        if (window.photoStream) {
            window.photoStream.getTracks().forEach(track => track.stop());
            window.photoStream = null;
        }
    }

    function photocontrol() {
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const capture = document.getElementById('capture');
        const retake = document.getElementById('retake');
        const done = document.getElementById('done');
        const switchBtn = document.getElementById('switchCamera');
        const preview = document.getElementById('photoPreview');

        startCamera(); // start initial camera
        showVideo();

        function showVideo() {
            image_flag = false;
            video.style.display = 'block';
            canvas.style.display = 'none';
            capture.style.display = 'inline-block';
            retake.style.display = 'none';
            done.style.display = 'none';
            switchBtn.style.display = 'none';
        }

        function showPhoto(dataURL) {
            canvas.style.display = 'block';
            video.style.display = 'none';
            capture.style.display = 'none';
            retake.style.display = 'inline-block';
            done.style.display = 'inline-block';
            switchBtn.style.display = 'none';
        }

        switchBtn.onclick = () => {
            currentFacingMode = currentFacingMode === "user" ? "environment" : "user";
            stopCameraStream();
            startCamera();
        };

        capture.onclick = () => {
            setTimeout(() => {
                const context = canvas.getContext('2d');
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                const ctx2 = preview.getContext('2d');
                preview.width = canvas.width;
                preview.height = canvas.height;
                ctx2.drawImage(canvas, 0, 0);
                const dataURL = canvas.toDataURL('image/png');
                showPhoto(dataURL);
            }, 100);
        };

        retake.onclick = showVideo;

        done.onclick = () => {
            document.getElementById('photoModal').classList.remove('active');
            image_flag = true;
            stopCameraStream();
        };
    }

    // Initialize on page load
    // window.onload = photocontrol;

    const clearBtn = document.getElementById('clearBtn') ;
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            const preview = document.getElementById('photoPreview');
            const ctx2 = preview.getContext('2d');
            ctx2.clearRect(0, 0, preview.width, preview.height);
            image_flag = false ;
        });
    }

    document.getElementById('reportForm').addEventListener('submit', function(e) {
        e.preventDefault(); // Stop form from submitting immediately
    
        if (image_flag == false) {
            alert("Image is not captured.");            
            return ;
        }

        const canvas = document.getElementById('photoPreview');
        const photoData = canvas.toDataURL('image/png');
        document.getElementById('photoData').value = photoData;
    
        navigator.geolocation.getCurrentPosition(function(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;    
            document.getElementById('latData').value = lat;
            document.getElementById('lonData').value = lng;
    
            // ✅ Now submit the form manually after lat/lng are set
            document.getElementById('reportForm').submit();
        }, function(error) {
            alert("Error getting location: " + error.message);
        });
    });
    // individual post map
});