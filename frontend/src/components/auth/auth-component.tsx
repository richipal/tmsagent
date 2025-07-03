import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { ApiService } from '../../services/api';

interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
}

interface AuthComponentProps {
  onAuthChange: (authenticated: boolean, user?: User) => void;
}

export const AuthComponent: React.FC<AuthComponentProps> = ({ onAuthChange }) => {
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const apiService = ApiService.getInstance();

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      // Check if we have a token in localStorage first
      const token = localStorage.getItem('access_token');
      if (token) {
        apiService.setAuthToken(token);
      }
      
      const status = await apiService.getAuthStatus();
      setAuthenticated(status.authenticated);
      setUser(status.user);
      onAuthChange(status.authenticated, status.user);
    } catch (error) {
      console.log('Not authenticated:', error);
      setAuthenticated(false);
      setUser(null);
      onAuthChange(false);
    } finally {
      setLoading(false);
    }
  };

  const handleDevLogin = async () => {
    try {
      setLoading(true);
      const result = await apiService.devLogin();
      setAuthenticated(true);
      setUser(result.user);
      onAuthChange(true, result.user);
    } catch (error) {
      console.error('Login failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      setLoading(true);
      // Redirect to Google OAuth
      window.location.href = 'http://localhost:8000/auth/google/login';
    } catch (error) {
      console.error('Google login failed:', error);
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      setLoading(true);
      await apiService.logout();
      setAuthenticated(false);
      setUser(null);
      onAuthChange(false);
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center space-x-2 text-sm text-gray-600">
        <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
        <span>Checking authentication...</span>
      </div>
    );
  }

  if (authenticated && user) {
    return (
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          {user.picture && (
            <img 
              src={user.picture} 
              alt={user.name}
              className="w-8 h-8 rounded-full"
            />
          )}
          <div className="flex flex-col">
            <span className="text-sm font-medium text-gray-900">{user.name}</span>
            <span className="text-xs text-gray-500">{user.email}</span>
          </div>
        </div>
        <Button 
          onClick={handleLogout} 
          variant="outline" 
          size="sm"
          disabled={loading}
        >
          Logout
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2">
      <Button 
        onClick={handleGoogleLogin} 
        variant="default" 
        size="sm"
        disabled={loading}
      >
        {loading ? 'Logging in...' : 'Sign in with Google'}
      </Button>
    </div>
  );
};