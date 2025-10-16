export class Router {
  constructor({ routes, onRouteChange, fallback }) {
    this.routes = routes;
    this.onRouteChange = onRouteChange;
    this.fallback = fallback;
    window.addEventListener('hashchange', () => this.handleRouteChange());
  }

  start() {
    if (!window.location.hash) {
      window.location.hash = '#/dashboard';
    } else {
      this.handleRouteChange();
    }
  }

  resolveRoute(hash) {
    const cleanHash = hash.replace(/^#/, '');
    const [path, search] = cleanHash.split('?');
    const route = this.routes[path] || this.routes['*'];
    const params = new URLSearchParams(search || '');
    return { route, params };
  }

  async handleRouteChange() {
    const { route, params } = this.resolveRoute(window.location.hash || '#/dashboard');
    if (!route) {
      if (this.fallback) {
        this.fallback({ path: window.location.hash });
      }
      return;
    }
    try {
      await this.onRouteChange(route, params);
    } catch (error) {
      console.error('Route render failed', error);
      if (this.fallback) {
        this.fallback({ path: window.location.hash, error });
      }
    }
  }
}
