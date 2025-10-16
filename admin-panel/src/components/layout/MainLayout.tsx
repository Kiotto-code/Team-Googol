import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/auth';
import { useUIStore } from '@/store/ui';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { useTranslation } from 'react-i18next';
import { useEffect } from 'react';
import { dayjs } from '@/lib/dayjs';

const navItems = [
  { to: '/', label: 'nav.dashboard' },
  { to: '/boxes', label: 'nav.boxes' },
  { to: '/cases', label: 'nav.cases' },
  { to: '/items', label: 'nav.items' },
  { to: '/users', label: 'nav.users' },
  { to: '/audit', label: 'nav.audit' },
  { to: '/reports', label: 'nav.reports' },
  { to: '/metrics', label: 'nav.metrics' },
  { to: '/health', label: 'nav.health' }
];

export function MainLayout() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuthStore((state) => ({
    user: state.user,
    logout: state.logout
  }));
  const { theme, setTheme, timezone, setTimezone, language, setLanguage } = useUIStore();

  useEffect(() => {
    const root = document.documentElement;
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const resolved = theme === 'system' ? (systemPrefersDark ? 'dark' : 'light') : theme;
    root.classList.remove('light', 'dark');
    root.classList.add(resolved);
  }, [theme]);

  useEffect(() => {
    dayjs.tz.setDefault(timezone);
  }, [timezone]);

  useEffect(() => {
    if (i18n.language !== language) {
      i18n.changeLanguage(language);
    }
  }, [i18n, language]);

  const onLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-6">
            <span className="text-lg font-semibold">{t('app.title')}</span>
            <nav className="flex items-center gap-4 text-sm">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `transition-colors hover:text-primary ${isActive ? 'text-primary font-medium' : 'text-muted-foreground'}`
                  }
                >
                  {t(item.label)}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  {t('timezone.label')}: {timezone === 'Asia/Kuala_Lumpur' ? t('timezone.kl') : t('timezone.utc')}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setTimezone('Asia/Kuala_Lumpur')}>{t('timezone.kl')}</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTimezone('UTC')}>{t('timezone.utc')}</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  {t('language.label')}: {language.toUpperCase()}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setLanguage('en')}>{t('language.en')}</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setLanguage('zh')}>{t('language.zh')}</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  {t('theme.label')}: {t(`theme.${theme}`)}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setTheme('light')}>{t('theme.light')}</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme('dark')}>{t('theme.dark')}</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme('system')}>{t('theme.system')}</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  {user?.name ?? 'Admin'}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>{user?.email}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onLogout}>{t('nav.logout')}</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl p-6">
        <Outlet />
      </main>
    </div>
  );
}
