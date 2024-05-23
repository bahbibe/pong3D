
const app = document.getElementById('app');
const routes = {
    '/': () => '<h1 class="fw-bold text-primary">Home Page</h1><p>Welcome to the Home page!</p>',
    '/about': () => '<h1 class="text-primary fw-bold">About Page</h1><p>Learn more about us on this page.</p>',
    '/contact': () => '<h1 class="text-primary fw-bold">Contact Page</h1><p>Contact us through this page.</p>',
};

 // Render the content for the given path
 const render = (path) => {
    const content = routes[path] || (() => '<h1>404 - Page Not Found</h1><p>Sorry, this page does not exist.</p>');
    console.log(content);
    app.innerHTML = content();
};

document.body.addEventListener('click', (e) => {
    if (e.target.matches('a')) {
        e.preventDefault();
        const path = e.target.getAttribute('href');
        history.pushState(null, null, path);
        render(path);
    }
});


// Handle browser navigation (back/forward buttons)
window.addEventListener('popstate', () => {
    render(window.location.pathname);
});

render(window.location.pathname);