// Theme switcher with system preference detection and cookie persistence
(function() {
    const THEME_COOKIE = 'theme_preference';
    const THEME_DARK = 'dark';
    const THEME_LIGHT = 'light';
    
    // Get cookie value
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    // Set cookie value (expires in 1 year)
    function setCookie(name, value) {
        const date = new Date();
        date.setTime(date.getTime() + (365 * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value}; expires=${date.toUTCString()}; path=/; SameSite=Lax`;
    }
    
    // Get initial theme
    function getInitialTheme() {
        // Check cookie first
        const savedTheme = getCookie(THEME_COOKIE);
        if (savedTheme === THEME_DARK || savedTheme === THEME_LIGHT) {
            return savedTheme;
        }
        
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return THEME_DARK;
        }
        
        return THEME_LIGHT;
    }
    
    // Apply theme to document
    function applyTheme(theme) {
        if (theme === THEME_DARK) {
            document.documentElement.classList.add('dark-mode');
        } else {
            document.documentElement.classList.remove('dark-mode');
        }
    }
    
    // Toggle theme
    function toggleTheme() {
        const currentTheme = document.documentElement.classList.contains('dark-mode') ? THEME_DARK : THEME_LIGHT;
        const newTheme = currentTheme === THEME_DARK ? THEME_LIGHT : THEME_DARK;
        
        applyTheme(newTheme);
        setCookie(THEME_COOKIE, newTheme);
        updateCheckbox(newTheme);
    }
    
    // Update checkbox state
    function updateCheckbox(theme) {
        const checkbox = document.getElementById('theme-toggle-checkbox');
        if (!checkbox) return;
        
        // Checked = light mode (sun), unchecked = dark mode (moon)
        checkbox.checked = (theme === THEME_LIGHT);
    }
    
    // Initialize theme on page load
    function initTheme() {
        const theme = getInitialTheme();
        applyTheme(theme);
        
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                updateCheckbox(theme);
                setupCheckboxListener();
            });
        } else {
            updateCheckbox(theme);
            setupCheckboxListener();
        }
    }
    
    // Setup checkbox change listener
    function setupCheckboxListener() {
        const checkbox = document.getElementById('theme-toggle-checkbox');
        if (!checkbox) return;
        
        checkbox.addEventListener('change', function() {
            toggleTheme();
        });
    }
    
    // Listen for system theme changes
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            // Only apply if user hasn't manually set a preference
            if (!getCookie(THEME_COOKIE)) {
                const theme = e.matches ? THEME_DARK : THEME_LIGHT;
                applyTheme(theme);
                updateCheckbox(theme);
            }
        });
    }
    
    // Make toggle function globally available
    window.toggleTheme = toggleTheme;
    
    // Initialize immediately
    initTheme();
})();
