import { useEffect, useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { api } from '@/api/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, AlertCircle, ArrowLeft } from 'lucide-react';
import { Logo } from '@/components/shared/Logo';

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true">
      <path fill="#EA4335" d="M12 10.2v3.9h5.5c-.2 1.3-1.5 3.9-5.5 3.9-3.3 0-6-2.7-6-6s2.7-6 6-6c1.9 0 3.1.8 3.8 1.5l2.6-2.5C16.7 3.5 14.6 2.5 12 2.5 6.8 2.5 2.5 6.8 2.5 12s4.3 9.5 9.5 9.5c5.5 0 9.1-3.8 9.1-9.2 0-.6-.1-1.1-.2-1.6H12z" />
    </svg>
  );
}

export function LoginForm() {
  const { setAuth } = useAuthStore();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(
    searchParams.get('tab') === 'register' ? 'register' : 'login'
  );

  // Login form state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Register form state
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerUsername, setRegisterUsername] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [registerConfirmPassword, setRegisterConfirmPassword] = useState('');
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001';

  const clearError = () => setError(null);

  useEffect(() => {
    const hash = window.location.hash.replace(/^#/, '');
    if (!hash) return;

    const params = new URLSearchParams(hash);
    const oauthStatus = params.get('oauth');
    if (!oauthStatus) return;

    if (oauthStatus === 'error') {
      setError((params.get('message') || 'OAuth login failed').replaceAll('_', ' '));
      window.history.replaceState(null, '', '/login');
      return;
    }

    const token = params.get('token');
    const encodedUser = params.get('user');
    const nextPath = params.get('next') || '/app';

    if (!token || !encodedUser) {
      setError('OAuth login failed: missing token or user data');
      window.history.replaceState(null, '', '/login');
      return;
    }

    try {
      const normalized = encodedUser.replace(/-/g, '+').replace(/_/g, '/');
      const padded = normalized + '='.repeat((4 - normalized.length % 4) % 4);
      const decoded = atob(padded);
      const user = JSON.parse(decoded);
      setAuth(token, user);
      window.history.replaceState(null, '', '/login');
      navigate(nextPath);
    } catch {
      setError('OAuth login failed: invalid user payload');
      window.history.replaceState(null, '', '/login');
    }
  }, [navigate, setAuth]);

  const startOAuth = (provider: 'google') => {
    clearError();
    window.location.href = `${apiUrl}/api/v1/auth/oauth/${provider}/start?next_path=${encodeURIComponent('/app')}`;
  };

  const SocialButtons = () => (
    <div className="space-y-2 mb-4">
      <Button type="button" variant="outline" className="w-full" onClick={() => startOAuth('google')} disabled={isLoading}>
        <GoogleIcon />
        <span className="ml-2">Continue with Google</span>
      </Button>
    </div>
  );

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setIsLoading(true);

    try {
      const response = await api.login({ email: loginEmail, password: loginPassword });
      setAuth(response.access_token, response.user);
      navigate('/app');
    } catch (err: any) {
      setError(err.detail || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (registerPassword !== registerConfirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (registerPassword.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.register({
        email: registerEmail,
        username: registerUsername,
        password: registerPassword,
      });
      setAuth(response.access_token, response.user);
      navigate('/app');
    } catch (err: any) {
      setError(err.detail || 'Registration failed. Email or username may already exist.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-[400px] shadow-lg">
        <CardHeader className="text-center pb-2">
          <div className="flex justify-start mb-2">
            <Link
              to="/"
              className="flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to home
            </Link>
          </div>
          <div className="flex justify-center mb-4">
            <Logo size="lg" showText={false} />
          </div>
          <CardTitle className="text-2xl font-semibold">Welcome to DocChat</CardTitle>
          <CardDescription className="text-muted-foreground">
            Sign in to start chatting with your documents
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          <Tabs
            value={activeTab}
            onValueChange={(v) => {
              setActiveTab(v);
              clearError();
            }}
            className="w-full"
          >
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="login">Sign In</TabsTrigger>
              <TabsTrigger value="register">Create Account</TabsTrigger>
            </TabsList>

            {error && (
              <div className="flex items-start gap-2 p-3 mb-4 rounded-lg bg-destructive/10 text-destructive text-sm">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <TabsContent value="login" className="mt-0">
              <SocialButtons />
              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">Or continue with email</span>
                </div>
              </div>
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="login-email">Email</Label>
                  <Input
                    id="login-email"
                    type="email"
                    placeholder="you@example.com"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    required
                    disabled={isLoading}
                    autoComplete="email"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="login-password">Password</Label>
                  <Input
                    id="login-password"
                    type="password"
                    placeholder="Enter your password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    required
                    disabled={isLoading}
                    autoComplete="current-password"
                  />
                </div>
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Signing in...
                    </>
                  ) : (
                    'Sign In'
                  )}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="register" className="mt-0">
              <SocialButtons />
              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">Or create with email</span>
                </div>
              </div>
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="register-email">Email</Label>
                  <Input
                    id="register-email"
                    type="email"
                    placeholder="you@example.com"
                    value={registerEmail}
                    onChange={(e) => setRegisterEmail(e.target.value)}
                    required
                    disabled={isLoading}
                    autoComplete="email"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-username">Username</Label>
                  <Input
                    id="register-username"
                    type="text"
                    placeholder="Choose a username"
                    value={registerUsername}
                    onChange={(e) => setRegisterUsername(e.target.value)}
                    required
                    disabled={isLoading}
                    minLength={3}
                    autoComplete="username"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-password">Password</Label>
                  <Input
                    id="register-password"
                    type="password"
                    placeholder="Min 6 characters"
                    value={registerPassword}
                    onChange={(e) => setRegisterPassword(e.target.value)}
                    required
                    disabled={isLoading}
                    minLength={6}
                    autoComplete="new-password"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-confirm-password">Confirm Password</Label>
                  <Input
                    id="register-confirm-password"
                    type="password"
                    placeholder="Confirm your password"
                    value={registerConfirmPassword}
                    onChange={(e) => setRegisterConfirmPassword(e.target.value)}
                    required
                    disabled={isLoading}
                    autoComplete="new-password"
                  />
                </div>
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating account...
                    </>
                  ) : (
                    'Create Account'
                  )}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
